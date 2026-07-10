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
    
    expected_block = ".. code-block:: python\n\n   x = 42\n   print(x)"
    assert expected_block in rest

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

def test_admonitions_serialization() -> None:
    docstring = """
        WARNING: This is a warning message.
        """
    doc = asciidocstring.parse(docstring)
    rest = doc.to_rest()
    
    expected_admonition = ".. warning::\n\n   This is a warning message."
    assert expected_admonition in rest

def test_links_serialization() -> None:
    from asciidoctrine.nodes import Document, Paragraph, Ref, Text
    
    # We construct an AST programmatically to test our visitor's translation of
    # Ref nodes, keeping the codebase pure and avoiding brittle parser-level
    # regex fallbacks.
    doc_node = Document()
    para_node = Paragraph()
    
    ref_node = Ref("link", "http://example.com")
    ref_node.name = "ref"
    ref_node.inlines = [Text(value="Example Site")]
    
    para_node.inlines = [
        Text(value="Check out "),
        ref_node,
        Text(value=" for more details.")
    ]
    doc_node.blocks = [para_node]
    
    doc = asciidocstring.parse("")
    doc.ast = doc_node
    
    rest = doc.to_rest()
    expected_link = "Check out `Example Site <http://example.com>`_ for more details."
    assert expected_link in rest

