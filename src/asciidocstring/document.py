import inspect
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


class AsciiDocStringDocument:
    """The main interface representing a parsed AsciiDoc docstring."""
    
    def __init__(self, raw_source: str):
        try:
            self.raw_source = raw_source
            self.clean_source = self._clean(raw_source)
            self.ast = self._parse(self.clean_source)
        except AsciiDocSyntaxError as e:
            raise AsciiDocStringParseError(
                f"AsciiDoc Parse Error: {e}",
                line=e.line,
                column=e.column,
                context=e.context,
            ) from e
        except Exception as e:
            raise AsciiDocStringParseError(f"AsciiDoc Parse Error: {e}") from e

    def _clean(self, source: str) -> str:
        """Strip common leading indentation from docstrings."""
        return inspect.cleandoc(source)

    def _parse(self, source: str) -> Any:
        """Parse cleaned AsciiDoc using asciidoctrine's Lark parser."""
        return parse_to_ast(source)

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

def parse(docstring: str) -> AsciiDocStringDocument:
    """Convenience function to parse a raw python docstring."""
    return AsciiDocStringDocument(docstring)
