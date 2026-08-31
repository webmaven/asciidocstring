"""Tests verifying AsciiDoc docstrings on models.py public dataclasses."""

import inspect

import pytest

import asciidocstring
from asciidocstring.models import (
    DocstringAttribute,
    DocstringDeprecated,
    DocstringExample,
    DocstringParam,
    DocstringRaise,
    DocstringReceive,
    DocstringReturn,
    DocstringWarn,
    DocstringYield,
)

ALL_MODELS = [
    DocstringParam,
    DocstringReturn,
    DocstringYield,
    DocstringRaise,
    DocstringReceive,
    DocstringWarn,
    DocstringAttribute,
    DocstringDeprecated,
    DocstringExample,
]


@pytest.mark.parametrize("model_cls", ALL_MODELS)
def test_model_docstring_format_and_absence_of_google_style(model_cls: type) -> None:
    """Verify each model docstring uses AsciiDoc [attributes] and not Google style."""
    doc = inspect.getdoc(model_cls)
    assert doc is not None, f"Docstring missing for {model_cls.__name__}"
    assert "[attributes]" in doc, (
        f"AsciiDoc '[attributes]' block missing in "
        f"{model_cls.__name__} docstring:\n{doc}"
    )
    assert "Attributes:" not in doc, (
        f"Google-style 'Attributes:' header found in "
        f"{model_cls.__name__} docstring:\n{doc}"
    )

    # Self-parsing verification: ensure attributes are parsed
    parsed = asciidocstring.parse(doc)
    assert len(parsed.attributes) > 0, (
        f"No attributes extracted from {model_cls.__name__} docstring"
    )


def test_docstring_param_docstring() -> None:
    doc = inspect.getdoc(DocstringParam)
    assert doc is not None
    assert "[attributes]" in doc
    assert "`name` (str)::" in doc
    assert "`type_name` (str, optional)::" in doc
    assert "`description` (str)::" in doc
    assert "`default` (str, optional)::" in doc
    assert "`optional` (bool, optional)::" in doc or "`optional` (bool)::" in doc
    assert "`raw_entry` (Any, optional)::" in doc

    parsed = asciidocstring.parse(doc)
    attr_names = [a.name for a in parsed.attributes]
    assert attr_names == [
        "name",
        "type_name",
        "description",
        "default",
        "optional",
        "raw_entry",
    ]


def test_docstring_return_docstring() -> None:
    doc = inspect.getdoc(DocstringReturn)
    assert doc is not None
    assert "[attributes]" in doc
    assert "`type_name` (str, optional)::" in doc
    assert "`description` (str)::" in doc
    assert "`name` (str, optional)::" in doc

    parsed = asciidocstring.parse(doc)
    attr_names = [a.name for a in parsed.attributes]
    assert attr_names == ["type_name", "description", "name"]


def test_docstring_yield_docstring() -> None:
    doc = inspect.getdoc(DocstringYield)
    assert doc is not None
    assert "[attributes]" in doc
    assert "`type_name` (str, optional)::" in doc
    assert "`description` (str)::" in doc
    assert "`name` (str, optional)::" in doc

    parsed = asciidocstring.parse(doc)
    attr_names = [a.name for a in parsed.attributes]
    assert attr_names == ["type_name", "description", "name"]


def test_docstring_raise_docstring() -> None:
    doc = inspect.getdoc(DocstringRaise)
    assert doc is not None
    assert "[attributes]" in doc
    assert "`type_name` (str)::" in doc
    assert "`description` (str)::" in doc

    parsed = asciidocstring.parse(doc)
    attr_names = [a.name for a in parsed.attributes]
    assert attr_names == ["type_name", "description"]


def test_docstring_receive_docstring() -> None:
    doc = inspect.getdoc(DocstringReceive)
    assert doc is not None
    assert "[attributes]" in doc
    assert "`type_name` (str, optional)::" in doc
    assert "`description` (str)::" in doc

    parsed = asciidocstring.parse(doc)
    attr_names = [a.name for a in parsed.attributes]
    assert attr_names == ["type_name", "description"]


def test_docstring_warn_docstring() -> None:
    doc = inspect.getdoc(DocstringWarn)
    assert doc is not None
    assert "[attributes]" in doc
    assert "`type_name` (str, optional)::" in doc
    assert "`description` (str)::" in doc

    parsed = asciidocstring.parse(doc)
    attr_names = [a.name for a in parsed.attributes]
    assert attr_names == ["type_name", "description"]


def test_docstring_attribute_docstring() -> None:
    doc = inspect.getdoc(DocstringAttribute)
    assert doc is not None
    assert "[attributes]" in doc
    assert "`name` (str)::" in doc
    assert "`type_name` (str, optional)::" in doc
    assert "`description` (str)::" in doc
    assert "`value` (str, optional)::" in doc

    parsed = asciidocstring.parse(doc)
    attr_names = [a.name for a in parsed.attributes]
    assert attr_names == ["name", "type_name", "description", "value"]


def test_docstring_deprecated_docstring() -> None:
    doc = inspect.getdoc(DocstringDeprecated)
    assert doc is not None
    assert "[attributes]" in doc
    assert "`version` (str, optional)::" in doc
    assert "`reason` (str)::" in doc

    parsed = asciidocstring.parse(doc)
    attr_names = [a.name for a in parsed.attributes]
    assert attr_names == ["version", "reason"]


def test_docstring_example_docstring() -> None:
    doc = inspect.getdoc(DocstringExample)
    assert doc is not None
    assert "[attributes]" in doc
    assert "`content` (str)::" in doc
    assert "`language` (str, optional)::" in doc
    assert "`line_number` (int, optional)::" in doc
    assert "`is_interactive` (bool, optional)::" in doc
    assert (
        "`attributes` (dict[str, Any], optional)::" in doc
        or "`attributes` (dict, optional)::" in doc
    )

    parsed = asciidocstring.parse(doc)
    attr_names = [a.name for a in parsed.attributes]
    assert attr_names == [
        "content",
        "language",
        "line_number",
        "is_interactive",
        "attributes",
    ]
