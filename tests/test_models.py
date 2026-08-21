from asciidocstring.models import (
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


def test_docstring_models_instantiation() -> None:
    param = DocstringParam(
        name="x",
        type_name="int",
        description="The initial count.",
        default="0",
        optional=False,
    )
    assert param.name == "x"
    assert param.type_name == "int"
    assert param.description == "The initial count."
    assert param.default == "0"
    assert not param.optional

    ret = DocstringReturn(
        type_name="bool",
        description="True if successful.",
        name="status",
    )
    assert ret.type_name == "bool"
    assert ret.description == "True if successful."
    assert ret.name == "status"

    yld = DocstringYield(
        type_name="str",
        description="Streamed chunks.",
    )
    assert yld.type_name == "str"
    assert yld.description == "Streamed chunks."
    assert yld.name is None

    exc = DocstringRaise(
        type_name="ValueError",
        description="If x is negative.",
    )
    assert exc.type_name == "ValueError"
    assert exc.description == "If x is negative."

    rec = DocstringReceive(
        type_name="int",
        description="Value received via send().",
    )
    assert rec.type_name == "int"
    assert rec.description == "Value received via send()."

    wrn = DocstringWarn(
        type_name="UserWarning",
        description="If deprecated feature is used.",
    )
    assert wrn.type_name == "UserWarning"
    assert wrn.description == "If deprecated feature is used."

    attr = DocstringAttribute(
        name="cache",
        type_name="dict",
        description="Internal caching dictionary.",
        value="{}",
    )
    assert attr.name == "cache"
    assert attr.type_name == "dict"
    assert attr.value == "{}"

    dep = DocstringDeprecated(
        version="1.2.0",
        reason="Use new_api() instead.",
    )
    assert dep.version == "1.2.0"
    assert dep.reason == "Use new_api() instead."

    ex = DocstringExample(
        content=">>> add(1, 2)\n3",
        language="python",
        line_number=10,
        is_interactive=True,
        attributes={"test": True},
    )
    assert ex.content == ">>> add(1, 2)\n3"
    assert ex.is_interactive
    assert ex.attributes == {"test": True}
