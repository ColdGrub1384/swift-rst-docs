# swift-rst-docs

Python library, cli and [Sphinx](https://www.sphinx-doc.org) extension to generate documentation for Swift projects from [SourceKitten](https://github.com/jpsim/SourceKitten) output files.

## Installation

```bash
$ pip install swift-rst-docs
$ brew install sourcekitten
```

## Usage

You need to generate a JSON file with SourceKitten first.
To reference symbols in your documentation, place their full name between 4 backticks. For example: ``` ``MyStructure.hello(world:)`` ``` or ``` ``MySwiftLibrary.MyStructure.hello(world:)`` ``` when referencing from another module or the documentation's overview text. This will create a link to the symbol's page.

```bash
$ sourcekitten doc [--spm] [-- <swift / xcodebuild arguments>] > documentation.json
```

See the [documentation](https://gatit.es/emma/cosas/documentaciones/swift-rst-docs) for the various ways of generating documentation pages and an example of a generated Swift documentation. The example documentation is in the repo's `docs/swift` directory and the SourceKitten documentation files are generated from the `tests/MySwiftPackage/generate-documentation.sh`
