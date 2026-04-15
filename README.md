# swift-rst-docs

Python library and cli to generate reStructuredText documentation for Swift projects from [SourceKitten](https://github.com/jpsim/SourceKitten) output files to use with [Sphinx](https://www.sphinx-doc.org).

This tool assumes the Sphinx output type is HTML because it embeds raw HTML and uses links ending with `.html`.

See the [documentation](https://gatit.es/emma/cosas/documentaciones/swift-rst-docs) for API usage and an example of a generated Swift documentation.

## Installation

```bash
$ pip install swift-rst-docs
$ brew install sourcekitten
```

## Usage

You need to generate a JSON file with SourceKitten first.
To reference symbols in your documentation, place their full name between 4 backticks. For example: `\`\`MyStructure.hello(world:)\`\`` or `\`\`MySwiftLibrary.MyStructure.hello(world:)\`\`` when referencing from another module or the documentation's overview text. This will create a link to the symbol's page.

```bash
$ sourcekitten doc [--spm] [-- <swift / xcodebuild arguments>] > documentation.json
```

### Command Line

Run `swift-rst-docs` to generate RST files.
You can provide multiple JSON paths to generate documentation for multiple modules.

```bash
$ swift-rst-docs \
--title MySwiftPackage \
--output-path swift-docs \
--documentation-file-path tests/MySwiftPackage/MySwiftLibrary.json \
--documentation-file-path tests/MySwiftPackage/MyOtherSwiftLibrary.json \
[...]
```

This will generate the pages inside the `swift-docs` directory. All the files are placed in the same directory and are named after the unique identifiers ('usr' documentation entry) of the symbols they document.

More options:

```bash
usage: swift-rst-docs [-h] --documentation-file-path DOCUMENTATION_FILE_PATH --output-path OUTPUT_PATH
                      --title TITLE [--overview OVERVIEW] [--files FILES] [--symbols SYMBOLS]
                      [--min-accessibility {public,internal,fileprivate,private,open}]

options:
  -h, --help            show this help message and exit
  --documentation-file-path, -d DOCUMENTATION_FILE_PATH
                        SourceKitten JSON file path.
  --output-path, -o OUTPUT_PATH
                        Output directory path.
  --title, -t TITLE     Index title.
  --overview, -v OVERVIEW
                        Overview file path or contents.
  --files, -f FILES     File names to document. Can be base names or paths relative to any directory in the source
                        code. Defaults to all.
  --symbols, -s SYMBOLS
                        Symbols to document. Defaults to all.
  --min-accessibility, -a {public,internal,fileprivate,private,open}
                        Minimum accessibility of symbols to document. Defaults to public.
```

### API

You can also use the Python API to programatically generate documentation.
See the [documentation](https://gatit.es/emma/cosas/documentaciones/swift-rst-docs) for more info.

Example:

```python
from swift_rst_docs import (
    GenerationContext, fetch_documents, generate_documentation
)
from swift_rst_docs.types import Accessibility

context = GenerationContext(
    index_title="MySwiftPackage",
    overview="Example Sphinx documentation for a Swift Package with two libraries.",
    documented_objects=[
        # Skip MyOtherSwiftLibrary/MyHiddenSymbols.swift
        #
        # The paths are relative to anything: 
        # you can just write the base names but if you do so there is no way disambiguate between modules.
        "MySwiftLibrary/MySwiftLibrary.swift",
        "MyOtherSwiftLibrary/MyOtherSwiftLibrary.swift"
        ],
        min_accessibility=Accessibility.PUBLIC
)

# Fetch symbols and writes them to `context`
for json_path in [
    "MySwiftPackage/MySwiftLibrary.json",
    "MySwiftPackage/MyOtherSwiftLibrary.json",
]:
    path = os.path.join(OUTPUT_PATH, json_path)
    fetch_documents(path, context)

# Write pages
for page in generate_documentation(context):
    with open(os.path.join(OUTPUT_PATH, page.file_name), "w+") as f:
        f.write(page.contents)
```
