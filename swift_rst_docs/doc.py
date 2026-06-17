from .types import Symbol, Structure, MARK, parse, fetch_fullnames, GenerationContext, DeclarationKind
from .highlight import highlight_statement
from dataclasses import dataclass
from typing import Optional
import warnings
import json
import os
import re


_DOCUMENTATION_LINK_STYLE = """
.. raw:: html

   <style>
       .doc-link {
           font-family: var(--font-stack--monospace);
       }
   </style>

   <script type="text/javascript">
       window.onload = function() {
           document.querySelectorAll("a[href^='s_']").forEach(function(link) {
               link.classList.add("doc-link");
           });
       }
   </script>

   <style>
       .symbol-toctree ul {
           list-style-type: none !important;
           padding-left: 0 !important;
           margin-left: 0 !important;
       }

       .symbol-toctree .toctree-l1 {
           list-style: none !important;
       }

       .symbol-toctree .toctree-l1 > a > code > .pre {
           font-size: 120% !important;
       }
   </style>
"""


_SECTIONS = [
    ("Classes", DeclarationKind.CLASS),
    ("Structures", DeclarationKind.STRUCT),
    ("Functions", DeclarationKind.FUNCTION),
    ("Protocols", DeclarationKind.PROTOCOL),
    ("Enumerations", DeclarationKind.ENUM),
    ("Extensions", DeclarationKind.EXTENSION)
]


class Page:
    """
    A Swift documentation page in RST format.

    Initializing from a :py:class:`swift_rst_docs.Symbol` and a :py:class:`swift_rst_docs.GenerationContext` automatically generates the contents. :py:func:`swift_rst_docs.fetch_documents` should have been called for links to be correctly generated.
    """

    file_name: str
    """
    File name with extension.
    """

    contents: str
    """
    The contents of the generated page.
    """

    _subpages: list["Page"]

    def __init__(self, item: Symbol, context: GenerationContext):

        self._subpages = []

        self.file_name = (item.usr or item.name).replace(':', '_')+".rst"
        self.contents = ":orphan:\n\n"
        if item.usr:
            self.contents += f".. _{item.usr.replace(":", "_")}:\n\n"
        self.contents += f"``{item.name}``\n{('=' * len(item.name))}====\n\n"
        
        if item.documentation and item.documentation.comment:
            self.contents += f"{item.documentation.comment}\n\n"

        self.contents += _DOCUMENTATION_LINK_STYLE

        self.contents += "\n.. rubric:: Declaration\n"
        decl = item.declaration
        self.contents += highlight_statement(decl, True, item.inherited_types is not None, context)
                
        if item.documentation and item.documentation.parameters:
            self.contents += ".. rubric:: Parameters\n\n"
            for param in item.documentation.parameters:
                self.contents += f"- **{param['name']}**: {replace_links(param['description'], item.module_name, context)}\n"
            self.contents += "\n"
        
        if item.documentation and item.documentation.result:
            self.contents += ".. rubric:: Returns\n\n"
            self.contents += f"{replace_links(item.documentation.result, item.module_name, context)}\n\n"
                
        if item.documentation and item.documentation.discussion:
            self.contents += ".. rubric:: Discussion\n\n"
            self.contents += f"{replace_links(item.documentation.discussion, item.module_name, context)}\n\n"

        subitems: list[Symbol] = []
        is_mark = any(isinstance(x, MARK) for x in item.substructure)

        order = [
            "Cases",
            "Initializers",
            "Properties",
            "Static Properties",
            "Functions",
            "Static Functions",
            "Structures",
            "Enumerations",
            "Classes"
        ]

        if not is_mark:
            categorized_subitems: dict[str, list[Symbol]] = {}
            for subitem in item.substructure:
                if not isinstance(subitem, Symbol):
                    continue
                if subitem.accessibility.order < context.min_accessibility.order:
                    continue
            
                match subitem.kind:
                    case DeclarationKind.ENUM_ELEMENT:
                        friendly_kind = "Cases"
                    case DeclarationKind.INSTANCE_METHOD:
                        if subitem.name.startswith("init("):
                            friendly_kind = "Initializers"
                        else:
                            friendly_kind = "Functions"
                    case DeclarationKind.STATIC_METHOD:
                        friendly_kind = "Static Functions"
                    case DeclarationKind.CLASS_VARIABLE:
                        friendly_kind = "Class Properties"
                    case DeclarationKind.CLASS_METHOD:
                        friendly_kind = "Class Functions"
                    case DeclarationKind.INSTANCE_VARIABLE:
                        friendly_kind = "Properties"
                    case DeclarationKind.STATIC_VARIABLE:
                        friendly_kind = "Static Properties"
                    case DeclarationKind.STRUCT:
                        friendly_kind = "Structures"
                    case DeclarationKind.ENUM:
                        friendly_kind = "Enumerations"
                    case DeclarationKind.CLASS:
                        friendly_kind = "Classes"
                    case _:
                        friendly_kind = subitem.kind.value.split(".")[-1].capitalize() + "s"
                    
                if friendly_kind not in categorized_subitems:
                    categorized_subitems[friendly_kind] = []
                categorized_subitems[friendly_kind].append(subitem)

        for subitem in item.substructure:
            if not isinstance(subitem, Symbol): 
                continue
            if subitem.accessibility.order < context.min_accessibility.order:
                continue
            self._subpages.append(Page(subitem, context))

        if is_mark:
            marks_and_items = list(filter(lambda x: isinstance(x, MARK) or (isinstance(x, Symbol) and x.accessibility.order >= context.min_accessibility.order), item.substructure[:]))
            if len(marks_and_items) > 0 and not isinstance(marks_and_items[0], MARK):
                has_mark_before_inits = False
                has_init_items = False
                inits_before_marks = []
                for i, subitem in enumerate(marks_and_items):
                    if isinstance(subitem, MARK) and not has_init_items:
                        has_mark_before_inits = True
                    elif isinstance(subitem, Symbol) and subitem.name.startswith("init("):
                        has_init_items = True
                        if not has_mark_before_inits:
                            inits_before_marks.append((i, subitem))
                    
                if not has_mark_before_inits and has_init_items:
                    marks_and_items.insert(0, MARK({"key.name": "MARK: - Initializers"}))
                    for init in inits_before_marks:
                        marks_and_items.remove(init[1])
                        marks_and_items.insert(1, init[1])
                    marks_and_items.insert(len(inits_before_marks)+1, MARK({"key.name": f"MARK: - Members"}))
                else:
                    marks_and_items.insert(0, MARK({"key.name": f"MARK: - Members"}))

            sections: list[tuple[str, list[Symbol]]] = []
            for subitem in marks_and_items:
                if isinstance(subitem, MARK):
                    sections.append((subitem.name, []))
                elif isinstance(subitem, Symbol):
                    sections[-1][1].append(subitem)

            for section in sections:
                if not section[1]: continue
                i = 0
                for _item in section[1]:
                    if _item.usr:
                        usr_name = _item.usr.replace(':', '_')
                    else:
                        continue

                    if "key.overrides" in _item._body:
                        continue

                    if i == 0:
                        self.contents += f"\n.. rubric:: {section[0]}\n\n"
                    i += 1

                    self.contents += "\n.. raw:: html\n\n"
                    self.contents += "   <div class='symbol-toctree'>\n\n"
                    self.contents += f"\n.. toctree::\n   :maxdepth: 1\n\n"
                    self.contents += f"   {usr_name}\n\n"
                    self.contents += ".. raw:: html\n\n"
                    self.contents += "   </div>\n"
                    if _item.documentation and _item.documentation.comment:
                        self.contents += f"\n{_item.documentation.comment}\n\n"

        else:
            for decl_type in order:
                if decl_type in categorized_subitems:
                    i = 0
                    for _item in sorted(categorized_subitems[decl_type], key=lambda x: x.name):
                        if _item.usr:
                            usr_name = _item.usr.replace(':', '_')
                        else:
                            continue

                        if "key.overrides" in _item._body:
                            continue

                        if i == 0:
                            self.contents += f"\n.. rubric:: {decl_type}\n"
                        i += 1

                        self.contents += "\n.. raw:: html\n\n"
                        self.contents += "   <div class='symbol-toctree'>\n\n"
                        self.contents += f".. toctree::\n   :maxdepth: 1\n\n"
                        self.contents += f"   {usr_name}\n\n"
                        self.contents += ".. raw:: html\n\n"
                        self.contents += "   </div>\n"
                        if _item.documentation and _item.documentation.comment:
                            self.contents += f"\n{_item.documentation.comment}\n\n"
                        self.contents += "\n"

        if item.inherited_types:
            self.contents += ".. rubric:: Conforms to\n\n"
            for inherited in item.inherited_types:
                usr = context.find(inherited, item.module_name)
                if usr:
                    self.contents += f"- :ref:`{usr.replace(':', '_')}`\n"
                else:
                    self.contents += f"- ``{inherited}``\n"
            self.contents += "\n"


class MainPage(Page):
    """
    The main index page of the whole documentation.
    This is the same as the module index page when there is only one module.
    """

    def __init__(self, context: GenerationContext):
        self.file_name = "index.rst"
        self.context = context
        self.contents = f"{context.index_title}\n{('=' * len(context.index_title))}\n\n"

        modules: dict[str, list[Symbol]] = {}
        for item in context.body:
            if item.module_name not in modules:
                modules[item.module_name] = []
            modules[item.module_name].append(item)

        if context.overview:
            if len(modules) == 1:
                only_module_name = list(modules.keys())[0]
            else:
                only_module_name = None
            overview_text = replace_links(context.overview, only_module_name, context)
            self.contents += f"{overview_text}\n"

        self.contents += _DOCUMENTATION_LINK_STYLE

        if len(modules) == 1:
            module_name, module_items = list(modules.items())[0]

            self.contents += f""".. code-block:: swift

    import {module_name}

"""

            for title, key in _SECTIONS:
                items = list(filter(lambda x: x.kind == key, module_items))
                valid_items = []
                for item in items:
                    if item.usr:
                        valid_items.append(item.usr.replace(":", "_"))
                
                if valid_items:
                    self.contents += "\n.. raw:: html\n\n"
                    self.contents += "   <div class='symbol-toctree'>\n\n"
                    self.contents += f".. toctree::\n   :maxdepth: 1\n   :caption: {title}\n\n"
                    for item_usr in valid_items:
                        self.contents += f"   {item_usr}\n"
                    self.contents += "\n"
                    self.contents += "\n.. raw:: html\n\n"
                    self.contents += "\n\n   </div>\n\n"
        else:
            self.contents += "\n.. raw:: html\n\n"
            self.contents += "   <div class='symbol-toctree'>\n\n"
            self.contents += f".. toctree::\n   :maxdepth: 2\n   :caption: Modules\n\n"
            for module_name in modules.keys():
                self.contents += f"   {module_name}\n"
            self.contents += "\n"
            self.contents += "\n.. raw:: html\n\n"
            self.contents += "\n\n   </div>\n\n"


class ModulePage(Page):
    """
    The index page for a module.
    """

    name: str
    """
    The module name.
    """

    title: bool
    """
    Whether to include the document's title.
    """

    declaration: bool
    """
    Whether to include the module's declaration.
    """

    members: list[str] | None
    """
    Member names (without the module) to include in the module page.
    If ``None``, all members will be included.
    """

    def __init__(self, name: str, context: GenerationContext, title: bool = True, declaration: bool = True, members: list[str] | None = None):
        self.file_name = f"{name}.rst"
        self.context = context
        self.name = name
        self.declaration = declaration
        self.members = members

        self.contents = ""
        if title:
            self.contents += f"{name}\n{('=' * len(name))}\n"
        self.contents += _DOCUMENTATION_LINK_STYLE

        module_items = list(filter(lambda x: x.module_name == name, context.body))

        if declaration:
            self.contents += f""".. code-block:: swift

    import {name}

"""

        for _title, key in _SECTIONS:
            items = list(filter(lambda x: x.kind == key, module_items))
            valid_items = []
            for item in items:
                if item.usr:
                    valid_items.append(item)
            if not valid_items:
                continue
            self.contents += f"\n.. rubric:: {_title}\n"
            for item in valid_items:
                if members is not None and item.name not in members:
                    continue
                if not item.usr:
                    continue
                self.contents += "\n.. raw:: html\n\n"
                self.contents += "   <div class='symbol-toctree'>\n\n"
                self.contents += f".. toctree::\n   :maxdepth: 1\n\n"
                self.contents += f"   {item.usr.replace(':', '_')}\n"
                self.contents += "\n.. raw:: html\n\n"
                self.contents += "   </div>\n"
                if item.documentation and item.documentation.comment:
                    self.contents += f"\n\n{item.documentation.comment}\n\n"


def replace_links(text: str, module_name: Optional[str], context: GenerationContext) -> str:
    """
    Replaces symbol references with a link to their html page and returns the result.
    :py:func:`swift_rst_docs.fetch_documents` should have been called for links to be correctly generated.

    :param text: The documentation text to parse.
    :param module_name: The current module name (can be None). Finds the symbol in the current module first, then in the global scope if the module name is specified in the symbol's name.
    :param context: The generation context.
    :rtype: str
    """

    def doc_name(match):
        return (context.find(match.group(1), module_name) or "").replace(':', '_')

    new_text = re.sub(
        r"``(.*?)``",
        lambda match: f":ref:`{doc_name(match)}`" if context.find(match.group(1), module_name) else match.group(0),
        text
    )

    return new_text


def generate_documentation(context: GenerationContext, index: bool = True) -> list[Page]:
    """
    Generates and returns all the documentation pages for the passed generation context.
    :py:func:`swift_rst_docs.fetch_documents` should have been called first.
    If multiple modules were fetched, will generate an index page for each module.

    The ``ìndex`` argument controls whether an index page should be generated.
    If it's ``True`` and only one module is documented, the index page will correspond to that module.
    If it's ``False``, the module page will be generated in its own file as it happens with multiple modules but no 'index.rst' page will be generated. 

    :param context: The generation context.
    :param index: Whether to generate an index page.
    :rtype: list[Page]
    """

    pages: list[Page] = []
    module_names: set[str] = set()
    for item in context.body:
        if not item.usr:
            continue
        module_names.add(item.module_name)
        page = Page(item, context)
        pages.append(page)

    if not (len(module_names) == 1 and index):
        for module_name in module_names:
            pages.append(ModulePage(module_name, context))

    all_pages: list[Page] = []
    
    def flatten(p: Page):
        all_pages.append(p)
        try:
            for sub in p._subpages:
                flatten(sub)
        except AttributeError:
            pass

    for page in pages:
        flatten(page)

    if index:
        all_pages.append(MainPage(context))
    return all_pages


def fetch_documents(api_file_path: str, context: GenerationContext):
    """
    Fetches symbols from a SourceKitten documentation JSON file path and writes them to :py:attr:`swift_rst_docs.GenerationContext.body`.

    :param api_file_path: The path to the SourceKitten documentation JSON file.
    :param context: The generation context.
    """

    with open(api_file_path, "r") as f:
        structure = json.load(f)

    body: list[Structure] = []

    for objects in structure:
        object_path = list(objects.keys())[0]
        if context.documented_objects is not None and len(list(filter(lambda o: object_path.endswith(o), context.documented_objects))) == 0:
            continue

        doc_object = objects[object_path]
        items = doc_object["key.substructure"]
        for item in items:
            fetch_fullnames(item, context)

    for objects in structure:
        object_path = list(objects.keys())[0]
        if context.documented_objects is not None and len(list(filter(lambda o: object_path.endswith(o), context.documented_objects))) == 0:
            continue

        doc_object = objects[object_path]
        items = doc_object["key.substructure"]
        for item in items:
            parsed = parse(item, context)
            if parsed.name in list(map(lambda x: x.name, body)):
                def filter_statements(x: Structure) -> bool:
                    if not isinstance(parsed, Symbol) or not isinstance(x, Symbol):
                        return False
                    return x.name == parsed.name and x.module_name == parsed.module_name
                existing_statement = list(filter(filter_statements, body))[0]
                if isinstance(parsed, Symbol) and isinstance(existing_statement, Symbol):
                    if parsed.kind == DeclarationKind.EXTENSION:
                        existing_statement.substructure += parsed.substructure
                    else:
                        i = body.index(existing_statement)
                        body.remove(existing_statement)
                        parsed.substructure += existing_statement.substructure
                        body.insert(i, parsed)
                else:
                    body.append(parsed)
            else:
                body.append(parsed)

    for item in body:
        if not isinstance(item, Symbol):
            continue
        if item.accessibility.order < context.min_accessibility.order:
            continue
        if context.documented_symbols is not None and item.name not in context.documented_symbols:
            continue
        context.body.append(item)


__all__ = [
    "fetch_documents",
    "generate_documentation",
    "replace_links",
    "Page",
    "MainPage",
    "ModulePage",
]

