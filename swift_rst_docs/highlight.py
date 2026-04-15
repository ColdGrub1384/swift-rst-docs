from .types import Symbol, AnnotatedDeclaration, GenerationContext
from pygments.formatters import HtmlFormatter
from pygments.lexers import SwiftLexer
from bs4 import BeautifulSoup
from pygments import highlight
import re


def prettify_swift_declaration(decl: str, indent: str = "    ") -> str:
    """
    Splits and returns a Swift declaration into multiple lines.

    :decl: A Swift declaration.
    :indent: Indentation to use.
    :rtype: str
    """

    tokens = re.findall(r'@[a-zA-Z_]\w*|\w+|[^\w\s]', decl)
    
    result = []
    level = 0
    i = 0
    
    def newline():
        result.append("\n" + indent * level)
    
    while i < len(tokens):
        tok = tokens[i]

        if tok in ("(", "["):
            closing = ")" if tok == "(" else "]"

            if tok == "[":
                j = i + 1
                simple = True
                depth = 1
                while j < len(tokens) and depth > 0:
                    if tokens[j] == "[":
                        depth += 1
                    elif tokens[j] == "]":
                        depth -= 1
                    elif tokens[j] == ",":
                        simple = False
                    j += 1

                if simple:
                    result.append(tok)
                    i += 1
                    continue

            if i + 1 < len(tokens) and tokens[i + 1] == closing:
                result.append(tok)
                result.append(closing)
                i += 2
                continue
            else:
                result.append(tok)
                level += 1
                newline()

        elif tok in (")", "]"):
            if tok == "]" and result and not result[-1].endswith("\n"):
                result.append(tok)  # inline case like [String]
            else:
                level -= 1
                newline()
                result.append(tok)


        elif tok == ",":
            result.append(tok)
            newline()

        elif tok == "-" and i + 1 < len(tokens) and tokens[i + 1] == ">":
            if result and not result[-1].endswith((" ", "\n")):
                result.append(" ")
            result.append("->")
            result.append(" ")
            i += 2
            continue

        elif tok == ":":
            result.append(tok)
            result.append(" ")

        elif tok == "=":
            if result and not result[-1].endswith((" ", "\n")):
                result.append(" ")
            result.append(tok)
            result.append(" ")

        elif tok == ".":
            result.append(tok)

        else:
            if result and not result[-1].endswith(("\n", "(", "[", " ", ".", "@")) and tok not in ("]", ")", ":", "?", "!"):
                result.append(" ")
            result.append(tok)
            if tok.startswith("@"):
                newline()

        i += 1

    return "".join(result)


def highlight_statement(statement: AnnotatedDeclaration, prettify: bool, remove_type: bool, context: GenerationContext) -> str:
    """
    Highlights a statement's declaration with pygments and returns it as a `raw:: html` block.
    Also replaces any USR in the statement's declaration with links to the corresponding documentation pages if symbols are already fetched into the generation context.

    :param statement: The statement to highlight.
    :param prettify: Whether to prettify the code.
    :param remove_type: Whether to remove the type.
    :param context: The generation context.
    :rtype: str
    """

    links = {}
    code = ""
    i = 0
    for chunk in statement.chunks:
        if chunk.usr:
            links[chunk.chunk] = chunk.usr.replace(":", "_")
        if i == 0:
            text = chunk.chunk.replace("public ", "").replace("final ", "")
        else:
            text = chunk.chunk
        if (chunk.chunk.endswith(" : ") or chunk.chunk.endswith(": ")) and remove_type:
            code += text.replace(" : ", "").replace(": ", "")
            break
        else:
            code += text
        i += 1
    if prettify:
        code = prettify_swift_declaration(code)

    highlighted = ""
    i = 0
    for line in highlight(code, SwiftLexer(), HtmlFormatter(style="friendly", cssclass="highlight")).split("\n"):
        if i > 0:
            highlighted += "\n"
        highlighted += "   " + line
        i += 1

    soup = BeautifulSoup(highlighted, features="html.parser")
    previous_is_arobase = False
    for child in soup.find_all("span"):
        try:
            if child.string and child.string.startswith("@"):
                previous_is_arobase = True
                child["class"] = "kd"
            else:
                if previous_is_arobase:
                    child["class"] = "kd"
                previous_is_arobase = False

            if child.string in links:
                name = child.string
                link = links[child.string]
                child["class"] = "nb"
                if links[child.string] in map(lambda s: s.replace(":", "_"), list(context.fullnames.values())):
                    new_link = soup.new_tag("a")
                    new_link["href"] = link+".html"
                    new_link.string = child.string
                    child.string = ""
                    new_link["class"] = child["class"]
                    new_link["style"] = "text-decoration: underline"
                    child.append(new_link)
        except KeyError:
            continue

    return f"""
.. raw:: html

    {str(soup)}
"""

__all__ = [
    "prettify_swift_declaration",
    "highlight_statement"
]
