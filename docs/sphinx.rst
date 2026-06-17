Sphinx
======

Besides generating static documents, ``swift-rst-docs`` supports integration with Sphinx as extension.
It automatically generates documents for every symbol, but you control where to index them through the ``swift:module`` directive. There is also a ``swift:symbol`` role for linking documentation pages.

Usage
-----

To generate Swift documentation with Sphinx, ``swift-rst-docs`` still requires SourceKitten JSON documentation files. It looks for them recursively in every ``_api`` directory in the documentation's source directory. ``swift-rst-docs`` temporarily generates the documents there.

The extension must be included in the documentation's configuration file for documents to be automatically generated.

.. code-block:: python

   extensions = ["swift_rst_docs", ...]

The directory API documentations are searched in can be changed through the ``swift_rst_docs.sphinx.API_DIRECTORY_NAME`` variable:

.. code-block:: python

   import swift_rst_docs
   swift_rst_docs.sphinx.API_DIRECTORY_NAME = "_swift_api"

Markup extensions
-----------------

reStructuredText extensions for Swift documentation.

.. raw:: html

   <style>
       .markup-extension-title code.docutils.literal,
       .markup-extension-title code.literal,
       .markup-extension-title span.pre {
           border: none;
           background: none;
           padding: 0;
           border-radius: 0;
           font-size: 1.5rem;
           font-weight: bold;
       }
   </style>

.. container:: markup-extension-title

   ``:swift:symbol:``

References a symbol's documentation page from its full name. The module name can be deduced automatically if there is only one symbol with the same name accross modules.

.. rubric:: Arguments

The full symbol's name, with or without its module name.

.. rubric:: Usage

.. code-block:: rst

   :swift:symbol:`MySwiftLibrary.MyStructure.hello(world:)`

.. container:: markup-extension-title

   ``.. swift:module::``

Writes a toctree listing a module's symbols with their documentation comments.
If the ``:members:`` option is present, all symbols are included, if not, every desired symbol must be included as the contents of the directive.

.. rubric:: Arguments

The documented module name.

.. rubric:: Options

- ``declaration`` If present, includes the module's import statement.
- ``members`` If present, includes all the module's symbols ignoring the directive's content.

.. rubric:: Contents

Optionally, every included symbol.

.. rubric:: Usage

Includes all symbols and the module's import statement:

.. code-block:: rst

   .. swift:module:: MySwiftLibrary
      :members:
      :declaration:

Includes the specified symbols only:

.. code-block:: rst

   .. swift:module:: MySwiftLibrary

      MyStructure
      MyProtocol
      Animal


