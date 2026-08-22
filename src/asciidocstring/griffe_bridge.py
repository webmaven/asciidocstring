"""Bridge for ingesting and converting Griffe docstring sections."""

from typing import TYPE_CHECKING, Any, Literal, Sequence, Union

from .document import AsciiDocStringDocument, parse

if TYPE_CHECKING:
    import griffe


def to_asciidoc(sections: Sequence[Union["griffe.DocstringSection", Any]]) -> str:
    """Convert a list of Griffe DocstringSection objects into clean AsciiDoc markup.

    Args:
        sections: A list of Griffe `DocstringSection` instances.

    Returns:
        A string containing formatted AsciiDoc markup representing the sections.
    """
    blocks: list[str] = []


    for section in sections:
        kind = getattr(section, "kind", None)
        kind_value = getattr(kind, "value", str(kind))

        if kind_value == "text":
            text = str(getattr(section, "value", "")).strip()
            if text:
                blocks.append(text)

        elif kind_value in (
            "parameters", "other parameters", "other_parameters", "attributes"
        ):
            # Normalise "other parameters" (griffe's canonical name) to
            # "other_parameters"
            label = "other_parameters" if "other" in kind_value else kind_value
            items = getattr(section, "value", [])
            if not items:
                continue
            lines = [f"[{label}]"]
            for param in items:
                name = getattr(param, "name", "")
                annotation = getattr(param, "annotation", None)
                desc = getattr(param, "description", "")
                default = getattr(param, "value", None)

                type_parts = []
                if annotation:
                    type_parts.append(str(annotation))
                if default is not None and label != "attributes":
                    type_parts.append("optional")

                type_str = f"({', '.join(type_parts)}) " if type_parts else ""
                default_str = (
                    f" Defaults to `{default}`."
                    if default is not None and label != "attributes"
                    else ""
                )

                lines.append(f"`{name}`:: {type_str}{desc}{default_str}")
            blocks.append("\n".join(lines))

        elif kind_value in ("returns", "yields", "raises", "receives", "warns"):
            items = getattr(section, "value", [])
            if not items:
                continue
            lines = [f"[{kind_value}]"]
            for obj in items:
                name = getattr(obj, "name", "")
                annotation = getattr(obj, "annotation", None)
                desc = getattr(obj, "description", "")
                type_name = str(annotation) if annotation else name or "object"
                lines.append(f"`{type_name}`:: {desc}")
            blocks.append("\n".join(lines))

        elif kind_value == "examples":
            items = getattr(section, "value", [])
            if not items:
                continue
            for item in items:
                if isinstance(item, tuple) and len(item) == 2:
                    _, example_code = item
                else:
                    example_code = str(item)
                code_block = (
                    "[source,python,test]\n----\n"
                    + example_code.strip()
                    + "\n----"
                )
                blocks.append(code_block)

        elif kind_value == "deprecated":
            # section.value is a DocstringDeprecated with .version and .description
            val = getattr(section, "value", None)
            version = getattr(val, "version", None) or ""
            desc = getattr(val, "description", None) or str(val)
            ver_str = f" in version {version}" if version else ""
            blocks.append(f"[deprecated]\n====\nDeprecated{ver_str}: {desc}\n====")

        elif kind_value == "admonition":
            # section.value is a DocstringAdmonition with .kind and .description
            val = getattr(section, "value", None)
            adm_kind = str(getattr(val, "kind", None) or "NOTE").upper()
            desc = getattr(val, "description", None) or ""
            blocks.append(f"[{adm_kind}]\n====\n{desc}\n====")

    return "\n\n".join(blocks)


def from_sections(
    sections: Sequence[Union["griffe.DocstringSection", Any]],
) -> AsciiDocStringDocument:
    """Convert Griffe DocstringSection items to an AsciiDocStringDocument.

    Args:
        sections: A sequence of Griffe `DocstringSection` instances.

    Returns:
        An `AsciiDocStringDocument` representing the converted sections.
    """
    adoc_text = to_asciidoc(sections)
    return parse(adoc_text)


def from_griffe(
    docstring: Union["griffe.Docstring", str],
    style: Literal["google", "numpy", "sphinx", "auto"] = "auto",
) -> AsciiDocStringDocument:

    """Parse docstring using Griffe static parser and return AsciiDocStringDocument.

    Args:
        docstring: A raw docstring string or a `griffe.Docstring` instance.
        style: Docstring convention style ("google", "numpy", "sphinx", or "auto").

    Returns:
        An `AsciiDocStringDocument` containing parsed semantic models and AST.

    Raises:
        ImportError: If `griffe` is not installed.
    """
    try:
        import griffe
    except ImportError as e:
        raise ImportError(
            "Griffe is required to use 'from_griffe()'. "
            "Install via 'pip install asciidocstring[griffe]'."
        ) from e

    if not isinstance(docstring, griffe.Docstring):
        docstring_obj = griffe.Docstring(str(docstring))
    else:
        docstring_obj = docstring

    sections = griffe.parse(docstring_obj, style)
    return from_sections(sections)
