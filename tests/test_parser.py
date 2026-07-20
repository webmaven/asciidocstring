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


@pytest.mark.xfail(
    reason="Upstream issue #85: lark_parser silently swallows syntax errors in 0.1.0a9"
)
def test_strict_parsing_errors() -> None:
    # Testing that syntactically invalid input raises descriptive errors
    invalid_syntax = ":: invalid\n"
    with pytest.raises(asciidocstring.AsciiDocStringParseError) as exc_info:
        asciidocstring.parse(invalid_syntax)

    # Check that it raised our custom parse exception with context details
    assert "Parse Error" in str(exc_info.value)
    assert exc_info.value.line == 1
    assert exc_info.value.column == 1


def test_generic_parsing_errors() -> None:
    # Passing an invalid type should raise a generic AsciiDocStringParseError
    with pytest.raises(asciidocstring.AsciiDocStringParseError):
        asciidocstring.parse(None)  # type: ignore


@pytest.mark.xfail(
    reason="Upstream issue #85: lark_parser silently swallows syntax errors in 0.1.0a9"
)
def test_safe_parsing_mode() -> None:
    # Testing that syntactically invalid input with safe_mode=True
    # emits an AsciiDocStringWarning and returns a warning admonition AST
    invalid_syntax = ":: invalid\n"

    with pytest.warns(asciidocstring.AsciiDocStringWarning) as record:
        doc = asciidocstring.parse(invalid_syntax, safe_mode=True)

    # Check that exactly one warning was emitted
    assert len(record) == 1
    assert "Parse Error" in str(record[0].message)

    # Check that a fallback admonition warning block AST was built
    assert doc.ast is not None

    # Check that to_rest() compiles the fallback admonition successfully
    serialized = doc.to_rest()
    assert ".. warning::" in serialized
    assert "Failed to parse AsciiDoc docstring: AsciiDoc Parse Error:" in serialized
    assert ".. code-block:: asciidoc" in serialized
    assert ":: invalid" in serialized
    # Check that visual caret pointer points to first character of ":: invalid"
    assert "^" in serialized


def test_safe_parsing_mode_general_exceptions() -> None:
    # Testing that general Exception with safe_mode=True
    # also emits warning and falls back
    with pytest.warns(asciidocstring.AsciiDocStringWarning) as record:
        doc2 = asciidocstring.parse(None, safe_mode=True)  # type: ignore
    assert len(record) == 1
    assert "Failed to parse" in doc2.to_rest()
