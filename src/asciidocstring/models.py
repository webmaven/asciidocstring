"""Semantic data models for parsed AsciiDoc docstrings."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DocstringParam:
    """Represents a documented function, method, or class parameter.

    Attributes:
        name: Name of the parameter.
        type_name: Optional type annotation string.
        description: Text description of the parameter.
        default: Optional default value representation string.
        optional: Whether the parameter is marked optional.
        raw_entry: Optional raw parsed AST node or term reference.
    """

    name: str
    type_name: str | None = None
    description: str = ""
    default: str | None = None
    optional: bool = False
    raw_entry: Any | None = None


@dataclass
class DocstringReturn:
    """Represents a return value specification.

    Attributes:
        type_name: Optional type annotation string of the return value.
        description: Text description of the return value.
        name: Optional identifier or label for the return value.
    """

    type_name: str | None = None
    description: str = ""
    name: str | None = None


@dataclass
class DocstringYield:
    """Represents a yield value specification.

    Attributes:
        type_name: Optional type annotation string of the yield value.
        description: Text description of the yield value.
        name: Optional identifier or label for the yield value.
    """

    type_name: str | None = None
    description: str = ""
    name: str | None = None


@dataclass
class DocstringRaise:
    """Represents a documented exception that may be raised.

    Attributes:
        type_name: Exception class or type name.
        description: Circumstances under which the exception is raised.
    """

    type_name: str
    description: str = ""


@dataclass
class DocstringReceive:
    """Represents a generator receive specification.

    Attributes:
        type_name: Optional type annotation string of the received value.
        description: Text description of the received value.
    """

    type_name: str | None = None
    description: str = ""


@dataclass
class DocstringWarn:
    """Represents a warning that may be issued.

    Attributes:
        type_name: Optional warning category or class name.
        description: Circumstances under which the warning is issued.
    """

    type_name: str | None = None
    description: str = ""


@dataclass
class DocstringAttribute:
    """Represents a class or module attribute.

    Attributes:
        name: Name of the attribute.
        type_name: Optional type annotation string.
        description: Text description of the attribute.
        value: Optional initial or default value.
    """

    name: str
    type_name: str | None = None
    description: str = ""
    value: str | None = None


@dataclass
class DocstringDeprecated:
    """Represents a deprecation notice.

    Attributes:
        version: Version in which the feature was or will be deprecated.
        reason: Explanation or migration guidance for the deprecation.
    """

    version: str | None = None
    reason: str = ""


@dataclass
class DocstringExample:
    """Represents an example or test code block.

    Attributes:
        content: Code contents of the example block.
        language: Programming or markup language of the block (default: "python").
        line_number: Starting line number of the block in the docstring.
        is_interactive: True if the code block contains interactive `>>>` prompts.
        attributes: Dictionary of raw block attributes from the AsciiDoc AST.
    """

    content: str
    language: str = "python"
    line_number: int = 1
    is_interactive: bool = False
    attributes: dict[str, Any] = field(default_factory=dict)
