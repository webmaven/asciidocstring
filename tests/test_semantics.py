import asciidocstring
from asciidocstring import parse
from asciidocstring.semantics import _split_types


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


def test_lhs_and_rhs_parameter_type_parsing() -> None:
    docstring = """
    Comprehensive parameter term and type parsing.

    [parameters]
    `x1` (float):: Description for x1
    `x2` (float, optional):: Description for x2. Defaults to `0.0`.
    name (type):: Description for name
    name_opt (type, optional):: Description for name_opt
    `x`:: (`int`) Description for x.
    `y`:: (`int`, optional) Description for y.
    `z` (optional):: Description for z.
    """
    doc = asciidocstring.parse(docstring)
    params = {p.name: p for p in doc.parameters}

    assert len(doc.parameters) == 7

    # LHS typed parameter `x1` (float)
    assert "x1" in params
    assert params["x1"].name == "x1"
    assert params["x1"].type_name == "float"
    assert params["x1"].optional is False
    assert params["x1"].description == "Description for x1"

    # LHS typed and optional `x2` (float, optional) with default
    assert "x2" in params
    assert params["x2"].name == "x2"
    assert params["x2"].type_name == "float"
    assert params["x2"].optional is True
    assert params["x2"].default == "0.0"

    # Unquoted LHS name (type)
    assert "name" in params
    assert params["name"].name == "name"
    assert params["name"].type_name == "type"
    assert params["name"].optional is False
    assert params["name"].description == "Description for name"

    # Unquoted LHS name_opt (type, optional)
    assert "name_opt" in params
    assert params["name_opt"].name == "name_opt"
    assert params["name_opt"].type_name == "type"
    assert params["name_opt"].optional is True

    # RHS typed `x`:: (`int`) Description for x.
    assert "x" in params
    assert params["x"].name == "x"
    assert params["x"].type_name == "int"
    assert params["x"].optional is False
    assert params["x"].description == "Description for x."

    # RHS typed and optional `y`:: (`int`, optional) Description for y.
    assert "y" in params
    assert params["y"].name == "y"
    assert params["y"].type_name == "int"
    assert params["y"].optional is True
    assert params["y"].description == "Description for y."

    # LHS optional only `z` (optional)
    assert "z" in params
    assert params["z"].name == "z"
    assert params["z"].type_name is None
    assert params["z"].optional is True


def test_default_value_syntax_variations() -> None:
    docstring = """
    Test various default syntax conventions.

    [parameters]
    `a`:: (`int`) Alpha. Defaults to 10.
    `b`:: (`int`) Beta. default is 20.
    `c`:: (`int`) Gamma. default=30.
    `d`:: (`int`) Delta. default = 40.
    `e`:: (`int`) Epsilon. defaults: 50.
    `f`:: (`int`) Zeta. default: 60.
    `g`:: (`int`) Eta. defaults = 70.
    `h`:: (`str`) Theta. defaults: "hello".
    """
    doc = asciidocstring.parse(docstring)
    params = {p.name: p for p in doc.parameters}

    assert params["a"].default == "10"
    assert params["a"].optional is True

    assert params["b"].default == "20"
    assert params["b"].optional is True

    assert params["c"].default == "30"
    assert params["c"].optional is True

    assert params["d"].default == "40"
    assert params["d"].optional is True

    assert params["e"].default == "50"
    assert params["e"].optional is True

    assert params["f"].default == "60"
    assert params["f"].optional is True

    assert params["g"].default == "70"
    assert params["g"].optional is True

    assert params["h"].default == "hello"
    assert params["h"].optional is True


def test_attribute_term_and_value_parsing() -> None:
    docstring = """
    Test attribute parsing.

    [attributes]
    `MAX_RETRIES` (int):: Maximum retry attempts. Defaults to 3.
    `TIMEOUT`:: (`float`, optional) Socket timeout. default=5.0.
    `DEBUG` (bool):: Debug mode flag. default is False.
    """
    doc = asciidocstring.parse(docstring)
    attrs = {a.name: a for a in doc.attributes}

    assert len(doc.attributes) == 3

    assert "MAX_RETRIES" in attrs
    assert attrs["MAX_RETRIES"].name == "MAX_RETRIES"
    assert attrs["MAX_RETRIES"].type_name == "int"
    assert attrs["MAX_RETRIES"].value == "3"

    assert "TIMEOUT" in attrs
    assert attrs["TIMEOUT"].name == "TIMEOUT"
    assert attrs["TIMEOUT"].type_name == "float"
    assert attrs["TIMEOUT"].value == "5.0"

    assert "DEBUG" in attrs
    assert attrs["DEBUG"].name == "DEBUG"
    assert attrs["DEBUG"].type_name == "bool"
    assert attrs["DEBUG"].value == "False"


def test_multi_type_parameter_preservation() -> None:
    doc = parse("""
        A sample function.

        [parameters]
        `val` (int, str, optional):: Input value.
        `config` (dict, list):: Configuration container.
    """)
    assert len(doc.parameters) == 2
    assert doc.parameters[0].name == "val"
    assert doc.parameters[0].type_name == "int | str"
    assert doc.parameters[0].optional is True
    assert doc.parameters[0].raw_entry is not None

    assert doc.parameters[1].name == "config"
    assert doc.parameters[1].type_name == "dict | list"
    assert doc.parameters[1].optional is False


def test_named_returns_and_yields_preservation() -> None:
    doc = parse("""
        A generator function.

        [returns]
        `status` (bool):: Whether operation succeeded.
        `int`:: Anonymous integer return.

        [yields]
        `chunk` (bytes):: Stream chunk data.
        `str`:: Anonymous string yield.
    """)
    assert len(doc.returns) == 2
    assert doc.returns[0].name == "status"
    assert doc.returns[0].type_name == "bool"
    assert doc.returns[0].description == "Whether operation succeeded."
    assert doc.returns[0].raw_entry is not None

    assert doc.returns[1].name is None
    assert doc.returns[1].type_name == "int"
    assert doc.returns[1].description == "Anonymous integer return."

    assert len(doc.yields) == 2
    assert doc.yields[0].name == "chunk"
    assert doc.yields[0].type_name == "bytes"
    assert doc.yields[0].description == "Stream chunk data."
    assert doc.yields[0].raw_entry is not None

    assert doc.yields[1].name is None
    assert doc.yields[1].type_name == "str"


def test_rhs_named_returns_yields_and_multi_type_parameters() -> None:
    doc = parse("""
        A generator function with RHS types.

        [parameters]
        `val`:: (int, str, optional) Input value.

        [returns]
        `status`:: (bool) Whether operation succeeded.

        [yields]
        `chunk`:: (bytes) Stream chunk data.
    """)
    assert len(doc.parameters) == 1
    assert doc.parameters[0].name == "val"
    assert doc.parameters[0].type_name == "int | str"
    assert doc.parameters[0].optional is True
    assert doc.parameters[0].raw_entry is not None

    assert len(doc.returns) == 1
    assert doc.returns[0].name == "status"
    assert doc.returns[0].type_name == "bool"
    assert doc.returns[0].description == "Whether operation succeeded."
    assert doc.returns[0].raw_entry is not None

    assert len(doc.yields) == 1
    assert doc.yields[0].name == "chunk"
    assert doc.yields[0].type_name == "bytes"
    assert doc.yields[0].description == "Stream chunk data."
    assert doc.yields[0].raw_entry is not None


def test_raises_and_attributes_raw_entry_preservation() -> None:
    doc = parse("""
        A function with raises and attributes.

        [raises]
        `ValueError`:: If something goes wrong.

        [attributes]
        `attr` (str):: An attribute.
    """)
    assert len(doc.raises) == 1
    assert doc.raises[0].type_name == "ValueError"
    assert doc.raises[0].raw_entry is not None

    assert len(doc.attributes) == 1
    assert doc.attributes[0].name == "attr"
    assert doc.attributes[0].raw_entry is not None


def test_generic_type_parameter_comma_handling() -> None:
    """Bracket-aware comma split must not corrupt generic type arguments."""
    doc = parse("""
        A function.

        [parameters]
        `mapping` (dict[str, int], optional):: A mapping.
        `value` (Union[int, list[str]], float):: A value.
        `rhs_generic`:: (dict[str, list[int]], optional) A mapping in description.
    """)
    assert len(doc.parameters) == 3

    assert doc.parameters[0].name == "mapping"
    assert doc.parameters[0].type_name == "dict[str, int]"
    assert doc.parameters[0].optional is True

    assert doc.parameters[1].name == "value"
    assert doc.parameters[1].type_name == "Union[int, list[str]] | float"
    assert doc.parameters[1].optional is False

    assert doc.parameters[2].name == "rhs_generic"
    assert doc.parameters[2].type_name == "dict[str, list[int]]"
    assert doc.parameters[2].optional is True


def test_split_types_helper() -> None:
    """_split_types respects brackets, braces, parens and whitespace."""
    assert _split_types("") == []
    assert _split_types("   ") == []
    assert _split_types(" , ") == []
    assert _split_types("int") == ["int"]
    assert _split_types("int, str") == ["int", "str"]
    assert _split_types("dict[str, int], list[tuple[int, str]]") == [
        "dict[str, int]",
        "list[tuple[int, str]]",
    ]
    assert _split_types("Callable((int, int), str), dict{str, int}") == [
        "Callable((int, int), str)",
        "dict{str, int}",
    ]


def test_param_is_required_no_default() -> None:
    docstring = """
    Test required param without default.

    [parameters]
    `req_param` (int):: A required parameter.
    """
    doc = asciidocstring.parse(docstring)
    assert len(doc.parameters) == 1
    assert doc.parameters[0].name == "req_param"
    assert doc.parameters[0].default is None
    assert doc.parameters[0].is_required is True


def test_param_is_required_with_default() -> None:
    docstring = """
    Test param with default and optional param.

    [parameters]
    `with_default` (int):: Param with default. Defaults to 42.
    `is_optional` (str, optional):: Optional param without default.
    """
    doc = asciidocstring.parse(docstring)
    assert len(doc.parameters) == 2

    assert doc.parameters[0].name == "with_default"
    assert doc.parameters[0].default == "42"
    assert doc.parameters[0].optional is True
    assert doc.parameters[0].is_required is False

    assert doc.parameters[1].name == "is_optional"
    assert doc.parameters[1].default is None
    assert doc.parameters[1].optional is True
    assert doc.parameters[1].is_required is False


def test_versionadded_parsed() -> None:
    docstring_simple = """
    A simple function.

    :versionadded: 1.2.0
    """
    doc1 = asciidocstring.parse(docstring_simple)
    assert doc1.semantics.version_added is not None
    assert doc1.semantics.version_added.version == "1.2.0"
    assert doc1.semantics.version_added.note is None

    docstring_with_next_line = """
    A function with note.

    :versionadded: 1.2.0
    Added support for async compilation.
    """
    doc2 = asciidocstring.parse(docstring_with_next_line)
    assert doc2.semantics.version_added is not None
    assert doc2.semantics.version_added.version == "1.2.0"
    assert doc2.semantics.version_added.note == "Added support for async compilation."
    assert doc2.summary == "A function with note."
    assert "Added support" not in doc2.description

    docstring_same_line = """
    A function with same-line note.

    :versionadded: 1.2.0 Added support for async compilation.
    """
    doc3 = asciidocstring.parse(docstring_same_line)
    assert doc3.semantics.version_added is not None
    assert doc3.semantics.version_added.version == "1.2.0"
    assert doc3.semantics.version_added.note == "Added support for async compilation."


def test_deprecated_role_parsed() -> None:
    docstring_with_rep = """
    A deprecated function.

    :deprecated: 2.0.0
    Use async_compile instead.
    """
    doc1 = asciidocstring.parse(docstring_with_rep)
    assert doc1.semantics.deprecated_role is not None
    assert doc1.semantics.deprecated_role.since == "2.0.0"
    assert doc1.semantics.deprecated_role.replacement == "async_compile"
    assert doc1.semantics.deprecated_role.note == "Use async_compile instead."
    assert doc1.summary == "A deprecated function."
    assert "Use async_compile" not in doc1.description

    docstring_backtick_rep = """
    A function with backticks in replacement.

    :deprecated: 2.0.0
    Use `async_compile()` instead. Will be removed in 3.0.0.
    """
    doc2 = asciidocstring.parse(docstring_backtick_rep)
    assert doc2.semantics.deprecated_role is not None
    assert doc2.semantics.deprecated_role.since == "2.0.0"
    assert doc2.semantics.deprecated_role.replacement == "async_compile()"
    assert doc2.semantics.deprecated_role.note == (
        "Use async_compile() instead. Will be removed in 3.0.0."
    )

    docstring_bare = """
    Bare deprecation role.

    :deprecated: 2.0.0
    """
    doc3 = asciidocstring.parse(docstring_bare)
    assert doc3.semantics.deprecated_role is not None
    assert doc3.semantics.deprecated_role.since == "2.0.0"
    assert doc3.semantics.deprecated_role.replacement is None
    assert doc3.semantics.deprecated_role.note is None

    # Coexistence of :deprecated: role and [deprecated] block
    docstring_coexistence = """
    Function with both deprecation forms.

    :deprecated: 2.0.0
    Use `new_api()` instead.

    [deprecated]
    ====
    Deprecated in version 2.0: Legacy synchronous caller.
    ====
    """
    doc4 = asciidocstring.parse(docstring_coexistence)
    assert doc4.semantics.deprecated_role is not None
    assert doc4.semantics.deprecated_role.since == "2.0.0"
    assert doc4.semantics.deprecated_role.replacement == "new_api()"
    assert doc4.semantics.deprecated is not None
    assert doc4.semantics.deprecated.version == "2.0"
    assert "Legacy synchronous caller." in doc4.semantics.deprecated.reason


def test_experimental_parsed() -> None:
    docstring_bare = """
    An experimental feature.

    :experimental:
    """
    doc1 = asciidocstring.parse(docstring_bare)
    assert doc1.semantics.is_experimental is True

    docstring_true = """
    Explicitly experimental.

    :experimental: true
    """
    doc2 = asciidocstring.parse(docstring_true)
    assert doc2.semantics.is_experimental is True

    docstring_negated = """
    Negated experimental.

    :!experimental:
    """
    doc3 = asciidocstring.parse(docstring_negated)
    assert doc3.semantics.is_experimental is False


def test_versionchanged_multiple() -> None:
    docstring = """
    A function with multiple revisions.

    :versionchanged: 1.1.0
    Added foo support.
    :versionchanged: 1.2.0 Added bar support.
    :versionchanged: 1.3.0
    """
    doc = asciidocstring.parse(docstring)
    assert len(doc.semantics.version_changed) == 3

    assert doc.semantics.version_changed[0].version == "1.1.0"
    assert doc.semantics.version_changed[0].note == "Added foo support."

    assert doc.semantics.version_changed[1].version == "1.2.0"
    assert doc.semantics.version_changed[1].note == "Added bar support."

    assert doc.semantics.version_changed[2].version == "1.3.0"
    assert doc.semantics.version_changed[2].note is None


def test_absent_version_fields_are_none() -> None:
    doc = asciidocstring.parse("""
    A simple docstring with no version or deprecation roles.

    [parameters]
    `x` (int):: An integer.
    """)
    assert doc.semantics.version_added is None
    assert doc.semantics.version_changed == []
    assert doc.semantics.deprecated_role is None
    assert doc.semantics.is_experimental is False


def test_document_version_properties() -> None:
    # Verify top-level exports
    from asciidocstring import DeprecationDoc, VersionDoc
    assert VersionDoc is not None
    assert DeprecationDoc is not None

    doc = asciidocstring.parse("""
    Docstring with all version roles.

    :versionadded: 1.0.0
    Initial implementation.

    :versionchanged: 1.1.0
    Performance optimization.

    :deprecated: 2.0.0
    Use `new_func()` instead.

    :experimental:
    """)
    assert doc.version_added is not None
    assert doc.version_added.version == "1.0.0"
    assert doc.version_added.note == "Initial implementation."

    assert len(doc.version_changed) == 1
    assert doc.version_changed[0].version == "1.1.0"
    assert doc.version_changed[0].note == "Performance optimization."

    assert doc.deprecated_role is not None
    assert doc.deprecated_role.since == "2.0.0"
    assert doc.deprecated_role.replacement == "new_func()"
    assert doc.deprecated_role.note == "Use new_func() instead."

    assert doc.is_experimental is True

    # When roles absent
    bare_doc = asciidocstring.parse("Plain docstring.")
    assert bare_doc.version_added is None
    assert bare_doc.version_changed == []
    assert bare_doc.deprecated_role is None
    assert bare_doc.is_experimental is False


def test_deprecated_note_without_replacement() -> None:
    doc = asciidocstring.parse("""
    A deprecated function.

    :deprecated: 2.0.0
    This function is obsolete and will be deleted.
    """)
    assert doc.deprecated_role is not None
    assert doc.deprecated_role.since == "2.0.0"
    assert doc.deprecated_role.replacement is None
    assert doc.deprecated_role.note == "This function is obsolete and will be deleted."


def test_version_role_combined_inline_and_contiguous_notes() -> None:
    doc = asciidocstring.parse("""
    Function with combined notes.

    :versionadded: 1.0.0 Initial implementation.
    Extended in subsequent patch with additional capabilities.
    """)
    assert doc.version_added is not None
    assert doc.version_added.version == "1.0.0"
    assert doc.version_added.note == (
        "Initial implementation. Extended in subsequent "
        "patch with additional capabilities."
    )


def test_visit_attribute_entry_direct() -> None:
    from asciidoctrine.nodes import AttributeEntry

    from asciidocstring.semantics import SemanticExtractorVisitor

    visitor = SemanticExtractorVisitor()
    entry = AttributeEntry("versionadded", "1.5.0 Direct visit.")
    visitor.visit_attribute_entry(entry)
    assert visitor.version_added is not None
    assert visitor.version_added.version == "1.5.0"
    assert visitor.version_added.note == "Direct visit."


def test_embedded_attribute_entry_in_paragraph() -> None:
    from asciidoctrine.nodes import Paragraph, Text

    from asciidocstring.semantics import SemanticExtractorVisitor

    para = Paragraph(
        inlines=[
            Text(
                value=(
                    "Leading paragraph text.\n"
                    ":versionadded: 1.2.0\n"
                    "Feature note.\n"
                    "Trailing text."
                )
            )
        ]
    )
    visitor = SemanticExtractorVisitor()
    visitor.visit_paragraph(para)
    assert visitor.version_added is not None
    assert visitor.version_added.version == "1.2.0"
    assert visitor.version_added.note == "Feature note."
    assert visitor._leading_paragraphs == ["Leading paragraph text.\nTrailing text."]


