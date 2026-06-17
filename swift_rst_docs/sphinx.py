import os

from sphinx import addnodes
from sphinx.util import logging
from sphinx.roles import XRefRole
from sphinx.domains import Domain
from sphinx.application import Sphinx
from sphinx.util.nodes import make_refnode
from sphinx.util.osutil import relative_uri
from sphinx.util.docutils import SphinxDirective

from importlib.metadata import version

from docutils import nodes
from docutils.utils import new_document
from docutils.frontend import OptionParser
from docutils.statemachine import StringList
from docutils.parsers.rst import Parser, directives

from .types import Accessibility, GenerationContext
from .doc import (
        Page,
        MainPage,
        ModulePage,
        fetch_documents,
        generate_documentation,
        _DOCUMENTATION_LINK_STYLE
)


logger = logging.getLogger(__name__)


API_DIRECTORY_NAME = "_api"


class SphinxContext:
    def __init__(self):
        self.gencontexts = []
        self.module_contexts = {}
        self.symbols_map = {}
        self.generated_files = []


_sphinx_contexts: dict[Sphinx, SphinxContext] = {}


class ModuleDirective(SphinxDirective):

    required_arguments = 1

    has_content = True

    option_spec = {
        "members": directives.flag,
        "declaration": directives.flag
    }

    def parse(self, rst: str) -> list[nodes.Node]:
        std = self.env.get_domain("std")
        # Resolve toctree document names and remove title
        lines = []
        context = _sphinx_contexts[self.env.app]
        for line in rst.splitlines():
            unspaced = line.replace(" ", "")
            try:
                docname = context.symbols_map[unspaced]
                docname = relative_uri(self.env.docname, docname)
                line = line.replace(unspaced, docname)
            except KeyError:
                pass
            lines.append(line)

        container = nodes.container()
        self.state.nested_parse(
            StringList(lines, source="<generated>"),
            self.content_offset,
            container
        )
        return container.children

    def run(self):
        module_name = self.arguments[0]
        context = _sphinx_contexts[self.env.app]
        if module_name not in context.module_contexts:
            self.error(f"No Swift module named '{module_name}' was found.")
        gen_context = context.module_contexts[module_name]
        module_page = ModulePage(
            module_name,
            gen_context,
            False,
            "declaration" in self.options,
            None if "members" in self.options else list(self.content)
        )
        return self.parse(module_page.contents)


class SwiftDomain(Domain):
    name = "swift"
    label = "Swift"

    roles = {
        "symbol": XRefRole(),
    }

    directives = {
        "module": ModuleDirective
    }

    def resolve_xref(
        self,
        env,
        fromdocname,
        builder,
        typ,
        target,
        node,
        contnode,
    ):
        if typ != "symbol":
            return None

        docname = None
        fullnames = {}

        context = _sphinx_contexts[env.app]
        for doc in context.gencontexts:
            fullnames.update(doc.fullnames)
        if target in fullnames:
            docname = fullnames[target].replace(":", "_")
            has_module_name = True
        else:
            matching = list(filter(lambda n: ".".join(n.split(".")[1:]) == target, fullnames.keys()))
            if len(matching) > 0:
                docname = fullnames[matching[0]].replace(":", "_")
                has_module_name = False
            if len(matching) > 1:
                formatted_matches = list(map(lambda m: f"'{m}'", ", ".join(matching)))
                msg = f"{len(matching)} matches found from different modules for '{target}' (using the first one): {formatted_matches}. Disambiguate by specifying the module name."
                logging.warning(msg)

        if docname is None:
            return None

        std = env.get_domain("std")
        docname, labelid, sectname = std.data["labels"][docname.lower()]
        shortened_target = target if not has_module_name else ".".join(target.split(".")[1:])

        contnode = nodes.literal()
        contnode += nodes.Text(shortened_target)

        return make_refnode(
            builder,
            fromdocname,
            docname,
            None,
            contnode,
            shortened_target 
        )


def generate_symbol_pages(app: Sphinx):
    src_dir = app.srcdir
    context_obj = SphinxContext()
    _sphinx_contexts[app] = context_obj

    # Find all _api directories recursively
    for root, dirs, files in os.walk(src_dir):
        if API_DIRECTORY_NAME in dirs:
            sourcekitten_dir = os.path.join(root, API_DIRECTORY_NAME)
            output_dir = os.path.join(root, API_DIRECTORY_NAME)
           
            index_title = os.path.basename(root) 
                        
            context = GenerationContext(
                index_title=index_title,
                min_accessibility=Accessibility.PUBLIC
            )
            context_obj.gencontexts.append(context)

            # Find all json files in .sourcekitten
            json_files = []
            for item in os.listdir(sourcekitten_dir):
                if item.endswith(".json"):
                    json_files.append(os.path.join(sourcekitten_dir, item))

            for json_path in json_files:
                fetch_documents(json_path, context)
 
            os.makedirs(output_dir, exist_ok=True)
            
            # Write pages
            for page in generate_documentation(context, False):
                if isinstance(page, MainPage):
                    continue
                elif isinstance(page, ModulePage):
                    context_obj.module_contexts[page.name] = context
                else:
                    page_path = os.path.join(output_dir, page.file_name)
                    if not os.path.exists(page_path):
                        context_obj.generated_files.append(page_path)
                    with open(page_path, "w+") as f:
                        relpath = os.path.relpath(page_path, app.srcdir)
                        relpath = os.path.splitext(relpath)[0]
                        page_name = page.file_name.split(".")[0]
                        if page_name in context_obj.symbols_map:
                            symbol_name = list(filter(lambda i: i[1] == page_name, context.fullnames.items()))
                            if len(symbol_name) > 0:
                                logger.warning(f"Duplicated symbol: '{symbol_name[0][0]}'")
                        context_obj.symbols_map[page_name] = relpath 
                        f.write(page.contents)


def cleanup_source(app, exc):
    if app in _sphinx_contexts:
        context = _sphinx_contexts[app]
        for doc in context.generated_files:
            if os.path.exists(doc):
                os.remove(doc)
        del _sphinx_contexts[app]


def setup(app: Sphinx):
    app.connect("builder-inited", generate_symbol_pages)
    app.connect("build-finished", cleanup_source)
    app.add_domain(SwiftDomain)
    return {
        "version": version("swift_rst_docs"),
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
