.. swift-rst-docs documentation master file, created by
   sphinx-quickstart on Wed Apr 15 03:32:14 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

swift-rst-docs
==============

Python library, CLI and `Sphinx <https://www.sphinx-doc.org>`_ extension to generate reStructuredText documentation for Swift projects from `SourceKitten <https://github.com/jpsim/SourceKitten>`_ output files.

Document
--------

.. toctree::
   :maxdepth: 2
   :caption: Contents

   cli
   sphinx
   api/index

.. toctree::
   :maxdepth: 2
   :caption: Example Output

   swift/index


Installation
------------

.. code-block:: bash

   $ pip install swift-rst-docs

Usage
-----

You need to generate a JSON file with SourceKitten first for ``swift_rst_docs`` to parse them.

To reference symbols in your documentation strings, place their full name between 4 backticks. For example: ````MyStructure.hello(world:)```` or ````MySwiftLibrary.MyStructure.hello(world:)```` when referencing from another module or the documentation's overview text. This will create a link to the symbol's page.

.. code-block:: bash

   $ sourcekitten doc [--spm] [-- <swift / xcodebuild arguments>] > documentation.json

You can then use either the CLI or the Python API to generate RST documents. This doesn't require the use of the Sphinx extension. 

If you want more control on your module pages and automatic generation from the JSON files, you can use ``sphinx_rst_docs`` as a Sphinx extension.

