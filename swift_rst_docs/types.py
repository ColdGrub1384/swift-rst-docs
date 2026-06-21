import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum
import sys


class DeclarationKind(Enum):
    """
    A kind of declaration.
    """

    CLASS = "source.lang.swift.decl.class"
    """
    A class.
    """

    PROTOCOL = "source.lang.swift.decl.protocol"
    """
    A protocol.
    """

    STRUCT = "source.lang.swift.decl.struct"
    """
    A structure.
    """

    ENUM = "source.lang.swift.decl.enum"
    """
    An enumeration.
    """

    FUNCTION = "source.lang.swift.decl.function.free"
    """
    A global function.
    """

    INSTANCE_VARIABLE = "source.lang.swift.decl.var.instance"
    """
    An instance variable.
    """

    INSTANCE_METHOD = "source.lang.swift.decl.function.method.instance"
    """
    An instance method.
    """

    STATIC_VARIABLE = "source.lang.swift.decl.var.static"
    """
    A static variable.
    """

    STATIC_METHOD = "source.lang.swift.decl.function.method.static"
    """
    A static method.
    """

    CLASS_VARIABLE = "source.lang.swift.decl.var.class"
    """
    A class variable.
    """

    CLASS_METHOD = "source.lang.swift.decl.function.method.class"
    """
    A class method.
    """

    ENUM_ELEMENT = "source.lang.swift.decl.enumelement"
    """
    An enumeration case.
    """

    EXTENSION = "source.lang.swift.decl.extension"
    """
    An extension.
    """

    LOCAL_VARIABLE = "source.lang.swift.decl.var.local"
    """
    A local variable.
    """

    UNKNOWN = "unknown"
    """
    An unknown declaration.
    """

    @classmethod
    def _missing_(cls, value):
        return cls.UNKNOWN


class Accessibility(Enum):
    """
    A symbol's accessibility attribute.
    """

    OPEN = "source.lang.swift.accessibility.open"
    """
    Open for inheritance.
    """

    PUBLIC = "source.lang.swift.accessibility.public"
    """
    Accessible from another module.
    """

    INTERNAL = "source.lang.swift.accessibility.internal"
    """
    Restricted to the module.
    """

    FILEPRIVATE = "source.lang.swift.accessibility.fileprivate"
    """
    Restricted to the source file.
    """

    PRIVATE = "source.lang.swift.accessibility.private"
    """
    Restricted to the containing declaration.
    """

    UNKNOWN = "unknown"
    """
    Unknown accessibility.
    """

    @property
    def order(self) -> int:
        """
        Order of accessibility.
        Higher value means more accessible.

        :rtype: int
        """

        match self:
            case Accessibility.OPEN:
                return 4
            case Accessibility.PUBLIC:
                return 3
            case Accessibility.INTERNAL:
                return 2
            case Accessibility.FILEPRIVATE:
                return 1
            case Accessibility.PRIVATE:
                return 0
            case Accessibility.UNKNOWN:
                return -1

    @classmethod
    def _missing_(cls, value):
        return cls.UNKNOWN


class GenerationContext:
    """
    A generation context contains metadata and options for the generation of the documentation, as well as the symbols information fetched by :py:func:`swift_rst_docs.fetch_documents`.
    """

    index_title: str
    """
    The title of the main page.
    """

    overview: str
    """
    A text written into the main page.
    """

    documented_objects: Optional[List[str]]
    """
    An optional list of documented files (with .swift extension).
    If `None`, all files in the module will be documented.
    :py:func:`swift_rst_docs.fetch_documents` checks if the fetched file paths end with any of the values of this list, so you can write just the file names, or the paths relative to any directory in the source code to disambiguate between modules.
    """

    documented_symbols: Optional[List[str]]
    """
    An optional list of top level documented symbol names.
    If `None`, all symbols will be documented.
    """

    min_accessibility: Accessibility
    """
    Minimum accessibility for symbols to be documented. 
    """

    fullnames: Dict[str, str]
    """
    A dictionary mapping full symbols names to their documentation's USR.
    A USR is an unique identifier of a symbol in the documentation, which corresponds to the file name (without the extension) in the documentation's root directory by replacing `":"` with `"_"`.

    This value is written by :py:func:`swift_rst_docs.fetch_fullnames`.
    """

    body: List[Symbol]
    """
    Top level symbols fetched by :py:func:`swift_rst_docs.fetch_documents`.
    """

    sphinx: bool
    """
    Whether the documentation is being built witht the Sphinx extension.

    If ``True``, symbol references will use the ``:swift:symbol:`` role instead of ``:ref:`` to make the name monospaced.
    """

    def __init__(
        self,
        index_title: str,
        overview: Optional[str] = None,
        min_accessibility: Accessibility = Accessibility.PUBLIC,
        documented_objects: Optional[List[str]] = None,
        documented_symbols: Optional[List[str]] = None
    ):
        self.index_title = index_title
        self.overview = overview or ""
        self.min_accessibility = min_accessibility
        self.documented_objects = documented_objects
        self.documented_symbols = documented_symbols
        self.fullnames = {}
        self.body = []

    def find(self, symbol_name: str, module_name: Optional[str]) -> Optional[str]:
        """
        Finds a symbol name in :py:attr:`swift_rst_docs.GenerationContext.fullnames` and returns its USR value if found.

        :param symbol_name: The symbol name to find.
        :param module_name: An optional module name to use as context. If not `None`, `symbol_name` can omit the module name.
        :rtype: Optional[str]
        """

        usr = None
        if module_name:
            usr = self.fullnames.get(f"{module_name}.{symbol_name}")
        if not usr:
            usr = self.fullnames.get(symbol_name)
        return usr


@dataclass
class Annotation:
    """
    An annotated part of a declaration.
    """

    chunk: str
    """
    The chunk of code in the declaration.
    """

    usr: Optional[str]
    """
    An optional type USR value the chunk corresponds to.
    """


@dataclass
class AnnotatedDeclaration:
    """
    A type annotated declaration, initialized from an XML string.
    """

    parsed: str
    """
    The full parsed declaration as plain text.
    """

    chunks: List[Annotation]
    """
    The typed chunks of the declaration.
    """

    def __init__(self, declaration: str):
        root = ET.fromstring(declaration)

        chunks = []
        parsed = ""

        if root.text:
            chunks.append(Annotation(root.text, None))
            parsed += root.text

        for item in root:
            if not item.text:
                continue
            if item.tag == "Type":
                chunks.append(Annotation(item.text, item.attrib.get("usr")))
            else:
                chunks.append(Annotation(item.text, None))
            parsed += item.text

            if item.tail:
                chunks.append(Annotation(item.tail, None))
                parsed += item.tail

        self.parsed = parsed
        self.chunks = chunks


@dataclass
class Documentation:
    """
    The documentation of a symbol, initialized from an XML string.
    """

    usr: str
    """
    The unique identifier of the symbol.
    Corresponds to its page file name (without the extension) by replacing `":"` with `":"`.
    """

    name: str
    """
    The relative name of the symbol.
    """

    comment: str
    """
    The first line of the comment string.
    """

    discussion: Optional[str]
    """
    The rest of the comment string.
    """

    parameters: List[Dict[str, str]]
    """
    A list of parameters witht their documentation.
    Each value has `name` and a `description` key.
    """

    result: Optional[str]
    """
    The description of the return value.
    """

    throws: Optional[str]
    """
    The description of the errors that can be thrown.
    """

    def __init__(self, body: str, context: GenerationContext):
        root = ET.fromstring(body)
        
        name_elem = root.find("Name")
        self.name = name_elem.text if (name_elem is not None and name_elem.text is not None) else ""
        
        usr_elem = root.find("USR")
        self.usr = usr_elem.text if (usr_elem is not None and usr_elem.text is not None) else ""
        
        comment_parts = root.find("CommentParts")
        
        abstract_elem = comment_parts.find("Abstract") if comment_parts is not None else None
        self.comment = self._extract_comment(abstract_elem, context) if abstract_elem is not None else ""
        
        discussion_elem = comment_parts.find("Discussion") if comment_parts is not None else None
        self.discussion = self._extract_comment(discussion_elem, context) if discussion_elem is not None else None
 
        self.parameters = []
        parameters_elem = root.find(".//Parameters")
        if parameters_elem is not None:
            for param in parameters_elem.findall("Parameter"):
                param_name = param.find("Name")
                param_discussion = param.find(".//Discussion")
                if param_name is None or param_name.text is None or param_name.text == "":
                    continue
                self.parameters.append({
                    "name": param_name.text,
                    "description": self._extract_comment(param_discussion, context) if param_discussion is not None else ""
                })
        
        if comment_parts is not None:
            result_elem = comment_parts.find("ResultDiscussion")
            if result_elem is not None:
                self.result = self._extract_comment(result_elem, context)
            else:
                self.result = None
            throws_elem = comment_parts.find("ThrowsDiscussion")
            if throws_elem is not None:
                self.throws = self._extract_comment(throws_elem, context)
            else:
                self.throws = None
        else:
            self.result = None
            self.throws = None
    
    # Callout tags that map to RST directives (tag -> directive name)
    _CALLOUT_TAGS = {
        "Note": "note",
        "Warning": "warning",
        "Important": "important",
        "Attention": "attention",
        "Tip": "tip",
        "Hint": "hint",
        "Danger": "danger",
        "Caution": "caution",
        "Bug": "admonition",
        "Requires": "admonition",
        "Precondition": "admonition",
        "Postcondition": "admonition",
        "Invariant": "admonition",
        "Complexity": "admonition",
        "Author": "admonition",
        "Authors": "admonition",
        "Copyright": "admonition",
        "Date": "admonition",
        "SeeAlso": "seealso",
        "Since": "admonition",
        "Version": "admonition",
        "Experiment": "admonition",
        "TODO": "admonition",
    }

    def _extract_comment(self, elem, context):
        if elem is None:
            return ""

        parts = []

        # Leading text directly inside the element
        if elem.text:
            parts.append(elem.text)

        for child in elem:
            tag = child.tag

            if tag == "codeVoice":
                # Inline code – optionally cross-reference known symbols
                text = child.text or ""
                if text in context.fullnames:
                    parts.append(f":ref:`{context.fullnames[text].replace(':', '_')}`")
                else:
                    parts.append(f"``{text}``")

            elif tag == "Para":
                # Flush any accumulated inline text, then render the paragraph
                inline = "".join(parts).strip()
                parts = []
                para_text = self._extract_comment(child, context)
                if inline:
                    parts.append(inline + "\n\n" + para_text)
                else:
                    parts.append(para_text)

            elif tag == "CodeListing":
                # Fenced code block; optional language via 'language' attribute
                lang = child.attrib.get("language", "")
                # Code lines are usually in <zCodeLineNumbered> or bare text
                code_lines = []
                raw = child.text or ""
                for line_elem in child:
                    if line_elem.text:
                        code_lines.append(line_elem.text)
                    if line_elem.tail:
                        raw += line_elem.tail
                if code_lines:
                    code_text = "\n".join(code_lines)
                else:
                    code_text = raw
                directive = f"code-block:: {lang}" if lang else "code-block::"
                indented = "\n".join("   " + l for l in code_text.splitlines())
                parts.append(f"\n\n.. {directive}\n\n{indented}\n\n")

            elif tag in ("List-Bullet", "List-Number"):
                # Render a bullet or numbered list
                numbered = (tag == "List-Number")
                items = []
                for item in child.findall("Item"):
                    item_text = self._extract_comment(item, context).strip()
                    # Indent continuation lines
                    item_lines = item_text.splitlines()
                    if item_lines:
                        prefix = "#. " if numbered else "- "
                        first = prefix + item_lines[0]
                        rest = ["  " + l for l in item_lines[1:]]
                        items.append("\n".join([first] + rest))
                parts.append("\n\n" + "\n".join(items) + "\n\n")

            elif tag == "Item":
                # Bare <Item> outside a list container – treat as a bullet
                item_text = self._extract_comment(child, context).strip()
                parts.append(f"- {item_text}")

            elif tag == "Name":
                # Field / parameter name – render as bold
                parts.append(f"**{child.text or ''}**")

            elif tag == "emphasis":
                parts.append(f"*{child.text or ''}*")

            elif tag == "bold":
                parts.append(f"**{child.text or ''}**")

            elif tag == "Link":
                url = child.attrib.get("href", child.text or "")
                label = child.text or url
                parts.append(f"`{label} <{url}>`_")

            elif tag == "Parameter":
                # A single parameter block when encountered inline
                param_name_elem = child.find("Name")
                param_disc_elem = child.find(".//Discussion")
                param_name = param_name_elem.text if param_name_elem is not None else ""
                param_desc = self._extract_comment(param_disc_elem, context) if param_disc_elem is not None else ""
                parts.append(f"\n\n:param {param_name}: {param_desc}")

            elif tag == "Parameters":
                # A whole parameters section encountered inline
                for param in child.findall("Parameter"):
                    param_name_elem = param.find("Name")
                    param_disc_elem = param.find(".//Discussion")
                    param_name = param_name_elem.text if param_name_elem is not None else ""
                    param_desc = self._extract_comment(param_disc_elem, context) if param_disc_elem is not None else ""
                    parts.append(f"\n\n:param {param_name}: {param_desc}")

            elif tag == "ResultDiscussion":
                result_text = self._extract_comment(child, context)
                parts.append(f"\n\n:returns: {result_text}")

            elif tag == "ThrowsDiscussion":
                throws_text = self._extract_comment(child, context)
                parts.append(f"\n\n:raises: {throws_text}")

            elif tag in self._CALLOUT_TAGS:
                directive = self._CALLOUT_TAGS[tag]
                body_text = self._extract_comment(child, context).strip()
                indented = "\n".join("   " + l for l in body_text.splitlines())
                if directive == "admonition":
                    # Generic admonition uses the tag name as its title
                    parts.append(f"\n\n.. {directive}:: {tag}\n\n{indented}\n\n")
                else:
                    parts.append(f"\n\n.. {directive}::\n\n{indented}\n\n")

            else:
                # Unknown tag – recurse and preserve text
                parts.append(self._extract_comment(child, context))

            if child.tail:
                parts.append(child.tail)

        return "".join(parts).strip()


@dataclass
class Structure:
    """
    A structure in the document.
    Initialized from a dictionary decoded from the documentation JSON file.
    """

    name: str
    """
    The name of the structure. Corresponds to the `key.name` key of the body passed to the initializer.
    """

    def __init__(self, body: dict):
        self.name = body["key.name"]


@dataclass
class MARK(Structure):
    """
    A mark (`MARK: -`) comment in the source file.
    Used to separate symbols into categories.
    """

    name: str
    """
    Name of the section.
    """

    def __init__(self, body: dict):
        self.name = body["key.name"].split("MARK: - ")[-1]


@dataclass
class Symbol(Structure):
    """
    A source code symbol.
    """

    name: str
    """
    Relative name of the symbol.
    """

    module_name: str
    """
    The name of the module exporting this symbol.
    """

    kind: DeclarationKind
    """
    Kind of declaration.
    """

    usr: Optional[str]
    """
    The unique identifier of the symbol.
    Corresponds to its page file name (without the extension) by replacing `":"` with `":"`.
    """

    declaration: AnnotatedDeclaration
    """
    Type annotated declaration.
    """

    accessibility: Accessibility
    """
    Symbol's accessibility level.
    """

    documentation: Optional[Documentation]
    """
    An optional documentation attached to the symbol.
    """

    inherited_types: Optional[List[str]]
    """
    Types the symbol inherits from.
    """

    substructure: List[Structure]
    """
    Sub-declarations of the symbol.
    """

    context: GenerationContext
    """
    The generation context fetching this symbol.
    """

    _body: Dict

    def __init__(self, body: Dict, context: GenerationContext):
        self._body = body
        self.context = context
        self.name = body["key.name"]
        self.module_name = body["key.modulename"]
        self.kind = DeclarationKind(body["key.kind"])
        self.usr = body.get("key.usr")
        self.accessibility = Accessibility(body.get("key.accessibility", "source.lang.swift.accessibility.internal"))
        if "key.inheritedtypes" in body:
            self.inherited_types = list(map(lambda x: x["key.name"], body.get("key.inheritedtypes", [])))
        else:
            self.inherited_types = None

        try:
            self.declaration = AnnotatedDeclaration(body["key.annotated_decl"])
        except KeyError:
            self.declaration = AnnotatedDeclaration(f"<Declaration>{body.get('key.parsed_declaration', '')}</Declaration>")
        try:
            self.documentation = Documentation(body["key.doc.full_as_xml"], context)
        except KeyError:
            self.documentation = None
        try:
            self.substructure = list(map(lambda x: parse(x, context), body["key.substructure"]))
        except KeyError as e:
            self.substructure = []


def fetch_fullnames(body: Dict, context: GenerationContext, parent_names: List[str] = []):
    """
    Fetches a symbol's full name (including their module) and all their sub declarations recursively, mapped to their USR value and writes them to :py:attr:`GenerationContext.fullnames`.

    :param body: The dictionary value of the symbol.
    :para context: The generation context to write to.
    :parent_names: List of parents containing the fetched declaration.
    """

    kind = body.get("key.kind")
    if kind in ("source.lang.swift.decl.mark", "source.lang.swift.syntaxtype.comment.mark"):
        return
    
    if kind == "source.lang.swift.decl.enumcase":
        for sub in body.get("key.substructure", []):
            fetch_fullnames(sub, context, parent_names)
        return

    name = body.get("key.name")
    usr = body.get("key.usr")
    
    if name and usr:
        comp = parent_names + [name]
        module_name = body.get("key.modulename")
        if module_name:
            comp.insert(0, module_name)
        context.fullnames[".".join(comp)] = usr
        
    for sub in body.get("key.substructure", []):
        fetch_fullnames(sub, context, parent_names + ([name] if name else []))


def parse(body: Dict, context: GenerationContext) -> Structure:
    """
    Parses a symbol from the documentation JSON file and returns it.

    :param body: The dictionary value of the symbol.
    :param context: The generation context to write to.
    :rtype: Symbol
    """
    try:
        if body["key.kind"] in ("source.lang.swift.decl.mark", "source.lang.swift.syntaxtype.comment.mark"):
            return MARK(body)
        elif body["key.kind"] == "source.lang.swift.decl.enumcase":
            statement =  Symbol(body["key.substructure"][0], context)
        else:
            statement = Symbol(body, context)
        return statement
    except Exception as e:
        print(f"Error parsing '{body.get("key.name", "unknown")}': {e}", file=sys.stderr)
        raise e


__all__ = [
    "DeclarationKind",
    "Accessibility",
    "GenerationContext",
    "AnnotatedDeclaration",
    "Annotation",
    "Documentation",
    "Structure",
    "MARK",
    "Symbol",
    "fetch_fullnames",
    "parse"
]
