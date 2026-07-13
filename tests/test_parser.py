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
    expected = (
        "= Sample Docstring\n\n"
        "This is a paragraph under the docstring.\n"
        "It should have common indentation stripped."
    )
    assert doc.clean_source == expected

def test_unexpected_eof_safety() -> None:
    # Verify that input without a trailing newline parses cleanly and safely
    no_newline = "== Section Header"
    doc = asciidocstring.parse(no_newline)
    assert doc.clean_source == "== Section Header"
    assert doc.ast is not None

def test_strict_parsing_errors() -> None:
    # Testing that syntactically invalid input raises descriptive errors
    invalid_syntax = ":: invalid\n"
    with pytest.raises(Exception) as exc_info:
         asciidocstring.parse(invalid_syntax)
    # Check that it raised our custom parse exception with context details
    assert "Parse Error" in str(exc_info.value)

