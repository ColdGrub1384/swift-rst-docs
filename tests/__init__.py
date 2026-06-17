from swift_rst_docs import GenerationContext, fetch_documents, generate_documentation
from swift_rst_docs.types import Accessibility, DeclarationKind
from swift_rst_docs.doc import Page, replace_links
from swift_rst_docs.highlight import prettify_swift_declaration
import unittest
import os


DIR_NAME = os.path.dirname(__file__)
OUTPUT_PATH = os.path.join(DIR_NAME, "..", "docs", "swift", "_api")


os.makedirs(OUTPUT_PATH, exist_ok=True)


class TestDocumentation(unittest.TestCase):

    context: GenerationContext = None
    pages: list[Page] = None

    def fetch(self):
        self.context = GenerationContext(
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
            "MySwiftLibrary.json",
            "MyOtherSwiftLibrary.json",
        ]:
            path = os.path.join(OUTPUT_PATH, json_path)
            fetch_documents(path, self.context)

        self.pages = generate_documentation(self.context)
        for page in self.pages:
            with open(os.path.join(OUTPUT_PATH, page.file_name), "w+") as f:
                f.write(page.contents)

    def __init__(self, *args, **kwargs):
        self.fetch()
        super().__init__(*args, **kwargs)

    def test_generation(self):
        self.assertEqual(set(map(lambda p: p.file_name, self.pages)), {
            "MyOtherSwiftLibrary.rst",
            "MySwiftLibrary.rst",
            "index.rst",
            "s_14MySwiftLibrary0A8ProtocolP.rst",
            "s_14MySwiftLibrary0A8ProtocolP3foo3barS2S_tF.rst",
            "s_14MySwiftLibrary0A9StructureV.rst",
            "s_14MySwiftLibrary0A9StructureV5hello5worldS2S_tF.rst",
            "s_14MySwiftLibrary6AnimalO.rst",
            "s_14MySwiftLibrary6AnimalO3catyA2CmF.rst",
            "s_14MySwiftLibrary6AnimalO3dogyA2CmF.rst",
            "s_14MySwiftLibrary6AnimalO4nameSSvp.rst",
            "s_14MySwiftLibrary6AnimalO5humanyA2CmF.rst",
            "s_14MySwiftLibrary6AnimalO5snakeyA2CmF.rst",
            "s_19MyOtherSwiftLibrary5Hello6animalSS0acD06AnimalO_tF.rst"
        })

    def test_find_symbol(self):
        symbol_name = "MySwiftLibrary.MyStructure.hello(world:)"
        usr = self.context.find(symbol_name, None)
        self.assertIsNotNone(usr)
        self.assertEqual(usr, "s:14MySwiftLibrary0A9StructureV5hello5worldS2S_tF")

    def test_find_symbol_with_module(self):
        symbol_name = "MyStructure.hello(world:)"
        usr = self.context.find(symbol_name, "MySwiftLibrary")
        self.assertIsNotNone(usr)
        self.assertEqual(usr, "s:14MySwiftLibrary0A9StructureV5hello5worldS2S_tF")

    def test_links(self):
        text = """
Link to ``MyStructure.hello(world:)``.
"""
        text = replace_links(text, "MySwiftLibrary", self.context)
        self.assertEqual(text, """
Link to :ref:`s_14MySwiftLibrary0A9StructureV5hello5worldS2S_tF`.
""")

        text = """
Link to ``MySwiftLibrary.MyStructure.hello(world:)``.
"""
        text = replace_links(text, None, self.context)
        self.assertEqual(text, """
Link to :ref:`s_14MySwiftLibrary0A9StructureV5hello5worldS2S_tF`.
""")

    def test_fullnames(self):
        self.assertEqual(list(self.context.fullnames.keys()), [
            'MySwiftLibrary.Animal',
            'MySwiftLibrary.Animal.cat',
            'MySwiftLibrary.Animal.dog',
            'MySwiftLibrary.Animal.snake',
            'MySwiftLibrary.Animal.human',
            'MySwiftLibrary.Animal.name',
            'MySwiftLibrary.MyProtocol',
            'MySwiftLibrary.MyProtocol.foo(bar:)',
            'MySwiftLibrary.MyStructure',
            'MySwiftLibrary.MyStructure.hello(world:)', 
            'MySwiftLibrary.MyStructure.foo(bar:)',
            'MyOtherSwiftLibrary.Hello(animal:)'
        ])

    def test_prettify(self):
        decls = [
            'public enum Animal',
            'var name: String { get }',
            'public protocol MyProtocol',
            'func foo(bar: String) -> String',
            'public struct MyStructure : MyProtocol',
            'public func hello(world: String) -> String',
            'public func foo(bar: String) -> String',
            'public func Hello(animal: Animal) -> String',
        ]
        prettified = [
            'public enum Animal',
            'var name: String { get }',
            'public protocol MyProtocol',
            'func foo(\n    bar: String\n) -> String',
            'public struct MyStructure: MyProtocol',
            'public func hello(\n    world: String\n) -> String',
            'public func foo(\n    bar: String\n) -> String',
            'public func Hello(\n    animal: Animal\n) -> String',
        ]

        i = 0
        for decl in decls:
            self.assertEqual(prettify_swift_declaration(decl), prettified[i])
            i += 1
