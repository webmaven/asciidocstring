"""Tests verifying AsciiDoc docstrings on document.py public APIs."""

import inspect

import asciidocstring
from asciidocstring.document import (
    AsciiDocStringDocument,
    AsciiDocStringParseError,
    AsciiDocStringWarning,
    parse,
)


def test_parse_function_docstring() -> None:
    doc = inspect.getdoc(parse)
    assert doc is not None
    assert "[parameters]" in doc
    assert "`docstring` (str)::" in doc
    assert "`safe_mode` (bool, optional)::" in doc
    assert "Defaults to `False`." in doc
    assert "[returns]" in doc
    assert "`AsciiDocStringDocument`::" in doc
    assert "[raises]" in doc
    assert "`AsciiDocStringParseError`::" in doc
    assert "[source,python]" in doc
    assert "----" in doc

    # Verify self-parsing
    parsed = asciidocstring.parse(doc)
    param_names = [p.name for p in parsed.parameters]
    assert param_names == ["docstring", "safe_mode"]
    assert len(parsed.returns) == 1
    assert parsed.returns[0].type_name == "AsciiDocStringDocument"


def test_asciidocstring_parse_error_docstring() -> None:
    doc = inspect.getdoc(AsciiDocStringParseError)
    assert doc is not None
    assert "[attributes]" in doc
    assert "`line` (int, optional)::" in doc
    assert "`column` (int, optional)::" in doc
    assert "`context` (str, optional)::" in doc

    # Verify self-parsing
    parsed = asciidocstring.parse(doc)
    attr_names = [a.name for a in parsed.attributes]
    assert attr_names == ["line", "column", "context"]


def test_asciidocstring_warning_docstring() -> None:
    doc = inspect.getdoc(AsciiDocStringWarning)
    assert doc is not None
    assert len(doc.splitlines()) > 1
    assert "safe_mode" in doc or "safe-mode" in doc


def test_asciidocstring_document_init_docstring() -> None:
    doc = inspect.getdoc(AsciiDocStringDocument.__init__)
    assert doc is not None
    assert "[parameters]" in doc
    assert "`raw_source` (str)::" in doc
    assert "`safe_mode` (bool, optional)::" in doc
    assert "Defaults to `False`." in doc
    assert "[raises]" in doc
    assert "`AsciiDocStringParseError`::" in doc

    # Verify self-parsing
    parsed = asciidocstring.parse(doc)
    param_names = [p.name for p in parsed.parameters]
    assert param_names == ["raw_source", "safe_mode"]
    assert len(parsed.raises) == 1
    assert parsed.raises[0].type_name == "AsciiDocStringParseError"


def test_asciidocstring_document_to_rest_docstring() -> None:
    doc = inspect.getdoc(AsciiDocStringDocument.to_rest)
    assert doc is not None
    assert "[returns]" in doc
    assert "`str`::" in doc
    assert "[source,python]" in doc
    assert "----" in doc

    # Verify self-parsing
    parsed = asciidocstring.parse(doc)
    assert len(parsed.returns) == 1
    assert parsed.returns[0].type_name == "str"


def test_asciidocstring_document_extract_tests_docstring() -> None:
    doc = inspect.getdoc(AsciiDocStringDocument.extract_tests)
    assert doc is not None
    assert "[parameters]" in doc
    assert "`language` (str, optional)::" in doc
    assert "`requires_test_marker` (bool, optional)::" in doc
    assert "[returns]" in doc
    assert "`list[TestBlock]`::" in doc

    # Verify self-parsing
    parsed = asciidocstring.parse(doc)
    param_names = [p.name for p in parsed.parameters]
    assert param_names == ["language", "requires_test_marker"]
    assert len(parsed.returns) == 1
    assert parsed.returns[0].type_name == "list[TestBlock]"


def test_asciidocstring_document_properties_docstrings() -> None:
    properties_expected = {
        "semantics": ("`SemanticExtractorVisitor`::", "SemanticExtractorVisitor"),
        "summary": ("`str`::", "str"),
        "description": ("`str`::", "str"),
        "parameters": ("`list[DocstringParam]`::", "list[DocstringParam]"),
        "returns": ("`list[DocstringReturn]`::", "list[DocstringReturn]"),
        "yields": ("`list[DocstringYield]`::", "list[DocstringYield]"),
        "raises": ("`list[DocstringRaise]`::", "list[DocstringRaise]"),
        "receives": ("`list[DocstringReceive]`::", "list[DocstringReceive]"),
        "warns": ("`list[DocstringWarn]`::", "list[DocstringWarn]"),
        "attributes": ("`list[DocstringAttribute]`::", "list[DocstringAttribute]"),
        "examples": ("`list[DocstringExample]`::", "list[DocstringExample]"),
        "deprecated": ("`DocstringDeprecated | None`::", "DocstringDeprecated | None"),
        "version_added": ("`VersionDoc | None`::", "VersionDoc | None"),
        "version_changed": ("`list[VersionDoc]`::", "list[VersionDoc]"),
        "deprecated_role": ("`DeprecationDoc | None`::", "DeprecationDoc | None"),
        "is_experimental": ("`bool`::", "bool"),
    }

    for prop_name, (expected_term, expected_type) in properties_expected.items():
        prop = getattr(AsciiDocStringDocument, prop_name)
        doc = inspect.getdoc(prop)
        assert doc is not None, f"Docstring missing for property {prop_name}"
        assert "[returns]" in doc, f"[returns] missing in docstring for {prop_name}"
        assert (
            expected_term in doc
        ), f"Expected term '{expected_term}' not in docstring for {prop_name}"

        # Verify self-parsing
        parsed = asciidocstring.parse(doc)
        assert len(parsed.returns) == 1, f"No return parsed for {prop_name}"
        assert parsed.returns[0].type_name == expected_type, (
            f"Return type mismatch for {prop_name}: "
            f"got {parsed.returns[0].type_name}, expected {expected_type}"
        )
