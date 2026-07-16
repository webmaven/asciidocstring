import asciidocstring


def test_extract_python_source_blocks() -> None:
    # Docstring with python source block and other language
    docstring = """
        Some introduction text.
        
        [source,python]
        ----
        assert foo() == 42
        ----
        
        And some Ruby code that should be ignored by default:
        [source,ruby]
        ----
        foo = 42
        ----
        """
    doc = asciidocstring.parse(docstring)
    tests = doc.extract_tests(language="python")

    assert len(tests) == 1
    test_block = tests[0]

    # Assert fields are extracted correctly
    assert test_block.content.strip() == "assert foo() == 42"
    assert test_block.language == "python"
    assert test_block.is_interactive is False
    assert test_block.line_number > 1  # Should find starting line number of block


def test_extract_interactive_prompts() -> None:
    # Docstring with standard python interactive prompts
    docstring = """
        [source,python]
        ----
        >>> foo()
        42
        ----
        """
    doc = asciidocstring.parse(docstring)
    tests = doc.extract_tests(language="python")

    assert len(tests) == 1
    assert tests[0].is_interactive is True


def test_requires_test_marker_filter() -> None:
    # Docstring containing both a normal source block and different
    # test-marked source blocks
    docstring = """
        A non-test block:
        [source,python]
        ----
        x = 1
        ----
        
        A test block with consecutive independent attribute lines:
        # (merged role + source)
        [.test]
        [source,python]
        ----
        y = 2
        ----
        
        A test block with positional third attribute [source,python,test]:
        [source,python,test]
        ----
        z = 3
        ----
        """
    doc = asciidocstring.parse(docstring)

    # By default, extracting tests should not require explicit marker
    all_tests = doc.extract_tests(requires_test_marker=False)
    assert len(all_tests) == 3

    # When requires_test_marker is True, only return blocks with "test" marker
    explicit_tests = doc.extract_tests(requires_test_marker=True)
    assert len(explicit_tests) == 2

    contents = {b.content.strip() for b in explicit_tests}
    assert contents == {"y = 2", "z = 3"}
