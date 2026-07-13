import inspect
from typing import Any, List

from asciidoctrine.lark_parser import parse_to_ast

from .visitors import ReSTSerializerVisitor, TestBlock, TestBlockExtractorVisitor


class AsciiDocStringDocument:
    """The main interface representing a parsed AsciiDoc docstring."""
    
    def __init__(self, raw_source: str):
        self.raw_source = raw_source
        self.clean_source = self._clean(raw_source)
        self.ast = self._parse(self.clean_source)

    def _clean(self, source: str) -> str:
        """Strip common leading indentation from docstrings."""
        return inspect.cleandoc(source)

    def _parse(self, source: str) -> Any:
        """Parse cleaned AsciiDoc using asciidoctrine's Lark parser."""
        try:
            return parse_to_ast(source)
        except Exception as e:
            # Re-raise standard parser errors transparently or wrap them if needed
            raise ValueError(f"AsciiDoc Parse Error: {e}") from e

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
