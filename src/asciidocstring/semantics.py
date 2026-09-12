"""Semantic extractor visitor for parsing structured docstring components."""

import re
from typing import Any

from asciidoctrine.nodes import (
    Admonition,
    AttributeEntry,
    DescriptionList,
    Example,
    Listing,
    Node,
    NodeVisitor,
    Open,
    Paragraph,
    Section,
)

from .models import (
    DeprecationDoc,
    DocstringAttribute,
    DocstringDeprecated,
    DocstringExample,
    DocstringParam,
    DocstringRaise,
    DocstringReceive,
    DocstringReturn,
    DocstringWarn,
    DocstringYield,
    VersionDoc,
)

_REPLACEMENT_STOPWORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "and",
        "as",
        "at",
        "by",
        "caution",
        "for",
        "from",
        "in",
        "instead",
        "is",
        "it",
        "not",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "with",
    }
)


def _is_valid_symbol(symbol: str) -> bool:
    """Check if symbol is a valid dotted identifier or callable.

    [parameters]
    `symbol` (str):: Candidate symbol text to validate.

    [returns]
    `bool`:: True if the candidate is a valid identifier or callable.
    """
    parts = symbol.removesuffix("()").split(".")
    return bool(parts) and all(p.isidentifier() for p in parts)



def _extract_replacement(note: str) -> str | None:
    """Extract replacement symbol or function from deprecation note.

    [parameters]
    `note` (str):: Note text to search for replacement indications.

    [returns]
    `str | None`:: Extracted replacement identifier or callable if found.
    """
    for match in re.finditer(
        r"\b(?:use|replaced by|superseded by|replacement[:=])"
        r"\s+(?:the\s+)?`?([a-zA-Z0-9_.]+(?:\(\))?)`?",
        note,
        re.IGNORECASE,
    ):
        candidate = match.group(1).strip().rstrip(".,;:")
        if (
            candidate.lower() not in _REPLACEMENT_STOPWORDS
            and _is_valid_symbol(candidate)
        ):
            return candidate
    return None





def _combine_notes(inline: str | None, contiguous: str | None) -> str | None:
    """Combine inline attribute note with contiguous block note."""
    if inline and contiguous:
        return f"{inline} {contiguous}"
    return contiguous if contiguous is not None else inline


def _split_types(type_str: str) -> list[str]:
    """Split type_str on commas at bracket-depth 0 only."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in type_str:
        if ch in "([{":
            depth += 1
            current.append(ch)
        elif ch in ")]}":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current or parts:
        parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


class SemanticExtractorVisitor(NodeVisitor):
    """AST visitor to inspect and extract structured semantic components.

    Walks an asciidoctrine AST hierarchy to extract structured docstring
    elements such as parameters, returns, yields, raises, receives, warns,
    attributes, deprecation notices, and code examples.

    [attributes]
    `summary` (str):: First paragraph summary of the docstring.
    `description` (str):: Full leading description paragraphs.
    `parameters` (list[DocstringParam]):: Extracted parameter definitions.
    `returns` (list[DocstringReturn]):: Extracted return value definitions.
    `yields` (list[DocstringYield]):: Extracted generator yield definitions.
    `raises` (list[DocstringRaise]):: Extracted exception definitions.
    `receives` (list[DocstringReceive]):: Extracted generator receive definitions.
    `warns` (list[DocstringWarn]):: Extracted warning definitions.
    `attributes` (list[DocstringAttribute]):: Extracted attribute definitions.
    `examples` (list[DocstringExample]):: Extracted code example blocks.
    `deprecated` (DocstringDeprecated | None, optional):: Extracted deprecation
      notice if present. Defaults to `None`.
    `version_added` (VersionDoc | None, optional):: Version in which the feature
      was added. Defaults to `None`.
    `version_changed` (list[VersionDoc]):: List of versions and notes in which the
      feature changed. Defaults to empty list.
    `deprecated_role` (DeprecationDoc | None, optional):: Deprecation role metadata
      from a :deprecated: attribute entry. Defaults to `None`.
    `is_experimental` (bool):: Whether the feature is marked experimental.
      Defaults to `False`.

    [source,python]
    ----
    visitor = SemanticExtractorVisitor()
    visitor.extract(ast_node)
    print(visitor.summary)
    ----
    """

    def __init__(self) -> None:
        """Initialize a new semantic extractor visitor instance.

        [attributes]
        `summary` (str):: First paragraph summary initialized to empty string.
        `description` (str):: Full leading description initialized to empty string.
        `parameters` (list[DocstringParam]):: Parameter list initialized to empty.
        `returns` (list[DocstringReturn]):: Return list initialized to empty.
        `yields` (list[DocstringYield]):: Yield list initialized to empty.
        `raises` (list[DocstringRaise]):: Raise list initialized to empty.
        `receives` (list[DocstringReceive]):: Receive list initialized to empty.
        `warns` (list[DocstringWarn]):: Warning list initialized to empty.
        `attributes` (list[DocstringAttribute]):: Attribute list initialized to empty.
        `examples` (list[DocstringExample]):: Example list initialized to empty.
        `deprecated` (DocstringDeprecated | None, optional):: Deprecation notice.
          Defaults to `None`.
        `version_added` (VersionDoc | None, optional)::
            Version added initialized to `None`.
        `version_changed` (list[VersionDoc])::
            Version changes initialized to empty list.
        `deprecated_role` (DeprecationDoc | None, optional)::
            Deprecation role initialized to `None`.
        `is_experimental` (bool)::
            Experimental flag initialized to `False`.
        """
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
        self.version_added: VersionDoc | None = None
        self.version_changed: list[VersionDoc] = []
        self.deprecated_role: DeprecationDoc | None = None
        self.is_experimental: bool = False
        self._leading_paragraphs: list[str] = []
        self._seen_semantic_block: bool = False
        self._current_role: str = ""

    def extract(self, ast: Any) -> "SemanticExtractorVisitor":
        """Walk the AST to extract and populate semantic docstring components.

        [parameters]
        `ast` (Any):: Parsed asciidoctrine AST root or document node to traverse.

        [returns]
        `SemanticExtractorVisitor`:: The visitor instance populated with
          extracted semantic components.

        [source,python]
        ----
        visitor = SemanticExtractorVisitor().extract(parsed_ast)
        params = visitor.parameters
        ----
        """
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

    def _parse_param_term(
        self, term_text: str, desc_text: str, raw_entry: Any = None
    ) -> DocstringParam:
        clean_term = term_text.strip()
        optional = False
        type_name = None
        default_val = None

        # Check LHS for parenthesized type/optional:
        # e.g. `x1` (float) or name (type, optional)
        term_match = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", clean_term)

        if term_match:
            raw_name, raw_type = term_match.groups()
            name = raw_name.strip().strip("`").strip()
            type_parts = [p.strip("`") for p in _split_types(raw_type)]
            if "optional" in [p.lower() for p in type_parts]:
                optional = True
                type_parts = [p for p in type_parts if p.lower() != "optional"]
            if type_parts:
                type_name = " | ".join(type_parts)
        else:
            name = clean_term.strip("`").strip()

        desc = desc_text.strip()
        type_match = re.match(
            r"^\s*\(([^)]+)\)\s*(?:[-:]\s*)?(.*)$", desc, re.DOTALL
        )
        if type_match:
            raw_type, remaining_desc = type_match.groups()
            desc = remaining_desc.strip()
            type_parts = [p.strip("`") for p in _split_types(raw_type)]
            if "optional" in [p.lower() for p in type_parts]:
                optional = True
                type_parts = [p for p in type_parts if p.lower() != "optional"]
            if not type_name and type_parts:
                type_name = " | ".join(type_parts)

        default_match = re.search(
            r"(?:defaults?(?:\s+(?:to|is)|\s*[:=]))\s*(?:[`'\"]([^`'\"]+)[`'\"]|([^\s,;)]+))",
            desc,
            re.IGNORECASE,
        )
        if default_match:
            default_val = (
                default_match.group(1) or default_match.group(2) or ""
            ).rstrip(".").strip()

        is_required = default_val is None and not optional

        return DocstringParam(
            name=name,
            type_name=type_name,
            description=desc,
            default=default_val,
            optional=optional or (default_val is not None),
            is_required=is_required,
            raw_entry=raw_entry,
        )


    def _parse_return_term(
        self, term_text: str, desc_text: str, raw_entry: Any = None
    ) -> DocstringReturn:
        clean_term = term_text.strip()
        match = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", clean_term)
        if match:
            name_part, type_part = match.groups()
            return DocstringReturn(
                name=name_part.strip().strip("`").strip() or None,
                type_name=type_part.strip().strip("`").strip() or None,
                description=desc_text.strip(),
                raw_entry=raw_entry,
            )

        clean = clean_term.strip("`").strip()
        # Check if desc starts with (type)
        desc = desc_text.strip()
        type_match = re.match(r"^\s*\(([^)]+)\)\s*(?:[-:]\s*)?(.*)$", desc, re.DOTALL)
        if type_match:
            raw_type, rem = type_match.groups()
            return DocstringReturn(
                name=clean if clean else None,
                type_name=raw_type.strip().strip("`").strip() or None,
                description=rem.strip(),
                raw_entry=raw_entry,
            )

        return DocstringReturn(
            name=None,
            type_name=clean if clean else None,
            description=desc,
            raw_entry=raw_entry,
        )

    def _parse_raise_term(
        self, term_text: str, desc_text: str, raw_entry: Any = None
    ) -> DocstringRaise:
        clean_term = term_text.strip().strip("`").strip()
        return DocstringRaise(
            type_name=clean_term,
            description=desc_text.strip(),
            raw_entry=raw_entry,
        )

    def _parse_yield_term(
        self, term_text: str, desc_text: str, raw_entry: Any = None
    ) -> DocstringYield:
        clean_term = term_text.strip()
        match = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", clean_term)
        if match:
            name_part, type_part = match.groups()
            return DocstringYield(
                name=name_part.strip().strip("`").strip() or None,
                type_name=type_part.strip().strip("`").strip() or None,
                description=desc_text.strip(),
                raw_entry=raw_entry,
            )

        clean = clean_term.strip("`").strip()
        # Check if desc starts with (type)
        desc = desc_text.strip()
        type_match = re.match(r"^\s*\(([^)]+)\)\s*(?:[-:]\s*)?(.*)$", desc, re.DOTALL)
        if type_match:
            raw_type, rem = type_match.groups()
            return DocstringYield(
                name=clean if clean else None,
                type_name=raw_type.strip().strip("`").strip() or None,
                description=rem.strip(),
                raw_entry=raw_entry,
            )

        return DocstringYield(
            name=None,
            type_name=clean if clean else None,
            description=desc,
            raw_entry=raw_entry,
        )

    def _parse_receive_term(
        self, term_text: str, desc_text: str, raw_entry: Any = None
    ) -> DocstringReceive:
        clean_term = term_text.strip().strip("`").strip()
        return DocstringReceive(
            type_name=clean_term if clean_term else None,
            description=desc_text.strip(),
        )

    def _parse_warn_term(
        self, term_text: str, desc_text: str, raw_entry: Any = None
    ) -> DocstringWarn:
        clean_term = term_text.strip().strip("`").strip()
        return DocstringWarn(
            type_name=clean_term if clean_term else None,
            description=desc_text.strip(),
        )

    def _parse_attr_term(
        self, term_text: str, desc_text: str, raw_entry: Any = None
    ) -> DocstringAttribute:
        param = self._parse_param_term(term_text, desc_text, raw_entry=raw_entry)
        return DocstringAttribute(
            name=param.name,
            type_name=param.type_name,
            description=param.description,
            value=param.default,
            raw_entry=raw_entry,
        )

    def _handle_attribute_role(
        self, name: str, val: str, note: str | None = None
    ) -> None:
        """Process an attribute entry role such as versionadded, deprecated, etc.

        [parameters]
        `name` (str):: Lowercase attribute name.
        `val` (str):: Inline attribute value.
        `note` (str | None, optional):: Optional contiguous block note.
        """
        if name in ("versionadded", "versionchanged", "deprecated", "experimental"):
            if self._leading_paragraphs:
                self._seen_semantic_block = True

        if name == "versionadded":
            parts = val.split(None, 1)
            version = parts[0] if parts else ""
            inline_note = parts[1] if len(parts) > 1 else None
            self.version_added = VersionDoc(
                version=version, note=_combine_notes(inline_note, note)
            )

        elif name == "versionchanged":
            parts = val.split(None, 1)
            version = parts[0] if parts else ""
            inline_note = parts[1] if len(parts) > 1 else None
            self.version_changed.append(
                VersionDoc(version=version, note=_combine_notes(inline_note, note))
            )

        elif name == "deprecated":
            parts = val.split(None, 1)
            since = parts[0] if parts else ""
            inline_note = parts[1] if len(parts) > 1 else None
            full_note = _combine_notes(inline_note, note)
            replacement = _extract_replacement(full_note) if full_note else None
            self.deprecated_role = DeprecationDoc(
                since=since,
                replacement=replacement,
                note=full_note,
            )

        elif name == "experimental":
            if val == "!" or val.lower() in ("false", "no", "off"):
                self.is_experimental = False
            else:
                self.is_experimental = True

    def _process_blocks(self, blocks: list[Any], **kwargs: Any) -> None:
        """Process blocks, associating contiguous notes with attribute entries.

        [parameters]
        `blocks` (list[Any]):: Block AST nodes to traverse.
        `kwargs` (Any):: Forwarded keyword arguments.
        """
        consumed_indices: set[int] = set()
        for i, block in enumerate(blocks):
            if i in consumed_indices:
                continue
            if getattr(block, "name", "") == "attribute_entry" or isinstance(
                block, AttributeEntry
            ):
                name = getattr(block, "attribute_name", "").lower()
                val = str(getattr(block, "value", "") or "").strip()
                note: str | None = None
                if (
                    name in ("versionadded", "versionchanged", "deprecated")
                    and i + 1 < len(blocks)
                ):
                    next_block = blocks[i + 1]
                    if getattr(next_block, "name", "") == "paragraph" and isinstance(
                        next_block, Paragraph
                    ):
                        loc_attr = getattr(block, "location", None)
                        loc_next = getattr(next_block, "location", None)
                        is_contiguous = bool(
                            loc_attr
                            and loc_next
                            and loc_next[0]["line"] == loc_attr[-1]["line"] + 1
                        )
                        if is_contiguous:
                            consumed_indices.add(i + 1)
                            note = self._get_node_text(next_block).strip()
                self._handle_attribute_role(name, val, note)
            else:
                self.visit(block, **kwargs)

    def generic_visit(self, node: Node, **kwargs: Any) -> Any:
        """Traverse child collections, handling attribute entries and blocks."""
        for coll_name, coll in node.get_child_collections().items():
            if coll_name == "blocks":
                self._process_blocks(coll, **kwargs)
            else:
                for child in coll:
                    self.visit(child, **kwargs)


    def visit_attribute_entry(self, node: Any) -> None:
        """Visit an individual AttributeEntry node."""
        name = getattr(node, "attribute_name", "").lower()
        val = str(getattr(node, "value", "") or "").strip()
        self._handle_attribute_role(name, val, None)

    def _parse_deprecated_block(self, text: str) -> DocstringDeprecated:
        version = None
        match = re.search(r"version\s+([0-9a-zA-Z._-]+)", text, re.IGNORECASE)
        if match:
            version = match.group(1).rstrip(".,;:").strip()
        reason = text.strip()
        return DocstringDeprecated(version=version, reason=reason)

    def visit_paragraph(self, node: Paragraph) -> None:
        """Visit a paragraph node to extract deprecations and leading summaries.

        [parameters]
        `node` (Paragraph):: Paragraph node to inspect and extract.
        """
        role = self._get_block_role(node) or self._current_role
        if role == "deprecated":
            self._seen_semantic_block = True
            text = self._get_node_text(node)
            self.deprecated = self._parse_deprecated_block(text)
            return

        was_seen = self._seen_semantic_block
        raw_text = self._get_node_text(node)
        lines = raw_text.splitlines()
        remaining_lines: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            attr_match = re.match(
                r"^:(!)?([a-zA-Z0-9_-]+)(!)?:(?:\s*(.*))?$", stripped
            )
            if attr_match:
                is_negated = bool(attr_match.group(1) or attr_match.group(3))
                attr_name = attr_match.group(2).lower()
                attr_val = "!" if is_negated else (attr_match.group(4) or "").strip()
                note_parts: list[str] = []
                if attr_name in ("versionadded", "versionchanged", "deprecated"):
                    while i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if re.match(r"^:(!)?([a-zA-Z0-9_-]+)(!)?:", next_line):
                            break
                        note_parts.append(next_line)
                        i += 1
                note = " ".join(note_parts) if note_parts else None
                self._handle_attribute_role(attr_name, attr_val, note)
            else:
                remaining_lines.append(line)
            i += 1

        text = "\n".join(remaining_lines).strip()
        if not was_seen and text:
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
                    self.parameters.append(
                        self._parse_param_term(term_text, desc_text, raw_entry=item)
                    )
                elif role == "returns":
                    self.returns.append(
                        self._parse_return_term(term_text, desc_text, raw_entry=item)
                    )
                elif role == "yields":
                    self.yields.append(
                        self._parse_yield_term(term_text, desc_text, raw_entry=item)
                    )
                elif role == "raises":
                    self.raises.append(
                        self._parse_raise_term(term_text, desc_text, raw_entry=item)
                    )
                elif role == "receives":
                    self.receives.append(
                        self._parse_receive_term(term_text, desc_text, raw_entry=item)
                    )
                elif role == "warns":
                    self.warns.append(
                        self._parse_warn_term(term_text, desc_text, raw_entry=item)
                    )
                elif role == "attributes":
                    self.attributes.append(
                        self._parse_attr_term(term_text, desc_text, raw_entry=item)
                    )
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
        line_number = 1
        if hasattr(node, "location") and node.location:
            line_number = node.location[0].get("line", 1)
        if style == "source" or node.name == "listing" or "test" in attrs:
            self.examples.append(
                DocstringExample(
                    content=content,
                    language=lang,
                    line_number=line_number,
                    is_interactive=">>> " in content,
                    attributes=attrs,
                )
            )

