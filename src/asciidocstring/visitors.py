from dataclasses import dataclass
from typing import Any, Dict, List

from asciidoctrine.nodes import Listing, NodeVisitor


@dataclass
class TestBlock:
    """Represents an executable code block extracted from a docstring."""

    content: str
    language: str
    line_number: int
    is_interactive: bool  # True if it contains ">>> " style prompts
    attributes: Dict[str, Any]


class TestBlockExtractorVisitor(NodeVisitor):
    """AST visitor to locate and extract Python test blocks from a docstring."""

    def __init__(self, target_language: str, requires_test_marker: bool):
        self.target_language = target_language.lower()
        self.requires_test_marker = requires_test_marker
        self.extracted_tests: List[TestBlock] = []

    def extract(self, node: Any) -> List[TestBlock]:
        """Reset state, traverse the node tree, and return extracted test blocks."""
        self.extracted_tests = []
        self.visit(node)
        return self.extracted_tests

    def visit_listing(self, node: Listing) -> None:
        """Process code listing blocks."""
        attrs = node.attributes or {}
        style = attrs.get("style", "")
        lang = attrs.get("language", "").lower()

        # A Listing node with style='source' represents a source code block
        is_source = style == "source" or node.name == "listing"
        is_target_lang = (lang == self.target_language) or (
            not lang and self.target_language == "python"
        )

        # Sgthand [.test] parsed as 'role': 'test', or positional [source,python,test]
        has_test_marker = (
            "test" in attrs
            or attrs.get("role") == "test"
            or attrs.get("3") == "test"
            or "test" in attrs.get("positional", [])
        )

        if is_source and is_target_lang:
            if self.requires_test_marker and not has_test_marker:
                return  # Skip since test marker is required but not present

            # Extract content from Text inline nodes
            content_parts = [
                inline.value for inline in node.inlines if hasattr(inline, "value")
            ]
            content = "".join(content_parts)

            # Identify interactive session
            is_interactive = ">>> " in content

            # Fetch line numbers from node locations if available
            line_number = 1
            if hasattr(node, "location") and node.location:
                line_number = node.location[0].get("line", 1)

            self.extracted_tests.append(
                TestBlock(
                    content=content,
                    language=lang or self.target_language,
                    line_number=line_number,
                    is_interactive=is_interactive,
                    attributes=attrs,
                )
            )


class ReSTSerializerVisitor(NodeVisitor):
    """AST visitor to serialize parsed AsciiDoc to reStructuredText."""

    def __init__(self) -> None:
        self.output: List[str] = []
        self._indent_level = 0
        self._current_list_depth = 0
        self._footnotes: List[tuple[str | None, List[Any]]] = []
        self._footnote_ids: set[str] = set()

    def serialize(self, node: Any) -> str:
        """Reset state, walk AST, and return reST representation."""
        self.output = []
        self._indent_level = 0
        self._current_list_depth = 0
        self._footnotes = []
        self._footnote_ids = set()
        self.visit(node)

        if self._footnotes:
            self.output.append("\n")
            for fn_id, inlines in self._footnotes:
                content = "".join(self.render_inline(sub) for sub in inlines)
                if fn_id:
                    self.output.append(f".. [{fn_id}] {content}\n")
                else:
                    self.output.append(f".. [#] {content}\n")

        # Strip excess trailing newlines from end of document
        return "".join(self.output).rstrip() + "\n"

    def render_inline(self, node: Any) -> str:
        """Recursively render inline nodes and format their styles."""
        if node.name == "text":
            return str(node.value)
        elif node.name == "span":
            content = "".join(self.render_inline(sub) for sub in node.inlines)
            if node.variant == "strong":
                return f"**{content}**"
            elif node.variant == "emphasis":
                return f"*{content}*"
            elif node.variant == "code":
                return f"``{content}``"
            return content
        elif node.name == "ref":
            variant = getattr(node, "variant", "")
            if variant == "footnote":
                target = getattr(node, "target", "")
                if target:
                    if node.inlines:
                        if target not in self._footnote_ids:
                            self._footnote_ids.add(target)
                            self._footnotes.append((target, node.inlines))
                    return f"[{target}]_"
                else:
                    self._footnotes.append((None, node.inlines))
                    return "[#]_"
            else:
                content = "".join(self.render_inline(sub) for sub in node.inlines)
                target = getattr(node, "target", "")
                return f"`{content} <{target}>`_"
        return ""

    def visit_document(self, node: Any) -> None:
        """Render Document header title and traverse block content."""
        if hasattr(node, "header") and node.header and node.header.title:
            title_text = "".join(
                self.render_inline(inline) for inline in node.header.title.inlines
            )
            underline = "=" * len(title_text)
            self.output.append(f"{title_text}\n{underline}\n\n")

        for block in node.blocks:
            self.visit(block)

    def visit_section(self, node: Any) -> None:
        """Render Section title with standard depth-based underline indicators."""
        level = getattr(node, "level", 1)
        # Underline character mapping: depth 0 is Document (=), depth 1 is Section (-)
        char_map = {0: "=", 1: "-", 2: "~", 3: "^"}
        underline_char = char_map.get(level, "-")

        if node.title:
            title_text = "".join(
                self.render_inline(inline) for inline in node.title.inlines
            )
            underline = underline_char * len(title_text)
            self.output.append(f"{title_text}\n{underline}\n\n")

        for block in node.blocks:
            self.visit(block)

    def visit_paragraph(self, node: Any) -> None:
        """Render a plain paragraph with the current block level indentation."""
        content = "".join(self.render_inline(inline) for inline in node.inlines)
        indent = " " * self._indent_level
        self.output.append(f"{indent}{content}\n\n")

    def visit_listing(self, node: Any) -> None:
        """Render code block listing using Sphinx-standard code-block directives."""
        attrs = node.attributes or {}
        lang = attrs.get("language", "python")

        content_parts = [
            inline.value for inline in node.inlines if hasattr(inline, "value")
        ]
        content = "".join(content_parts)

        indent = " " * self._indent_level
        self.output.append(f"{indent}.. code-block:: {lang}\n\n")

        body_indent = " " * (self._indent_level + 3)
        indented_lines = []
        for line in content.splitlines():
            if line.strip():
                indented_lines.append(f"{body_indent}{line}")
            else:
                indented_lines.append("")
        body = "\n".join(indented_lines)
        self.output.append(f"{body}\n\n")

    def visit_list(self, node: Any) -> None:
        """Render bullets and handle list level nesting contexts."""
        old_depth = self._current_list_depth
        self._current_list_depth += 1

        for item in node.items:
            self.visit(item)

        self._current_list_depth = old_depth

    def visit_listitem(self, node: Any) -> None:
        """Render standard bullet item formatting."""
        indent_size = (self._current_list_depth - 1) * 2
        indent = " " * indent_size

        content = ""
        if hasattr(node, "principal") and node.principal:
            content = "".join(self.render_inline(inline) for inline in node.principal)

        self.output.append(f"{indent}* {content}\n")

        # Render nested block children under this item
        old_indent = self._indent_level
        self._indent_level += indent_size + 2
        for block in node.blocks:
            self.visit(block)
        self._indent_level = old_indent

    def visit_descriptionlist(self, node: Any) -> None:
        """Render description lists."""
        for item in node.items:
            self.visit(item)

    def visit_descriptionlistitem(self, node: Any) -> None:
        """Render a single description list item (definition)."""
        for term in node.terms:
            term_text = "".join(self.render_inline(inline) for inline in term.inlines)
            self.output.append(f"{term_text}\n")

        old_indent = self._indent_level
        # reST standard definition block is indented by 3 spaces
        self._indent_level += 3
        for block in node.blocks:
            self.visit(block)
        self._indent_level = old_indent

    def visit_admonition(self, node: Any) -> None:
        """Render standard admonition blocks (e.g. note, warning, tip)."""
        variant = getattr(node, "variant", "note").lower()

        indent = " " * self._indent_level
        self.output.append(f"{indent}.. {variant}::\n\n")

        old_indent = self._indent_level
        self._indent_level += 3
        for block in node.blocks:
            self.visit(block)
        self._indent_level = old_indent

    def visit_thematic_break(self, node: Any) -> None:
        """Render thematic breaks (horizontal lines)."""
        indent = " " * self._indent_level
        self.output.append(f"{indent}----\n\n")
