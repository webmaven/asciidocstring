import pytest
import asciidocstring
from asciidocstring.document import AsciiDocStringDocument

def test_indentation_stripping() -> None:
    # A standard raw indented docstring
    raw_docstring = """
        = Sample Docstring
        
        This is a paragraph under the docstring.
        It should have common indentation stripped.
        """
    doc = asciidocstring.parse(raw_docstring)
    assert isinstance(doc, AsciiDocStringDocument)
    # The clean source should be normalized without common leading whitespace
    assert doc.clean_source == "= Sample Docstring\n\nThis is a paragraph under the docstring.\nIt should have common indentation stripped.\n"

def test_unexpected_eof_prevention() -> None:
    # Under the hood, lark will fail on string ends without a trailing newline
    # asciidocstring should ensure a trailing newline is appended
    no_newline = "== Section Header"
    doc = asciidocstring.parse(no_newline)
    assert doc.clean_source == "== Section Header\n"
    assert doc.ast is not None

def test_strict_parsing_errors() -> None:
    # Testing that syntactically invalid input raises descriptive errors
    invalid_syntax = ":: invalid\n"
    with pytest.raises(Exception) as exc_info:
         asciidocstring.parse(invalid_syntax)
    # Check that it raised our custom parse exception with context details
    assert "Parse Error" in str(exc_info.value)

