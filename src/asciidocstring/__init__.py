"""
`asciidocstring` is a pure-Python, WASM/Pyodide-compatible library for parsing
and processing Python docstrings written in AsciiDoc.
"""

from .document import AsciiDocStringDocument, parse
from .visitors import TestBlock

__version__ = "0.1.0a2"
__all__ = ["parse", "AsciiDocStringDocument", "TestBlock"]
