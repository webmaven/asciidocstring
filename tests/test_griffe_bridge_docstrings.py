"""Tests verifying AsciiDoc docstrings on griffe_bridge.py public APIs."""

import inspect

import asciidocstring
from asciidocstring.griffe_bridge import from_griffe, from_sections, to_asciidoc


def test_to_asciidoc_docstring() -> None:
    doc = inspect.getdoc(to_asciidoc)
    assert doc is not None
    assert "[parameters]" in doc
    assert "`sections` (Sequence)::" in doc
    assert "[returns]" in doc
    assert "`str`::" in doc
    assert "[source,python]" in doc
    assert "----" in doc

    # Verify self-parsing
    parsed = asciidocstring.parse(doc)
    param_names = [p.name for p in parsed.parameters]
    assert param_names == ["sections"]
    assert len(parsed.returns) == 1
    assert parsed.returns[0].type_name == "str"
    assert len(parsed.examples) >= 1


def test_from_sections_docstring() -> None:
    doc = inspect.getdoc(from_sections)
    assert doc is not None
    assert "[parameters]" in doc
    assert "`sections` (Sequence)::" in doc
    assert "[returns]" in doc
    assert "`AsciiDocStringDocument`::" in doc
    assert "[source,python]" in doc
    assert "----" in doc

    # Verify self-parsing
    parsed = asciidocstring.parse(doc)
    param_names = [p.name for p in parsed.parameters]
    assert param_names == ["sections"]
    assert len(parsed.returns) == 1
    assert parsed.returns[0].type_name == "AsciiDocStringDocument"
    assert len(parsed.examples) >= 1


def test_from_griffe_docstring() -> None:
    doc = inspect.getdoc(from_griffe)
    assert doc is not None
    assert "[parameters]" in doc
    assert "`docstring` (griffe.Docstring | str)::" in doc
    assert "`style` (str, optional)::" in doc
    assert 'Defaults to `"auto"`.' in doc
    assert "[returns]" in doc
    assert "`AsciiDocStringDocument`::" in doc
    assert "[raises]" in doc
    assert "`ImportError`::" in doc
    assert "[source,python]" in doc
    assert "----" in doc

    # Verify self-parsing
    parsed = asciidocstring.parse(doc)
    param_names = [p.name for p in parsed.parameters]
    assert param_names == ["docstring", "style"]
    assert parsed.parameters[1].optional is True
    assert parsed.parameters[1].default == "auto"
    assert len(parsed.returns) == 1
    assert parsed.returns[0].type_name == "AsciiDocStringDocument"
    assert len(parsed.raises) == 1
    assert parsed.raises[0].type_name == "ImportError"
    assert len(parsed.examples) >= 1
