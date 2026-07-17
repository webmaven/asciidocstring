import asciidocstring


def test_basic_blocks_serialization() -> None:
    docstring = """
        = Document Title
        
        This is a plain paragraph.
        
        == Section Subtitle
        
        Another paragraph.
        """
    doc = asciidocstring.parse(docstring)
    rest = doc.to_rest()

    # Assert titles are translated to proper reST underlines
    assert "Document Title\n==============" in rest
    assert "Section Subtitle\n----------------" in rest
    assert "This is a plain paragraph." in rest


def test_source_listing_serialization() -> None:
    docstring = """
        Here is some code:
        
        [source,python]
        ----
        x = 42

        print(x)
        ----
        """
    doc = asciidocstring.parse(docstring)
    rest = doc.to_rest()

    expected_block = ".. code-block:: python\n\n   x = 42\n\n   print(x)"
    assert expected_block in rest


def test_thematic_break_serialization() -> None:
    docstring = """
        Paragraph before.
        
        '''
        
        Paragraph after.
        """
    doc = asciidocstring.parse(docstring)
    rest = doc.to_rest()

    assert "Paragraph before.\n\n----\n\nParagraph after." in rest


def test_inline_formatting_serialization() -> None:
    docstring = """
        This text contains *bold word*, _italic word_, and `monospace code`.
        """
    doc = asciidocstring.parse(docstring)
    rest = doc.to_rest()

    # Bold *x* in AsciiDoc -> **x** in reST
    # Italic _x* in AsciiDoc -> *x* in reST
    # Monospace `x` in AsciiDoc -> ``x`` in reST
    assert "contains **bold word**," in rest
    assert "*italic word*," in rest
    assert "``monospace code``." in rest


def test_lists_serialization() -> None:
    docstring = """
        * First bullet
        * Second bullet
        ** Nested bullet
        """
    doc = asciidocstring.parse(docstring)
    rest = doc.to_rest()

    # Assert standard bullet formatting and indentation
    assert "* First bullet" in rest
    assert "  * Nested bullet" in rest


def test_description_lists_serialization() -> None:
    docstring = """
        param1 (int):: The first parameter
        param2 (str):: The second parameter
        """
    doc = asciidocstring.parse(docstring)
    rest = doc.to_rest()

    expected_param1 = "param1 (int)\n   The first parameter"
    expected_param2 = "param2 (str)\n   The second parameter"
    assert expected_param1 in rest
    assert expected_param2 in rest


def test_consecutive_multiline_description_lists_serialization() -> None:
    docstring = """
        base_dir::
          The base directory for resolving include paths.
          Defaults to the current working directory.
        safe_mode::
          If True, prevents including files outside base_dir.
        """
    doc = asciidocstring.parse(docstring)
    rest = doc.to_rest()

    expected = (
        "base_dir\n"
        "   The base directory for resolving include paths.\n"
        "   Defaults to the current working directory.\n"
        "\n"
        "safe_mode\n"
        "   If True, prevents including files outside base_dir."
    )
    assert expected in rest

    # Verify that docutils parses it with no unexpected warnings or errors
    import docutils.core
    settings = {"warning_stream": None, "halt_level": 2}  # halt_level=2 is WARNING
    docutils.core.publish_parts(rest, writer_name="html", settings_overrides=settings)



def test_admonitions_serialization() -> None:
    docstring = """
        WARNING: This is a warning message.
        """
    doc = asciidocstring.parse(docstring)
    rest = doc.to_rest()

    expected_admonition = ".. warning::\n\n   This is a warning message."
    assert expected_admonition in rest


def test_links_serialization() -> None:
    docstring = """
        Check out http://example.com[Example Site] for more details.
        """
    doc = asciidocstring.parse(docstring)
    rest = doc.to_rest()

    expected_link = "Check out `Example Site <http://example.com>`_ for more details."
    assert expected_link in rest


def test_footnotes_serialization() -> None:
    docstring = """
        This is an anonymous footnote footnote:[Anonymous info.].
        This is a named footnote footnoteref:[fn-id, Named info.].
        Referencing the named footnote again footnoteref:[fn-id].
        """
    doc = asciidocstring.parse(docstring)
    rest = doc.to_rest()

    assert "an anonymous footnote [#]_." in rest
    assert "a named footnote [fn-id]_." in rest
    assert "the named footnote again [fn-id]_." in rest

    # Assert definitions are appended at the bottom
    assert ".. [#] Anonymous info." in rest
    assert ".. [fn-id] Named info." in rest


def test_description_lists_edge_cases_and_coverage() -> None:
    from asciidoctrine.nodes import Paragraph, Span, Text

    from asciidocstring.visitors import ReSTSerializerVisitor

    visitor = ReSTSerializerVisitor()

    # Cover line 184: empty line in paragraph
    p_node = Paragraph(inlines=[Text(value="Line 1\n\nLine 2")])
    visitor.output = []
    visitor.visit_paragraph(p_node)
    assert "Line 1\n\nLine 2" in "".join(visitor.output)

    # Cover line 253: _ensure_blank_line when last_str is empty
    visitor.output = [""]
    visitor._ensure_blank_line()

    # Cover line 257: _ensure_blank_line when trailing_newlines == 0
    visitor.output = ["term"]
    visitor._ensure_blank_line()
    assert visitor.output[-1] == "\n\n"

    # Cover line 259: _ensure_blank_line when trailing_newlines == 1
    visitor.output = ["term\n"]
    visitor._ensure_blank_line()
    assert visitor.output[-1] == "\n"

    # Cover line 124: span variant not recognized
    span_node = Span(variant="unknown", inlines=[Text(value="hello")])
    res = visitor.render_inline(span_node)
    assert res == "hello"

    # Cover line 142: unrecognized node name (not text, span, or ref)
    class UnknownNode:
        name = "unknown"
    res = visitor.render_inline(UnknownNode())
    assert res == ""

