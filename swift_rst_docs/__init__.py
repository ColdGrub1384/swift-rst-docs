"""
API for generating Swift documentation as restructuredText for HTML output.
"""

from .cli import main
from .highlight import __all__ as _highlight_all
from .types import __all__ as _types_all
from .doc import __all__ as _doc_all
from .highlight import *
from .types import *
from .doc import *


__all__ = [
    "main"
]+_highlight_all+_types_all+_doc_all

del _highlight_all
del _types_all
del _doc_all


if __name__ == "__main__":
    main()
