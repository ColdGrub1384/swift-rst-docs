CLI Usage
=========

Run ``swift-rst-docs`` to generate RST files.
You can provide multiple JSON paths to generate documentation for multiple modules.

.. code-block:: bash

   $ swift-rst-docs \
   --title MySwiftPackage \
   --output-path swift-docs \
   --documentation-file-path tests/MySwiftPackage/MySwiftLibrary.json \
   --documentation-file-path tests/MySwiftPackage/MyOtherSwiftLibrary.json \
   [...]

This will generate the pages inside the ``swift-docs`` directory. All the files are placed in the same directory and are named after the unique identifiers (``usr`` documentation entry) of the symbols they document.

More options:

.. code-block:: bash

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

