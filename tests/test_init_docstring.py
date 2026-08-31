"""Tests verifying AsciiDoc module docstring for asciidocstring."""

import asciidocstring


def test_init_module_docstring_content() -> None:
    doc = asciidocstring.__doc__
    assert doc is not None
    assert "[source,python]" in doc
    assert "----" in doc
    assert "parse(" in doc
    assert "from_griffe(" in doc
    assert "parameters" in doc
    assert "returns" in doc
    assert "raises" in doc
    assert "WASM" in doc or "Pyodide" in doc

    # Verify self-parsing
    parsed = asciidocstring.parse(doc)
    assert parsed.summary
    assert len(parsed.examples) >= 1
    assert "parse(" in parsed.examples[0].content
