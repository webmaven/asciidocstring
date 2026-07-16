import inspect
import warnings
from typing import Any, List

from asciidoctrine import AsciiDocSyntaxError
from asciidoctrine.lark_parser import parse_to_ast

from .visitors import ReSTSerializerVisitor, TestBlock, TestBlockExtractorVisitor


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


def parse(docstring: str, safe_mode: bool = False) -> AsciiDocStringDocument:
    """Convenience function to parse a raw python docstring."""
    return AsciiDocStringDocument(docstring, safe_mode=safe_mode)
