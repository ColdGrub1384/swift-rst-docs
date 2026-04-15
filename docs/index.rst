.. swift-rst-docs documentation master file, created by
   sphinx-quickstart on Wed Apr 15 03:32:14 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

swift-rst-docs
==============

Python library and CLI to generate reStructuredText documentation for Swift projects from `SourceKitten <https://github.com/jpsim/SourceKitten>`_ output files to use with `Sphinx <https://www.sphinx-doc.org>`_ HTML output.

Document
--------

.. toctree::
   :maxdepth: 2
   :caption: Contents

   cli
   reference

.. toctree::
   :maxdepth: 2
   :caption: Example Output

   swift/index


Installation
------------

.. code-block:: bash

   $ pip install swift-rst-docs

API Usage
---------

You need to generate a JSON file with SourceKitten first.
To reference symbols in your documentation, place their full name between 4 backticks. For example: ````MyStructure.hello(world:)\`\``` or ````MySwiftLibrary.MyStructure.hello(world:)```` when referencing from another module or the documentation's overview text. This will create a link to the symbol's page.

.. code-block:: bash

   $ sourcekitten doc [--spm] [-- <swift / xcodebuild arguments>] > documentation.json

API Example
-----------

First, create a :py:class:`swift_rst_docs.types.GenerationContext` object and populate it with your options.
Then call :py:func:`swift_rst_docs.doc.fetch_documents` for each JSON file you want to process.
And finally, call :py:func:`swift_rst_docs.doc.generate_documentation` to generate and return all the documentation RST files.

.. code-block:: python

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

