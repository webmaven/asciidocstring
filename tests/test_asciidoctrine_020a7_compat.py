"""Compatibility tests verifying upstream asciidoctrine 0.2.0a6-0.2.0a7 fixes."""

from asciidocstring import from_griffe, parse


def test_hanging_indented_list_items_in_docstring() -> None:
    """Issue #125 / asciidocstring #5: Hanging-indented lines stay in item."""
    doc = parse("""
        Process plugins.

        1. Discovery pass: Scans entry points, local plugins directory,
           and importlib module paths. Nothing is registered here.
        2. Registration pass: Iterates config.plugins in list order,
           and registers each entry in order.
    """)
    assert doc.summary == "Process plugins."
    rest = doc.to_rest()
    assert "Discovery pass: Scans entry points" in rest
    assert "Registration pass: Iterates config.plugins" in rest
    # Ensure no spurious literal block was created
    assert ".. code-block::" not in rest
    assert "::" not in rest


def test_hanging_indented_list_in_griffe_bridge() -> None:
    """Issue #5: Griffe docstring with hanging-indented list preserves text."""
    doc = from_griffe(
        """
        Description of workflow.

        1. Discovery pass: Scans entry points, local plugins directory,
           and importlib module paths. Nothing is registered here.
        2. Registration pass: Iterates config.plugins in list order,
           and registers each entry in order.
        """,
        style="google",
    )
    rest = doc.to_rest()
    assert "Discovery pass: Scans entry points" in rest
    assert "Registration pass: Iterates config.plugins" in rest
    assert ".. code-block::" not in rest


def test_backslash_escaped_inline_formatting() -> None:
    """AsciiDoctrine #113: Backslash delimiters suppress span creation."""
    doc = parse("""
        A utility function.

        [parameters]
        `name` (str):: Must not match \\__special__ or \\*reserved*.
    """)
    assert len(doc.parameters) == 1
    desc = doc.parameters[0].description
    assert "__special__" in desc
    assert "*reserved*" in desc
