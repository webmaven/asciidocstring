"""Document parser and primary AsciiDocStringDocument interface."""

import inspect
import warnings
from typing import TYPE_CHECKING, Any, List

from asciidoctrine import AsciiDocSyntaxError
from asciidoctrine.lark_parser import parse_to_ast

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
from .visitors import ReSTSerializerVisitor, TestBlock, TestBlockExtractorVisitor

if TYPE_CHECKING:
    from .semantics import SemanticExtractorVisitor


class AsciiDocStringParseError(ValueError):
    """Raised when parsing of an AsciiDoc docstring fails."""

    def __init__(
        self,
        message: str,
        line: int | None = None,
        column: int | None = None,
        context: str | None = None,
    ):
        super().__init__(message)
        self.line = line
        self.column = column
        self.context = context


class AsciiDocStringWarning(UserWarning):
    """Warning raised when parsing of an AsciiDoc docstring fails under safe-mode."""


class AsciiDocStringDocument:
    """The main interface representing a parsed AsciiDoc docstring."""

    def __init__(self, raw_source: str, safe_mode: bool = False):
        self.raw_source = raw_source
        self.safe_mode = safe_mode
        self._semantics_cache: Any = None
        try:
            self.clean_source = self._clean(raw_source)
            self.ast = self._parse(self.clean_source)
        except AsciiDocSyntaxError as e:
            self.clean_source = getattr(self, "clean_source", str(raw_source))
            err = AsciiDocStringParseError(
                f"AsciiDoc Parse Error: {e.args[0] if e.args else str(e)}",
                line=e.line,
                column=e.column,
                context=e.context,
            )
            if self.safe_mode:
                self._handle_parse_error(err)
            else:
                raise err from e
        except Exception as e:
            self.clean_source = getattr(self, "clean_source", str(raw_source))
            err = AsciiDocStringParseError(f"AsciiDoc Parse Error: {e}")
            if self.safe_mode:
                self._handle_parse_error(err)
            else:
                raise err from e

    def _clean(self, source: str) -> str:
        """Strip common leading indentation from docstrings."""
        return inspect.cleandoc(source)

    def _parse(self, source: str) -> Any:
        """Parse cleaned AsciiDoc using asciidoctrine's Lark parser."""
        return parse_to_ast(source)

    def _handle_parse_error(self, err: AsciiDocStringParseError) -> None:
        """Emit warning and fall back to careted admonition warning."""
        warnings.warn(str(err), AsciiDocStringWarning, stacklevel=3)

        # Build clean source with caret pointing to syntax error if available
        source_with_caret = self.clean_source
        if err.line is not None and err.column is not None:
            lines = self.clean_source.splitlines()
            if 1 <= err.line <= len(lines):
                col_idx = max(0, err.column - 1)
                caret_line = " " * col_idx + "^"
                lines.insert(err.line, caret_line)
                source_with_caret = "\n".join(lines)

        from asciidoctrine.nodes import Admonition, Document, Listing, Paragraph, Text

        self.ast = Document(
            blocks=[
                Admonition(
                    variant="warning",
                    blocks=[
                        Paragraph(
                            inlines=[
                                Text(value=f"Failed to parse AsciiDoc docstring: {err}")
                            ]
                        ),
                        Listing(
                            inlines=[Text(value=source_with_caret)],
                            attributes={"language": "asciidoc"},
                        ),
                    ],
                )
            ]
        )

    def to_rest(self) -> str:
        """Render parsed ASG into standard reStructuredText."""
        visitor = ReSTSerializerVisitor()
        return visitor.serialize(self.ast)

    def extract_tests(
        self, language: str = "python", requires_test_marker: bool = False
    ) -> List[TestBlock]:
        """Extract executable code blocks from the parsed AST."""
        visitor = TestBlockExtractorVisitor(language, requires_test_marker)
        return visitor.extract(self.ast)

    @property
    def semantics(self) -> "SemanticExtractorVisitor":
        """Semantic extractor visitor holding all parsed docstring models."""
        if self._semantics_cache is None:
            from .semantics import SemanticExtractorVisitor

            visitor = SemanticExtractorVisitor()
            self._semantics_cache = visitor.extract(self.ast)
        return self._semantics_cache  # type: ignore[no-any-return]

    @property
    def summary(self) -> str:
        """One-line summary (the first paragraph of the docstring)."""
        return self.semantics.summary

    @property
    def description(self) -> str:
        """Full extended description of the docstring."""
        return self.semantics.description

    @property
    def parameters(self) -> list[DocstringParam]:
        """List of documented parameters extracted from the docstring."""
        return self.semantics.parameters

    @property
    def returns(self) -> list[DocstringReturn]:
        """List of documented return value specifications."""
        return self.semantics.returns

    @property
    def yields(self) -> list[DocstringYield]:
        """List of documented yield value specifications."""
        return self.semantics.yields

    @property
    def raises(self) -> list[DocstringRaise]:
        """List of documented exceptions that may be raised."""
        return self.semantics.raises

    @property
    def receives(self) -> list[DocstringReceive]:
        """List of documented generator receive specifications."""
        return self.semantics.receives

    @property
    def warns(self) -> list[DocstringWarn]:
        """List of documented warnings that may be issued."""
        return self.semantics.warns

    @property
    def attributes(self) -> list[DocstringAttribute]:
        """List of documented class or module attributes."""
        return self.semantics.attributes

    @property
    def examples(self) -> list[DocstringExample]:
        """List of example and test code blocks extracted from the docstring."""
        return self.semantics.examples

    @property
    def deprecated(self) -> DocstringDeprecated | None:
        """Deprecation notice if present, otherwise None."""
        return self.semantics.deprecated


def parse(docstring: str, safe_mode: bool = False) -> AsciiDocStringDocument:
    """Convenience function to parse a raw python docstring."""
    return AsciiDocStringDocument(docstring, safe_mode=safe_mode)

