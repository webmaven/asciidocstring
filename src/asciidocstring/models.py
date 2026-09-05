"""Semantic data models for parsed AsciiDoc docstrings."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DocstringParam:
    """Represent a documented function, method, or class parameter.

    [attributes]
    `name` (str):: Name of the parameter.
    `type_name` (str, optional)::
        Optional type annotation string. Defaults to `None`.
    `description` (str)::
        Text description of the parameter. Defaults to `""`.
    `default` (str, optional)::
        Optional default value representation string. Defaults to `None`.
    `optional` (bool)::
        Whether the parameter is marked optional. Defaults to `False`.
    `raw_entry` (Any, optional)::
        Optional raw parsed AST node or term reference. Defaults to `None`.
    """

    name: str
    type_name: str | None = None
    description: str = ""
    default: str | None = None
    optional: bool = False
    raw_entry: Any | None = None


@dataclass
class DocstringReturn:
    """Represent a return value specification.

    [attributes]
    `type_name` (str, optional)::
        Optional type annotation string of the return value. Defaults to `None`.
    `description` (str)::
        Text description of the return value. Defaults to `""`.
    `name` (str, optional)::
        Optional identifier or label for the return value. Defaults to `None`.
    `raw_entry` (Any, optional)::
        Optional raw parsed AST node or term reference. Defaults to `None`.
    """

    type_name: str | None = None
    description: str = ""
    name: str | None = None
    raw_entry: Any | None = None


@dataclass
class DocstringYield:
    """Represent a yield value specification.

    [attributes]
    `type_name` (str, optional)::
        Optional type annotation string of the yield value. Defaults to `None`.
    `description` (str)::
        Text description of the yield value. Defaults to `""`.
    `name` (str, optional)::
        Optional identifier or label for the yield value. Defaults to `None`.
    `raw_entry` (Any, optional)::
        Optional raw parsed AST node or term reference. Defaults to `None`.
    """

    type_name: str | None = None
    description: str = ""
    name: str | None = None
    raw_entry: Any | None = None


@dataclass
class DocstringRaise:
    """Represent a documented exception that may be raised.

    [attributes]
    `type_name` (str):: Exception class or type name.
    `description` (str)::
        Circumstances under which the exception is raised. Defaults to `""`.
    `raw_entry` (Any, optional)::
        Optional raw parsed AST node or term reference. Defaults to `None`.
    """

    type_name: str
    description: str = ""
    raw_entry: Any | None = None


@dataclass
class DocstringReceive:
    """Represent a generator receive specification.

    [attributes]
    `type_name` (str, optional)::
        Optional type annotation string of the received value. Defaults to `None`.
    `description` (str)::
        Text description of the received value. Defaults to `""`.
    """

    type_name: str | None = None
    description: str = ""


@dataclass
class DocstringWarn:
    """Represent a warning that may be issued.

    [attributes]
    `type_name` (str, optional)::
        Optional warning category or class name. Defaults to `None`.
    `description` (str)::
        Circumstances under which the warning is issued. Defaults to `""`.
    """

    type_name: str | None = None
    description: str = ""


@dataclass
class DocstringAttribute:
    """Represent a class or module attribute.

    [attributes]
    `name` (str):: Name of the attribute.
    `type_name` (str, optional)::
        Optional type annotation string. Defaults to `None`.
    `description` (str)::
        Text description of the attribute. Defaults to `""`.
    `value` (str, optional)::
        Optional initial or default value. Defaults to `None`.
    `raw_entry` (Any, optional)::
        Optional raw parsed AST node or term reference. Defaults to `None`.
    """

    name: str
    type_name: str | None = None
    description: str = ""
    value: str | None = None
    raw_entry: Any | None = None


@dataclass
class DocstringDeprecated:
    """Represent a deprecation notice.

    [attributes]
    `version` (str, optional)::
        Version in which the feature was or will be deprecated. Defaults to `None`.
    `reason` (str)::
        Explanation or migration guidance for the deprecation. Defaults to `""`.
    """

    version: str | None = None
    reason: str = ""


@dataclass
class DocstringExample:
    """Represent an example or test code block.

    [attributes]
    `content` (str):: Code contents of the example block.
    `language` (str, optional)::
        Programming or markup language of the block. Defaults to `"python"`.
    `line_number` (int, optional)::
        Starting line number of the block in the docstring. Defaults to `1`.
    `is_interactive` (bool, optional)::
        True if the code block contains interactive `>>>` prompts. Defaults to `False`.
    `attributes` (dict[str, Any], optional)::
        Dictionary of raw block attributes from the AsciiDoc AST. Defaults to `{}`.
    """

    content: str
    language: str = "python"
    line_number: int = 1
    is_interactive: bool = False
    attributes: dict[str, Any] = field(default_factory=dict)


# Harmonize TestBlock and DocstringExample
TestBlock = DocstringExample
