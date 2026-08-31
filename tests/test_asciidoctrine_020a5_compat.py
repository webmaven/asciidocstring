"""Compatibility tests verifying upstream asciidoctrine 0.2.0a3-0.2.0a5 fixes."""

from asciidocstring import parse


def test_mid_identifier_underscore_does_not_create_emphasis() -> None:
    """Issue #97: Mid-identifier underscores should not split into emphasis nodes."""
    doc = parse("""
        Process a batch operation.

        [parameters]
        `batch_size` (int):: The size of each processing batch.
        `error_handler` (Callable, optional):: Custom error handling callback.
    """)
    assert len(doc.parameters) == 2
    assert doc.parameters[0].name == "batch_size"
    assert doc.parameters[0].type_name == "int"
    assert doc.parameters[1].name == "error_handler"
    assert doc.parameters[1].type_name == "Callable"
    assert doc.parameters[1].optional is True


def test_inline_macro_attached_to_punctuation() -> None:
    """Issue #120: Footnote macro attached to punctuation in returns description."""
    doc = parse("""
        Compute a result.

        [parameters]
        `x` (int):: The input value.

        [returns]
        `int`:: The output value.footnote:[Always positive.]
    """)
    assert len(doc.returns) == 1
    assert doc.returns[0].type_name == "int"
    assert "The output value" in doc.returns[0].description


def test_block_title_after_block_attaches_correctly() -> None:
    """Issue #119: Block title preceded by another block attaches correctly."""
    doc = parse("""
        Process data.

        NOTE: This is important.

        .Usage Example
        [source,python]
        ----
        result = process(data)
        ----
    """)
    assert len(doc.examples) == 1
    assert "result = process(data)" in doc.examples[0].content


def test_multiple_inline_code_spans_in_description() -> None:
    """Issue #117: Multiple backtick code spans in parameter descriptions."""
    doc = parse("""
        Connect to a service.

        [parameters]
        `hooks` (list):: List of hook names: `hook_0`, `hook_1`, `hook_2`, `hook_3`.
    """)
    assert len(doc.parameters) == 1
    assert doc.parameters[0].name == "hooks"
    assert "hook_0" in doc.parameters[0].description
    assert "hook_3" in doc.parameters[0].description


def test_memoized_parser_consistent_results() -> None:
    """Memoized parser produces identical results on repeat parses."""
    docstring = """
        Compute area.

        [parameters]
        `width` (float):: Width value.
        `height` (float):: Height value.

        [returns]
        `float`:: The computed area.
    """
    doc1 = parse(docstring)
    doc2 = parse(docstring)
    assert doc1.summary == doc2.summary == "Compute area."
    assert len(doc1.parameters) == len(doc2.parameters) == 2
    assert doc1.parameters[0].name == doc2.parameters[0].name == "width"
    assert doc1.parameters[1].name == doc2.parameters[1].name == "height"
    assert len(doc1.returns) == len(doc2.returns) == 1
    assert doc1.returns[0].type_name == doc2.returns[0].type_name == "float"
