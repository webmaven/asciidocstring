"""Tests verifying AsciiDoc docstrings on visitors.py and semantics.py APIs."""

import inspect

import asciidocstring
from asciidocstring.semantics import SemanticExtractorVisitor
from asciidocstring.visitors import ReSTSerializerVisitor, TestBlockExtractorVisitor

TestBlockExtractorVisitor.__test__ = False



def test_test_block_extractor_init_docstring() -> None:
    doc = inspect.getdoc(TestBlockExtractorVisitor.__init__)
    assert doc is not None
    assert "[parameters]" in doc
    assert "`target_language` (str)::" in doc
    assert "`requires_test_marker` (bool)::" in doc

    # Verify self-parsing
    parsed = asciidocstring.parse(doc)
    param_names = [p.name for p in parsed.parameters]
    assert param_names == ["target_language", "requires_test_marker"]


def test_test_block_extractor_extract_docstring() -> None:
    doc = inspect.getdoc(TestBlockExtractorVisitor.extract)
    assert doc is not None
    assert "[parameters]" in doc
    assert "`node` (Any)::" in doc
    assert "[returns]" in doc
    assert "`list[TestBlock]`::" in doc or "`List[TestBlock]`::" in doc

    # Verify self-parsing
    parsed = asciidocstring.parse(doc)
    param_names = [p.name for p in parsed.parameters]
    assert param_names == ["node"]
    assert len(parsed.returns) == 1
    assert parsed.returns[0].type_name in ("list[TestBlock]", "List[TestBlock]")


def test_rest_serializer_serialize_docstring() -> None:
    doc = inspect.getdoc(ReSTSerializerVisitor.serialize)
    assert doc is not None
    assert "[parameters]" in doc
    assert "`node` (Any)::" in doc
    assert "[returns]" in doc
    assert "`str`::" in doc
    assert "[source,python]" in doc
    assert "----" in doc

    # Verify self-parsing
    parsed = asciidocstring.parse(doc)
    param_names = [p.name for p in parsed.parameters]
    assert param_names == ["node"]
    assert len(parsed.returns) == 1
    assert parsed.returns[0].type_name == "str"
    assert len(parsed.examples) >= 1


def test_rest_serializer_render_inline_docstring() -> None:
    doc = inspect.getdoc(ReSTSerializerVisitor.render_inline)
    assert doc is not None
    assert "[parameters]" in doc
    assert "`node` (Any)::" in doc
    assert "[returns]" in doc
    assert "`str`::" in doc

    # Verify self-parsing
    parsed = asciidocstring.parse(doc)
    param_names = [p.name for p in parsed.parameters]
    assert param_names == ["node"]
    assert len(parsed.returns) == 1
    assert parsed.returns[0].type_name == "str"


def test_semantic_extractor_class_docstring() -> None:
    doc = inspect.getdoc(SemanticExtractorVisitor)
    assert doc is not None
    assert len(doc.splitlines()) > 3
    assert "[attributes]" in doc
    assert "`summary` (str)::" in doc
    assert "`parameters` (list[DocstringParam])::" in doc
    assert "`returns` (list[DocstringReturn])::" in doc
    assert "`examples` (list[DocstringExample])::" in doc
    assert "[source,python]" in doc

    # Verify self-parsing
    parsed = asciidocstring.parse(doc)
    attr_names = [a.name for a in parsed.attributes]
    assert "summary" in attr_names
    assert "description" in attr_names
    assert "parameters" in attr_names
    assert "returns" in attr_names
    assert "yields" in attr_names
    assert "raises" in attr_names
    assert "receives" in attr_names
    assert "warns" in attr_names
    assert "attributes" in attr_names
    assert "examples" in attr_names
    assert "deprecated" in attr_names
    assert len(parsed.examples) >= 1


def test_semantic_extractor_extract_docstring() -> None:
    doc = inspect.getdoc(SemanticExtractorVisitor.extract)
    assert doc is not None
    assert "[parameters]" in doc
    assert "`ast` (Any)::" in doc
    assert "[returns]" in doc
    assert "`SemanticExtractorVisitor`::" in doc
    assert "[source,python]" in doc
    assert "----" in doc

    # Verify self-parsing
    parsed = asciidocstring.parse(doc)
    param_names = [p.name for p in parsed.parameters]
    assert param_names == ["ast"]
    assert len(parsed.returns) == 1
    assert parsed.returns[0].type_name == "SemanticExtractorVisitor"
    assert len(parsed.examples) >= 1
