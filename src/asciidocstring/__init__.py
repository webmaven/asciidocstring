"""AsciiDoc docstring parser and toolchain for Python.

`asciidocstring` is a pure-Python, WASM/Pyodide-compatible library for parsing,
querying, and transforming Python docstrings written in AsciiDoc syntax into
strongly typed semantic metadata, Sphinx-compatible reST, or test blocks.

[source,python]
----
import asciidocstring

docstring = '''
Compute the area of a rectangle.

[parameters]
`width` (float):: The width of the rectangle.
`height` (float):: The height of the rectangle.

[returns]
`float`:: The calculated area.

[raises]
`ValueError`:: If width or height is negative.
'''

doc = asciidocstring.parse(docstring)
for param in doc.parameters:
    print(f"{param.name}: {param.type_name}")

for ret in doc.returns:
    print(f"Returns: {ret.type_name}")

for exc in doc.raises:
    print(f"Raises: {exc.type_name}")

# Ingest docstrings from Google/NumPy formats via Griffe
doc_from_griffe = asciidocstring.from_griffe(
    "Args:\\n    x (int): Value\\n", style="google"
)
----

NOTE: `asciidocstring` requires zero native C-extensions and is fully portable
to WebAssembly (WASM) and Pyodide runtimes.
"""

from .document import (
    AsciiDocStringDocument,
    AsciiDocStringParseError,
    AsciiDocStringWarning,
    parse,
)
from .griffe_bridge import from_griffe, from_sections, to_asciidoc
from .models import (
    DeprecationDoc,
    DocstringAttribute,
    DocstringDeprecated,
    DocstringExample,
    DocstringParam,
    DocstringRaise,
    DocstringReceive,
    DocstringReturn,
    DocstringWarn,
    DocstringYield,
    TestBlock,
    VersionDoc,
)

__version__ = "0.1.0a9"
__all__ = [
    "parse",
    "AsciiDocStringDocument",
    "AsciiDocStringParseError",
    "AsciiDocStringWarning",
    "TestBlock",
    "DocstringAttribute",
    "DocstringDeprecated",
    "DocstringExample",
    "DocstringParam",
    "DocstringRaise",
    "DocstringReceive",
    "DocstringReturn",
    "DocstringWarn",
    "DocstringYield",
    "VersionDoc",
    "DeprecationDoc",
    "from_griffe",
    "from_sections",
    "to_asciidoc",
]
