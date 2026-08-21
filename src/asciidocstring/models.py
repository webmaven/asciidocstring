"""Semantic data models for parsed AsciiDoc docstrings."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DocstringParam:
    """Represents a documented function/method/class parameter."""

    name: str
    type_name: str | None = None
    description: str = ""
    default: str | None = None
    optional: bool = False
    raw_entry: Any | None = None


@dataclass
class DocstringReturn:
    """Represents a return value specification."""

    type_name: str | None = None
    description: str = ""
    name: str | None = None


@dataclass
class DocstringYield:
    """Represents a yield value specification."""

    type_name: str | None = None
    description: str = ""
    name: str | None = None


@dataclass
class DocstringRaise:
    """Represents a documented exception that may be raised."""

    type_name: str
    description: str = ""


@dataclass
class DocstringReceive:
    """Represents a generator receive specification."""

    type_name: str | None = None
    description: str = ""


@dataclass
class DocstringWarn:
    """Represents a warning that may be issued."""

    type_name: str | None = None
    description: str = ""


@dataclass
class DocstringAttribute:
    """Represents a class or module attribute."""

    name: str
    type_name: str | None = None
    description: str = ""
    value: str | None = None


@dataclass
class DocstringDeprecated:
    """Represents a deprecation notice."""

    version: str | None = None
    reason: str = ""


@dataclass
class DocstringExample:
    """Represents an example or test block."""

    content: str
    language: str = "python"
    line_number: int = 1
    is_interactive: bool = False
    attributes: dict[str, Any] = field(default_factory=dict)
