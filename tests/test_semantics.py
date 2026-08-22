import asciidocstring


def test_parse_semantic_sections_attributes() -> None:
    docstring = """
    Compute the Fibonacci sequence.

    [parameters]
    `n`:: (`int`) The index to compute.
    `prefix`:: (`str`, optional) Result prefix. Defaults to "fib:".

    [returns]
    `int`:: The nth Fibonacci number.

    [raises]
    `ValueError`:: If n is negative.
    """
    doc = asciidocstring.parse(docstring)

    assert doc.summary == "Compute the Fibonacci sequence."
    assert len(doc.parameters) == 2
    assert doc.parameters[0].name == "n"
    assert doc.parameters[0].type_name == "int"
    assert doc.parameters[1].optional is True
    assert doc.parameters[1].default == "fib:"

    assert len(doc.returns) == 1
    assert doc.returns[0].type_name == "int"

    assert len(doc.raises) == 1
    assert doc.raises[0].type_name == "ValueError"


def test_parse_semantic_sections_headings() -> None:
    docstring = """
    Perform data sync.

    == Parameters
    `endpoint`:: (`str`) Target sync URL.

    == Yields
    `dict`:: Progress report packets.

    == Receives
    `int`:: Control signal.

    == Warns
    `UserWarning`:: If timeout occurs.

    == Attributes
    `cache`:: (`dict`) Active connections.

    == Deprecated
    Deprecated in version 2.0: Use `v2.sync` instead.
    """
    doc = asciidocstring.parse(docstring)

    assert len(doc.parameters) == 1
    assert doc.parameters[0].name == "endpoint"

    assert len(doc.yields) == 1
    assert doc.yields[0].type_name == "dict"

    assert len(doc.receives) == 1
    assert doc.receives[0].type_name == "int"

    assert len(doc.warns) == 1
    assert doc.warns[0].type_name == "UserWarning"

    assert len(doc.attributes) == 1
    assert doc.attributes[0].name == "cache"

    assert doc.deprecated is not None
    assert doc.deprecated.version == "2.0"


def test_parse_semantic_sections_titles() -> None:
    docstring = """
    Evaluate expression.

    .Parameters
    `expr`:: (`str`) Expression to evaluate.

    .Returns
    `Any`:: Evaluated output.
    """
    doc = asciidocstring.parse(docstring)
    assert len(doc.parameters) == 1
    assert doc.parameters[0].name == "expr"
    assert len(doc.returns) == 1
    assert doc.returns[0].type_name == "Any"


def test_parse_semantic_examples() -> None:
    docstring = """
    Demonstrate calculator operations.

    [source,python]
    ----
    >>> calc = Calculator()
    >>> calc.add(2, 3)
    5
    ----

    [source,python]
    ----
    calc = Calculator()
    res = calc.multiply(4, 5)
    ----
    """
    doc = asciidocstring.parse(docstring)
    assert len(doc.examples) == 2
    assert doc.examples[0].is_interactive is True
    assert ">>> calc.add(2, 3)" in doc.examples[0].content
    assert doc.examples[1].is_interactive is False
    assert "calc.multiply(4, 5)" in doc.examples[1].content


def test_parse_leading_summary_and_description() -> None:
    docstring = """
    Short summary line.

    Second paragraph with more details.

    Third paragraph before parameters.

    [parameters]
    `x`:: (`int`) Input number.
    """
    doc = asciidocstring.parse(docstring)
    assert doc.summary == "Short summary line."
    assert (
        doc.description
        == "Short summary line.\n\n"
        "Second paragraph with more details.\n\n"
        "Third paragraph before parameters."
    )
    assert len(doc.parameters) == 1


def test_parse_semantic_aliases_and_open_blocks() -> None:
    docstring = """
    Testing aliases and open blocks.

    [args]
    `a`:: (`int`) Arg a. default is 42.

    [exceptions]
    `KeyError`:: When key missing.

    [warnings]
    `DeprecationWarning`:: When old method used.

    [deprecated]
    ~~~~
    Deprecated in version 3.1.0: Use new method.
    ~~~~
    """
    doc = asciidocstring.parse(docstring)
    assert len(doc.parameters) == 1
    assert doc.parameters[0].name == "a"
    assert doc.parameters[0].default == "42"
    assert len(doc.raises) == 1
    assert doc.raises[0].type_name == "KeyError"
    assert len(doc.warns) == 1
    assert doc.warns[0].type_name == "DeprecationWarning"
    assert doc.deprecated is not None
    assert doc.deprecated.version == "3.1.0"


def test_parse_deprecated_paragraph() -> None:
    docstring = """
    Testing deprecated paragraph.

    [deprecated]
    Deprecated in version 1.0.0: Legacy function.
    """
    doc = asciidocstring.parse(docstring)
    assert doc.deprecated is not None
    assert doc.deprecated.version == "1.0.0"


def test_parse_empty_and_generic_blocks() -> None:
    docstring = ""
    doc = asciidocstring.parse(docstring)
    assert doc.summary == ""
    assert doc.description == ""
    assert len(doc.parameters) == 0

    docstring2 = """
    Simple docstring.

    Normal term:: Normal definition without semantic role.
    """
    doc2 = asciidocstring.parse(docstring2)
    assert doc2.summary == "Simple docstring."
    assert len(doc2.parameters) == 0


def test_parse_semantic_example_and_open_and_admonition_blocks() -> None:
    docstring = """
    Example with various blocks.

    [example]
    ====
    print("Example block")
    ====

    [parameters]
    ~~~~
    `x`:: (`int`) Param x in open block.
    ~~~~

    [NOTE]
    ====
    This is a note admonition.
    ====

    [deprecated]
    ====
    Deprecated in version 1.2: Admonition deprecation.
    ====
    """
    doc = asciidocstring.parse(docstring)
    assert len(doc.parameters) == 1
    assert doc.parameters[0].name == "x"
    assert doc.deprecated is not None
    assert doc.deprecated.version == "1.2"


def test_parse_node_text_and_admonition_edge_cases() -> None:
    from asciidoctrine.nodes import Admonition

    from asciidocstring.semantics import SemanticExtractorVisitor

    visitor = SemanticExtractorVisitor()
    assert visitor._get_node_text(object()) == ""

    # Test node with terms
    term_node_a = type("MockTerm", (), {"value": "term_a"})()
    term_node_b = type("MockTerm", (), {"value": "term_b"})()
    mock_terms_node = type(
        "MockTermsNode", (), {"terms": [term_node_a, term_node_b]}
    )()
    assert visitor._get_node_text(mock_terms_node) == "term_aterm_b"

    # Test visit_admonition with deprecated role
    mock_adm = Admonition(
        variant="deprecated",
        blocks=[
            type("MockBlock", (), {"value": "Deprecated in version 1.0: Old"})()
        ],
    )
    visitor.visit_admonition(mock_adm)
    assert visitor.deprecated is not None
    assert visitor.deprecated.version == "1.0"


def test_param_default_values_parsing() -> None:
    docstring = """
    Test default parsing.

    [parameters]
    `pi_val`:: (`float`, optional) Circle constant. Defaults to 3.14.
    `named_const`:: (`float`, optional) Math constant. Defaults to math.pi.
    `version_str`:: (`str`, optional) Version string. Defaults to "1.0.0".
    `quoted_dotted`:: (`str`, optional) Module ref. Defaults to `pkg.mod`.
    """
    doc = asciidocstring.parse(docstring)
    assert len(doc.parameters) == 4
    assert doc.parameters[0].name == "pi_val"
    assert doc.parameters[0].default == "3.14"

    assert doc.parameters[1].name == "named_const"
    assert doc.parameters[1].default == "math.pi"

    assert doc.parameters[2].name == "version_str"
    assert doc.parameters[2].default == "1.0.0"

    assert doc.parameters[3].name == "quoted_dotted"
    assert doc.parameters[3].default == "pkg.mod"


def test_deprecated_version_trailing_punctuation() -> None:
    docstring1 = """
    Test deprecation trailing period.

    [deprecated]
    Deprecated in version 2.0.
    """
    doc1 = asciidocstring.parse(docstring1)
    assert doc1.deprecated is not None
    assert doc1.deprecated.version == "2.0"

    docstring2 = """
    Test deprecation trailing colon.

    [deprecated]
    Deprecated in version 3.1.0: Use new_api instead.
    """
    doc2 = asciidocstring.parse(docstring2)
    assert doc2.deprecated is not None
    assert doc2.deprecated.version == "3.1.0"

