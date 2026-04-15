from .doc import fetch_documents, generate_documentation
from .types import GenerationContext, Accessibility
from argparse import ArgumentParser
import os


_accessibility = {
    "public": Accessibility.PUBLIC,
    "internal": Accessibility.INTERNAL,
    "fileprivate": Accessibility.FILEPRIVATE,
    "private": Accessibility.PRIVATE,
    "open": Accessibility.OPEN,
}


def main():
    """
    CLI entry point.
    """

    parser = ArgumentParser()
    parser.add_argument("--documentation-file-path", "-d", required=True, help="SourceKitten JSON file path.")
    parser.add_argument("--output-path", "-o", required=True, help="Output directory path.")
    parser.add_argument("--title", "-t", required=True, help="Index title.")
    parser.add_argument("--overview", "-v", required=False, help="Overview file path or contents.")
    parser.add_argument("--files", "-f", required=False, action="append", help="File names to document. Can be base names or paths relative to any directory in the source code. Defaults to all.")
    parser.add_argument("--symbols", "-s", required=False, action="append", help="Symbols to document. Defaults to all.")
    parser.add_argument("--min-accessibility", "-a", required=False, choices=list(_accessibility.keys()), default="public", help="Minimum accessibility of symbols to document. Defaults to public.")
    args = parser.parse_args()
    try:
        with open(args.overview, "r") as f:
            overview = f.read()
    except FileNotFoundError:
        overview = args.overview
    context = GenerationContext(
        index_title=args.title,
        overview=overview,
        min_accessibility=_accessibility[args.min_accessibility],
        documented_objects=args.files,
        documented_symbols=args.symbols,
    )
    fetch_documents(args.documentation_file_path, context)
    pages = generate_documentation(context)
    os.makedirs(args.output_path, exist_ok=True)
    for page in pages:
        path = os.path.join(args.output_path, page.file_name)
        try:
            f = open(path, "r")
            contents = f.read()
            f.close()
            if contents == page.contents:
                continue
        except FileNotFoundError:
            pass
        with open(path, "w+") as f:
            f.write(page.contents)
