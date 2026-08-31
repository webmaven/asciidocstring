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
    TestBlock,
)
from .visitors import ReSTSerializerVisitor, TestBlockExtractorVisitor

if TYPE_CHECKING:
    from .semantics import SemanticExtractorVisitor


class AsciiDocStringParseError(ValueError):
    """Raised when parsing of an AsciiDoc docstring fails.

    [attributes]
    `line` (int, optional)::
        Line number where the syntax error occurred. Defaults to `None`.
    `column` (int, optional)::
        Column offset where the error occurred. Defaults to `None`.
    `context` (str, optional)::
        Contextual source snippet around the error. Defaults to `None`.
    """

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
    """Warning issued when docstring parsing fails while running under `safe_mode`.

    Enables non-fatal parsing recovery and diagnostics during safe-mode execution.
    """


class AsciiDocStringDocument:
    """Primary interface representing a parsed AsciiDoc docstring document.

    Provides access to the underlying Abstract Semantic Graph (ASG) AST,
    structured semantic models (parameters, returns, exceptions, yields,
    and attributes), reStructuredText rendering, and doctest extraction.

    [source,python]
    ----
    import asciidocstring

    doc = asciidocstring.parse('''
        Compute the sum of two integers.

        [parameters]
        `a` (int):: The first integer operand.
        `b` (int):: The second integer operand.

        [returns]
        `int`:: Sum of `a` and `b`.
    ''')
    assert doc.summary == "Compute the sum of two integers."
    assert len(doc.parameters) == 2
    ----
    """

    def __init__(self, raw_source: str, safe_mode: bool = False):
        """Initialize and parse an AsciiDoc docstring document.

        [parameters]
        `raw_source` (str)::
            Raw docstring text, potentially with leading indentation.
        `safe_mode` (bool, optional)::
            If `True`, catch parse errors and emit warnings instead of raising.
            Defaults to `False`.

        [raises]
        `AsciiDocStringParseError`::
            If parsing fails and `safe_mode` is `False`.
        """
        self.raw_source = raw_source
        self.safe_mode = safe_mode
        self._semantics_cache: Any = None
        self._parse_failed: bool = False
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

    def __repr__(self) -> str:
        status = "parse_failed" if self._parse_failed else "valid"
        return f"<AsciiDocStringDocument status={status!r} summary={self.summary!r}>"

    def __str__(self) -> str:
        return self.clean_source

    def _clean(self, source: str) -> str:
        """Strip common leading indentation from docstrings."""
        return inspect.cleandoc(source)

    def _parse(self, source: str) -> Any:
        """Parse cleaned AsciiDoc using asciidoctrine's Lark parser."""
        return parse_to_ast(source)

    def _handle_parse_error(self, err: AsciiDocStringParseError) -> None:
        """Emit warning and fall back to careted admonition warning."""
        self._parse_failed = True
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
        """Render parsed ASG into standard reStructuredText.

        [source,python]
        ----
        doc = asciidocstring.parse("A simple docstring.")
        rest_output = doc.to_rest()
        assert "A simple docstring." in rest_output
        ----

        [returns]
        `str`:: Serialized reStructuredText representation for Sphinx and docutils.
        """
        visitor = ReSTSerializerVisitor()
        return visitor.serialize(self.ast)

    def extract_tests(
        self, language: str = "python", requires_test_marker: bool = False
    ) -> List[TestBlock]:
        """Extract executable code blocks from the parsed AST.

        [parameters]
        `language` (str, optional)::
            Programming language filter for listing blocks. Defaults to `"python"`.
        `requires_test_marker` (bool, optional)::
            When `True`, only extract code blocks tagged with
            `[source,python,test]` or `[.test]`. Defaults to `False`.

        [returns]
        `list[TestBlock]`::
            Extracted test blocks with code content, line numbers, and flags.
        """
        visitor = TestBlockExtractorVisitor(language, requires_test_marker)
        return visitor.extract(self.ast)

    @property
    def semantics(self) -> "SemanticExtractorVisitor":
        """Semantic extractor visitor holding all parsed docstring models.

        [returns]
        `SemanticExtractorVisitor`::
            The visitor containing populated semantic collections.
        """
        if self._semantics_cache is None:
            from .semantics import SemanticExtractorVisitor

            visitor = SemanticExtractorVisitor()
            if not self._parse_failed:
                visitor.extract(self.ast)
            self._semantics_cache = visitor
        return self._semantics_cache  # type: ignore[no-any-return]

    @property
    def summary(self) -> str:
        """One-line summary extracted as the first paragraph of the docstring.

        [returns]
        `str`:: The first paragraph text, or an empty string if parse failed.
        """
        if self._parse_failed:
            return ""
        return self.semantics.summary

    @property
    def description(self) -> str:
        """Full extended description of the docstring.

        [returns]
        `str`:: Leading description paragraphs, or an empty string if parse failed.
        """
        if self._parse_failed:
            return ""
        return self.semantics.description

    @property
    def parameters(self) -> list[DocstringParam]:
        """List of documented parameters extracted from the docstring.

        [returns]
        `list[DocstringParam]`:: Documented parameters with names, types, and defaults.
        """
        if self._parse_failed:
            return []
        return self.semantics.parameters

    @property
    def returns(self) -> list[DocstringReturn]:
        """List of documented return value specifications.

        [returns]
        `list[DocstringReturn]`:: Return value annotations and descriptions.
        """
        if self._parse_failed:
            return []
        return self.semantics.returns

    @property
    def yields(self) -> list[DocstringYield]:
        """List of documented yield value specifications.

        [returns]
        `list[DocstringYield]`:: Generator yield specifications.
        """
        if self._parse_failed:
            return []
        return self.semantics.yields

    @property
    def raises(self) -> list[DocstringRaise]:
        """List of documented exceptions that may be raised.

        [returns]
        `list[DocstringRaise]`:: Exception types and trigger conditions.
        """
        if self._parse_failed:
            return []
        return self.semantics.raises

    @property
    def receives(self) -> list[DocstringReceive]:
        """List of documented generator receive specifications.

        [returns]
        `list[DocstringReceive]`:: Generator receive types and descriptions.
        """
        if self._parse_failed:
            return []
        return self.semantics.receives

    @property
    def warns(self) -> list[DocstringWarn]:
        """List of documented warnings that may be issued.

        [returns]
        `list[DocstringWarn]`:: Warning categories and trigger descriptions.
        """
        if self._parse_failed:
            return []
        return self.semantics.warns

    @property
    def attributes(self) -> list[DocstringAttribute]:
        """List of documented class or module attributes.

        [returns]
        `list[DocstringAttribute]`:: Attributes with names, types, and descriptions.
        """
        if self._parse_failed:
            return []
        return self.semantics.attributes

    @property
    def examples(self) -> list[DocstringExample]:
        """List of example and test code blocks extracted from the docstring.

        [returns]
        `list[DocstringExample]`:: Source code example blocks.
        """
        if self._parse_failed:
            return []
        return self.semantics.examples

    @property
    def deprecated(self) -> DocstringDeprecated | None:
        """Deprecation notice if present, otherwise None.

        [returns]
        `DocstringDeprecated | None`::
            Deprecation notice with version and reason, or `None`.
        """
        if self._parse_failed:
            return None
        return self.semantics.deprecated


def parse(docstring: str, safe_mode: bool = False) -> AsciiDocStringDocument:
    """Parse a raw Python docstring written in AsciiDoc.

    Convenience entrypoint that cleans leading docstring indentation, parses
    the AsciiDoc markup into an AST, and prepares semantic extractors.

    [source,python]
    ----
    import asciidocstring

    doc = asciidocstring.parse('''
        Calculate hypotenuse length.

        [parameters]
        `a` (float):: First side length.
        `b` (float):: Second side length.

        [returns]
        `float`:: Hypotenuse length.
    ''')
    assert doc.summary == "Calculate hypotenuse length."
    ----

    [parameters]
    `docstring` (str)::
        Raw docstring string to clean and parse.
    `safe_mode` (bool, optional)::
        If `True`, catch parse errors and emit warnings instead of raising.
        Defaults to `False`.

    [returns]
    `AsciiDocStringDocument`::
        Parsed document representation ready for querying.

    [raises]
    `AsciiDocStringParseError`::
        If syntax or parsing fails and `safe_mode` is `False`.
    """
    return AsciiDocStringDocument(docstring, safe_mode=safe_mode)
