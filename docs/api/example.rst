Example
=======

First, import needed names from ``swift_rst_docs``:

.. code-block:: python

   from swift_rst_docs import (
       GenerationContext,
       Accessibility
       fetch_documents,
       generate_documentation
   )


Then create a :py:class:`swift_rst_docs.types.GenerationContext` object and populate it with your options.

.. code-block:: python

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


And call :py:func:`swift_rst_docs.fetch_documents` for each JSON file you want to process.

.. code-block:: python

   for json_path in [
       "MySwiftPackage/MySwiftLibrary.json",
       "MySwiftPackage/MyOtherSwiftLibrary.json",
   ]:
       path = os.path.join(OUTPUT_PATH, json_path)
       fetch_documents(path, context)


Finally, use :py:func:`swift_rst_docs.generate_documentation` to generate and return all the documentation RST files.

.. code-block:: python

   for page in generate_documentation(context):
       with open(os.path.join(OUTPUT_PATH, page.file_name), "w+") as f:
           f.write(page.contents)

