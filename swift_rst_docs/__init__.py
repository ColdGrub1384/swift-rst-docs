"""
API for generating Swift documentation as restructuredText for HTML output.
"""

from .cli import main
from .highlight import __all__ as _highlight_all
from .types import __all__ as _types_all
from .doc import __all__ as _doc_all
from .sphinx import setup
from .highlight import *
from . import sphinx
from .types import *
from .doc import *

__all__ = [
    "main",
    "setup",
    "sphinx"
]+_highlight_all+_types_all+_doc_all

del _highlight_all
del _types_all
del _doc_all


if __name__ == "__main__":
    main()
