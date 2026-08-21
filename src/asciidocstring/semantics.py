"""Semantic extractor visitor for parsing structured docstring components."""

import re
from typing import Any

from asciidoctrine.nodes import (
    Admonition,
    DescriptionList,
    Example,
    Listing,
    NodeVisitor,
    Open,
    Paragraph,
    Section,
)

from .models import (
    DocstringAttribute,
    DocstringDeprecated,
    DocstringExample,
    DocstringParam,
    DocstringRaise,
    DocstringReceive,
    DocstringReturn,
    DocstringWarn,
    DocstringYield,
)


class SemanticExtractorVisitor(NodeVisitor):
    """AST visitor to inspect and extract structured semantic components."""

    def __init__(self) -> None:
        self.summary: str = ""
        self.description: str = ""
        self.parameters: list[DocstringParam] = []
        self.returns: list[DocstringReturn] = []
        self.yields: list[DocstringYield] = []
        self.raises: list[DocstringRaise] = []
        self.receives: list[DocstringReceive] = []
        self.warns: list[DocstringWarn] = []
        self.attributes: list[DocstringAttribute] = []
        self.examples: list[DocstringExample] = []
        self.deprecated: DocstringDeprecated | None = None
        self._leading_paragraphs: list[str] = []
        self._seen_semantic_block: bool = False
        self._current_role: str = ""

    def extract(self, ast: Any) -> "SemanticExtractorVisitor":
        self.visit(ast)
        if self._leading_paragraphs:
            self.summary = self._leading_paragraphs[0]
            self.description = "\n\n".join(self._leading_paragraphs)
        return self

    def _get_node_text(self, node: Any) -> str:
        """Extract plain text recursively from an inline or block node."""
        if hasattr(node, "value"):
            return str(node.value)
        if hasattr(node, "inlines") and node.inlines:
            return "".join(self._get_node_text(inl) for inl in node.inlines)
        if hasattr(node, "terms") and node.terms:
            return "".join(self._get_node_text(term) for term in node.terms)
        if hasattr(node, "blocks") and node.blocks:
            return "\n\n".join(self._get_node_text(blk) for blk in node.blocks)
        return ""

    def _get_block_role(self, node: Any) -> str:
        """Identify if a block or section carries a semantic role/title."""
        attrs = getattr(node, "attributes", {}) or {}
        role = attrs.get("role", "")
        style = attrs.get("style", "")
        pos_1 = attrs.get("1", "")
        title_text = ""
        if hasattr(node, "title") and node.title:
            title_text = self._get_node_text(node.title).strip().lower()

        candidates = [
            str(role).lower(),
            str(style).lower(),
            str(pos_1).lower(),
            title_text,
        ]
        for c in candidates:
            if c:
                if c in ("parameters", "params", "args", "arguments", "parameter"):
                    return "parameters"
                if c in ("returns", "return"):
                    return "returns"
                if c in ("yields", "yield"):
                    return "yields"
                if c in ("raises", "raise", "exceptions", "exception"):
                    return "raises"
                if c in ("receives", "receive"):
                    return "receives"
                if c in ("warns", "warn", "warnings", "warning"):
                    return "warns"
                if c in ("attributes", "attribute", "attrs"):
                    return "attributes"
                if c in ("examples", "example"):
                    return "examples"
                if c in ("deprecated", "deprecation"):
                    return "deprecated"
        return ""

    def _parse_param_term(self, term_text: str, desc_text: str) -> DocstringParam:
        clean_term = term_text.strip().strip("`").strip()
        optional = False
        type_name = None
        default_val = None

        desc = desc_text.strip()
        type_match = re.match(
            r"^\s*\(([^)]+)\)\s*(?:[-:]\s*)?(.*)$", desc, re.DOTALL
        )
        if type_match:
            raw_type, remaining_desc = type_match.groups()
            desc = remaining_desc.strip()
            type_parts = [p.strip().strip("`") for p in raw_type.split(",")]
            if "optional" in [p.lower() for p in type_parts]:
                optional = True
                type_parts = [p for p in type_parts if p.lower() != "optional"]
            if type_parts:
                type_name = type_parts[0]

        default_match = re.search(
            r"(?:defaults? to|default is)\s+[`'\"]?([^`'\".\n]+)[`'\"]?",
            desc,
            re.IGNORECASE,
        )
        if default_match:
            default_val = default_match.group(1).strip()

        return DocstringParam(
            name=clean_term,
            type_name=type_name,
            description=desc,
            default=default_val,
            optional=optional or (default_val is not None),
        )

    def _parse_return_term(
        self, term_text: str, desc_text: str
    ) -> DocstringReturn:
        clean_term = term_text.strip().strip("`").strip()
        return DocstringReturn(
            type_name=clean_term if clean_term else None,
            description=desc_text.strip(),
        )

    def _parse_raise_term(self, term_text: str, desc_text: str) -> DocstringRaise:
        clean_term = term_text.strip().strip("`").strip()
        return DocstringRaise(
            type_name=clean_term,
            description=desc_text.strip(),
        )

    def _parse_yield_term(self, term_text: str, desc_text: str) -> DocstringYield:
        clean_term = term_text.strip().strip("`").strip()
        return DocstringYield(
            type_name=clean_term if clean_term else None,
            description=desc_text.strip(),
        )

    def _parse_receive_term(self, term_text: str, desc_text: str) -> DocstringReceive:
        clean_term = term_text.strip().strip("`").strip()
        return DocstringReceive(
            type_name=clean_term if clean_term else None,
            description=desc_text.strip(),
        )

    def _parse_warn_term(self, term_text: str, desc_text: str) -> DocstringWarn:
        clean_term = term_text.strip().strip("`").strip()
        return DocstringWarn(
            type_name=clean_term if clean_term else None,
            description=desc_text.strip(),
        )

    def _parse_attr_term(self, term_text: str, desc_text: str) -> DocstringAttribute:
        param = self._parse_param_term(term_text, desc_text)
        return DocstringAttribute(
            name=param.name,
            type_name=param.type_name,
            description=param.description,
            value=param.default,
        )

    def _parse_deprecated_block(self, text: str) -> DocstringDeprecated:
        version = None
        match = re.search(r"version\s+([0-9a-zA-Z._-]+)", text, re.IGNORECASE)
        if match:
            version = match.group(1)
        reason = text.strip()
        return DocstringDeprecated(version=version, reason=reason)

    def visit_paragraph(self, node: Paragraph) -> None:
        role = self._get_block_role(node) or self._current_role
        if role == "deprecated":
            self._seen_semantic_block = True
            text = self._get_node_text(node)
            self.deprecated = self._parse_deprecated_block(text)
            return
        text = self._get_node_text(node).strip()
        if not self._seen_semantic_block and text:
            self._leading_paragraphs.append(text)

    def visit_descriptionlist(self, node: DescriptionList) -> None:
        role = self._get_block_role(node) or self._current_role
        if role:
            self._seen_semantic_block = True
            for item in node.items:
                term_text = "".join(
                    self._get_node_text(t) for t in getattr(item, "terms", [])
                )
                desc_text = "\n\n".join(
                    self._get_node_text(b) for b in getattr(item, "blocks", [])
                )
                if role == "parameters":
                    self.parameters.append(self._parse_param_term(term_text, desc_text))
                elif role == "returns":
                    self.returns.append(self._parse_return_term(term_text, desc_text))
                elif role == "yields":
                    self.yields.append(self._parse_yield_term(term_text, desc_text))
                elif role == "raises":
                    self.raises.append(self._parse_raise_term(term_text, desc_text))
                elif role == "receives":
                    self.receives.append(self._parse_receive_term(term_text, desc_text))
                elif role == "warns":
                    self.warns.append(self._parse_warn_term(term_text, desc_text))
                elif role == "attributes":
                    self.attributes.append(self._parse_attr_term(term_text, desc_text))
        else:
            self.generic_visit(node)

    def visit_section(self, node: Section) -> None:
        role = self._get_block_role(node)
        old_role = self._current_role
        if role:
            self._seen_semantic_block = True
            if role == "deprecated":
                text = self._get_node_text(node)
                self.deprecated = self._parse_deprecated_block(text)
                return
            self._current_role = role
        self.generic_visit(node)
        self._current_role = old_role

    def visit_open(self, node: Open) -> None:
        role = self._get_block_role(node)
        old_role = self._current_role
        if role:
            self._seen_semantic_block = True
            if role == "deprecated":
                text = self._get_node_text(node)
                self.deprecated = self._parse_deprecated_block(text)
                return
            self._current_role = role
        self.generic_visit(node)
        self._current_role = old_role

    def visit_admonition(self, node: Admonition) -> None:
        variant = getattr(node, "variant", "")
        role = self._get_block_role(node) or variant
        if role == "deprecated":
            self._seen_semantic_block = True
            text = self._get_node_text(node)
            self.deprecated = self._parse_deprecated_block(text)
            return
        self.generic_visit(node)

    def visit_example(self, node: Example) -> None:
        role = self._get_block_role(node)
        old_role = self._current_role
        if role:
            self._seen_semantic_block = True
            if role == "deprecated":
                text = self._get_node_text(node)
                self.deprecated = self._parse_deprecated_block(text)
                return
            self._current_role = role
        self.generic_visit(node)
        self._current_role = old_role

    def visit_listing(self, node: Listing) -> None:
        attrs = getattr(node, "attributes", {}) or {}
        style = attrs.get("style", "")
        lang = attrs.get("language", "python")
        content = self._get_node_text(node)
        if style == "source" or node.name == "listing" or "test" in attrs:
            self.examples.append(
                DocstringExample(
                    content=content,
                    language=lang,
                    is_interactive=">>> " in content,
                    attributes=attrs,
                )
            )
