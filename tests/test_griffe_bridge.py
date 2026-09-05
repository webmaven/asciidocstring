import sys
from unittest.mock import patch

import griffe
import pytest

import asciidocstring
from asciidocstring.griffe_bridge import from_griffe, from_sections, to_asciidoc


def test_from_griffe_google_style() -> None:
    docstring_text = """
    Calculate the sum of two integers.

    Args:
        a (int): The first integer.
        b (int, optional): The second integer. Defaults to 0.

    Returns:
        int: The sum of a and b.

    Raises:
        TypeError: If a or b is not an integer.

    Examples:
        >>> add(1, 2)
        3
    """
    doc = from_griffe(docstring_text, style="google")
    assert isinstance(doc, asciidocstring.AsciiDocStringDocument)
    assert doc.summary == "Calculate the sum of two integers."

    assert len(doc.parameters) == 2
    assert doc.parameters[0].name == "a"
    assert doc.parameters[0].type_name == "int"
    assert doc.parameters[0].description == "The first integer."
    assert doc.parameters[1].optional is True

    assert len(doc.returns) == 1
    assert doc.returns[0].type_name == "int"

    assert len(doc.raises) == 1
    assert doc.raises[0].type_name == "TypeError"

    assert len(doc.examples) == 1
    assert ">>> add(1, 2)" in doc.examples[0].content


def test_from_sections_direct() -> None:
    d = griffe.Docstring("A short description.\n\nArgs:\n    x (str): A string.")
    sections = griffe.parse(d, "google")
    doc = from_sections(sections)
    assert isinstance(doc, asciidocstring.AsciiDocStringDocument)
    assert len(doc.parameters) == 1
    assert doc.parameters[0].name == "x"
    assert doc.parameters[0].type_name == "str"


def test_from_griffe_numpy_style() -> None:
    numpy_doc = """
    Subtract two numbers.

    Parameters
    ----------
    x : int
        First number.

    Yields
    ------
    int
        Difference chunk.

    Receives
    --------
    int
        Reset signal.

    Warns
    -----
    UserWarning
        If deprecated.
    """
    doc = from_griffe(numpy_doc, style="numpy")
    assert len(doc.parameters) == 1
    assert len(doc.yields) == 1
    assert doc.yields[0].type_name == "int"
    assert len(doc.receives) == 1
    assert doc.receives[0].type_name == "int"
    assert len(doc.warns) == 1
    assert doc.warns[0].type_name == "UserWarning"


def test_from_griffe_with_griffe_docstring_instance() -> None:
    raw = "Summary here.\n\nArgs:\n    y (float): Float arg."
    d = griffe.Docstring(raw)
    doc = from_griffe(d, style="google")
    assert doc.summary == "Summary here."
    assert len(doc.parameters) == 1
    assert doc.parameters[0].name == "y"
    assert doc.parameters[0].type_name == "float"


def test_to_asciidoc_and_deprecated() -> None:
    sec_dep = griffe.DocstringSectionDeprecated(version="1.5", text="Use new_fn()")
    adoc = to_asciidoc([sec_dep])
    assert "deprecated" in adoc.lower()
    doc = from_sections([sec_dep])
    assert doc.deprecated is not None
    assert doc.deprecated.version == "1.5"


def test_to_asciidoc_admonition() -> None:
    sec_adm = griffe.DocstringSectionAdmonition(kind="note", text="Important note.")
    adoc = to_asciidoc([sec_adm])
    assert "[NOTE]" in adoc
    assert "Important note." in adoc


def test_to_asciidoc_attributes_and_other_params() -> None:
    attr = griffe.DocstringAttribute(
        name="count", annotation="int", description="Item count.", value="10"
    )
    sec_attr = griffe.DocstringSectionAttributes([attr])
    adoc = to_asciidoc([sec_attr])
    assert "[attributes]" in adoc
    assert "`count`::" in adoc

    param2 = griffe.DocstringParameter(
        name="extra", annotation="str", description="Extra param.", value="'abc'"
    )
    sec_other = griffe.DocstringSectionOtherParameters([param2])
    adoc_other = to_asciidoc([sec_other])
    # kind_value is "other parameters" (with space), mapped to [other_parameters]
    assert "[other_parameters]" in adoc_other
    assert "`extra`::" in adoc_other


def test_from_griffe_missing_import() -> None:
    with patch.dict(sys.modules, {"griffe": None}):
        with pytest.raises(ImportError, match="Griffe is required"):
            from_griffe("Some docstring")


def test_to_asciidoc_examples_string_items() -> None:
    sec_ex = griffe.DocstringSectionExamples(["1 + 1\n2"])  # type: ignore[list-item]
    adoc = to_asciidoc([sec_ex])
    assert "[source,python,test]" in adoc
    assert "1 + 1" in adoc


def test_to_asciidoc_admonition_delimiter() -> None:
    sec_adm = griffe.DocstringSectionAdmonition(kind="warning", text="Be careful.")
    adoc = to_asciidoc([sec_adm])
    assert adoc == "[WARNING]\n====\nBe careful.\n===="


def test_to_asciidoc_empty_sections() -> None:
    sections = [
        griffe.DocstringSectionParameters([]),
        griffe.DocstringSectionOtherParameters([]),
        griffe.DocstringSectionAttributes([]),
        griffe.DocstringSectionReturns([]),
        griffe.DocstringSectionYields([]),
        griffe.DocstringSectionRaises([]),
        griffe.DocstringSectionReceives([]),
        griffe.DocstringSectionWarns([]),
        griffe.DocstringSectionExamples([]),
    ]
    adoc = to_asciidoc(sections)
    assert adoc == ""
def test_griffe_named_returns_and_yields() -> None:
    docstring = """
    Returns:
        total (int): The total computed sum.

    Yields:
        chunk (bytes): The next data chunk.
    """
    doc = from_griffe(docstring, style="google")
    assert len(doc.returns) == 1
    assert doc.returns[0].name == "total"
    assert doc.returns[0].type_name == "int"
    assert doc.returns[0].description == "The total computed sum."

    assert len(doc.yields) == 1
    assert doc.yields[0].name == "chunk"
    assert doc.yields[0].type_name == "bytes"
    assert doc.yields[0].description == "The next data chunk."

