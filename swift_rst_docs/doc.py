from .types import Symbol, MARK, parse, fetch_fullnames, GenerationContext, DeclarationKind
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
       document.querySelectorAll("a[href*='#doclink']").forEach(function(link) {
           link.classList.add("doc-link");
           link.href = link.href.replace("#doclink", "");
       });
   }
   </script>

"""


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
        self.contents = f"``{item.name}``\n{('=' * len(item.name))}====\n\n"
        if item.usr:
            self.contents += f".. index:: {item.usr}\n\n"
        if item.documentation and item.documentation.comment:
            self.contents += f"{item.documentation.comment}\n\n"

        self.contents += _DOCUMENTATION_LINK_STYLE

        self.contents += """

.. raw:: html

   <style>
   .toctree-wrapper ul {
       list-style-type: none !important;
       padding-left: 0 !important;
       margin-left: 0 !important;
   }

   .toctree-l1 {
       list-style: none !important;
   }

   .main .toctree-l1 > a > code > .pre { font-size: 120% !important; }
   </style>

"""

        self.contents += "Declaration\n-----------\n\n"
        decl = item.declaration
        self.contents += highlight_statement(decl, True, item.inherited_types is not None, context)
                
        if item.documentation and item.documentation.parameters:
            self.contents += "Parameters\n----------\n\n"
            for param in item.documentation.parameters:
                self.contents += f"- **{param['name']}**: {param['description']}\n"
            self.contents += "\n"
        
        if item.documentation and item.documentation.result:
            self.contents += "Returns\n-------\n\n"
            self.contents += f"{item.documentation.result}\n\n"
                
        if item.documentation and item.documentation.discussion:
            self.contents += "Discussion\n----------\n\n"
            self.contents += f"{item.documentation.discussion}\n\n"

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
                if isinstance(subitem, MARK) or subitem.accessibility.order < context.min_accessibility.order:
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
            if isinstance(subitem, MARK) or subitem.accessibility.order < context.min_accessibility.order:
                continue
            self._subpages.append(Page(subitem, context))

        if is_mark:
            marks_and_items = list(filter(lambda x: isinstance(x, MARK) or x.accessibility.order >= context.min_accessibility.order, item.substructure[:]))
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
                else:
                    sections[-1][1].append(subitem)

            for section in sections:
                if not section[1]: continue
                i = 0
                for _item in section[1]:
                    if _item.usr:
                        usr_name = _item.usr.replace(':', '_')
                    else:
                        continue

                    if i == 0:
                        self.contents += f"\n{section[0]}\n{'-' * len(section[0])}\n"
                    i += 1

                    self.contents += f"\n.. toctree::\n   :maxdepth: 1\n\n"
                    self.contents += f"   {usr_name}\n"
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

                        if i == 0:
                            self.contents += f"\n{decl_type}\n{'-' * len(decl_type)}\n"
                        i += 1

                        self.contents += f".. toctree::\n   :maxdepth: 1\n\n"
                        self.contents += f"   {usr_name}\n"
                        if _item.documentation and _item.documentation.comment:
                            self.contents += f"\n{_item.documentation.comment}\n\n"
                        self.contents += "\n"

        if item.inherited_types:
            self.contents += "\nConforms to\n-----------\n\n"
            for inherited in item.inherited_types:
                usr = context.find(inherited, item.module_name)
                if usr:
                    self.contents += f"- `{inherited} <{usr.replace(':', '_')}.html#doclink>`_\n"
                else:
                    self.contents += f"- ``{inherited}``\n"
            self.contents += "\n"


class MainPage(Page):
    """
    The main index page of the whole documentation.
    This is the same as the module index page when there is only one module.
    """

    def __init__(self, contents: str, context: GenerationContext):
        self.file_name = "index.rst"
        self.contents = contents
        self.context = context


class ModulePage(Page):
    """
    The index page for a module.
    """

    def __init__(self, module_name: str, contents: str, context: GenerationContext):
        self.file_name = f"{module_name}.rst"
        self.contents = contents
        self.context = context


def replace_links(text: str, module_name: Optional[str], context: GenerationContext) -> str:
    """
    Replaces symbol references with a link to their html page and returns the result.
    :py:func:`swift_rst_docs.fetch_documents` should have been called for links to be correctly generated.

    :param text: The documentation text to parse.
    :param module_name: The current module name (can be None). Finds the symbol in the current module first, then in the global scope if the module name is specified in the symbol's name.
    :param context: The generation context.
    :rtype: str
    """

    new_text = re.sub(
        r"``(.*?)``",
        lambda match: f"`{match.group(1)} <{(context.find(match.group(1), module_name) or "").replace(':', '_')}.html#doclink>`_" if context.find(match.group(1), module_name) else match.group(0),
        text
    )
    return new_text


def generate_documentation(context: GenerationContext) -> list[Page]:
    """
    Generates and returns all the documentation pages for the passed generation context.
    :py:func:`swift_rst_docs.fetch_documents` should have been called first.
    If multiple modules were fetched, will generate an index page for each module.

    :param context: The generation context.
    :rtype: list[Page]
    """

    sections = [
        ("Classes", DeclarationKind.CLASS),
        ("Structures", DeclarationKind.STRUCT),
        ("Functions", DeclarationKind.FUNCTION),
        ("Protocols", DeclarationKind.PROTOCOL),
        ("Enumerations", DeclarationKind.ENUM),
        ("Extensions", DeclarationKind.EXTENSION)
    ]

    pages: list[Page] = []
    document: dict[DeclarationKind, list[Symbol]] = {}
    modules: dict[str, list[Symbol]] = {}
    for item in context.body:
        if not item.usr:
            continue
        if item.module_name not in modules:
            modules[item.module_name] = []
        page = Page(item, context)
        pages.append(page)
        modules[item.module_name].append(item)

    main_document = f"{context.index_title}\n{"=" * len(context.index_title)}"
    main_document += "\n\n"

    if context.overview:
        if len(modules) == 1:
            only_module_name = list(modules.keys())[0]
        else:
            only_module_name = None
        overview_text = replace_links(context.overview, only_module_name, context)
        main_document += f"{overview_text}\n"

    main_document += _DOCUMENTATION_LINK_STYLE

    if len(modules) == 1:
        module_name, module_items = list(modules.items())[0]

        main_document += f""".. code-block:: swift

    import {module_name}


"""

        for title, key in sections:
            items = list(filter(lambda x: x.kind == key, module_items))
            valid_items = []
            for item in items:
                if item.usr:
                    valid_items.append(item.usr.replace(":", "_"))
            
            if valid_items:
                main_document += f".. toctree::\n   :maxdepth: 1\n   :caption: {title}\n\n"
                for item_usr in valid_items:
                    main_document += f"   {item_usr}\n"
                main_document += "\n"
    else:
        for module_name, module_items in modules.items():
            module_document = f"{module_name}\n{"=" * len(module_name)}"
            module_document += "\n\n"
            module_document += _DOCUMENTATION_LINK_STYLE

            module_document += f""".. code-block:: swift

    import {module_name}


"""

            for title, key in sections:
                items = list(filter(lambda x: x.kind == key, module_items))
                valid_items = []
                for item in items:
                    if item.usr:
                        valid_items.append(item.usr.replace(":", "_"))
                
                if valid_items:
                    module_document += f".. toctree::\n   :maxdepth: 1\n   :caption: {title}\n\n"
                    for item_usr in valid_items:
                        module_document += f"   {item_usr}\n"
                    module_document += "\n"

            pages.append(ModulePage(module_name, module_document, context))

        main_document += f".. toctree::\n   :maxdepth: 2\n   :caption: Modules\n\n"
        for module_name in modules.keys():
            main_document += f"   {module_name}\n"
        main_document += "\n"

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

    all_pages.append(MainPage(main_document, context))
    return all_pages


def fetch_documents(api_file_path: str, context: GenerationContext):
    """
    Fetches symbols from a SourceKitten documentation JSON file path and writes them to :py:attr:`swift_rst_docs.GenerationContext.body`.

    :param api_file_path: The path to the SourceKitten documentation JSON file.
    :param context: The generation context.
    """

    with open(api_file_path, "r") as f:
        structure = json.load(f)

    body: list[Symbol] = []

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
                existing_statement = list(filter(lambda x: x.name == parsed.name and x.module_name == parsed.module_name, body))[0]
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
