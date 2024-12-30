from dataclasses import dataclass

from dataclass_wizard import JSONWizard


# noinspection PyCompatibility
def test_union_as_type_alias_recursive():
    """
    Recursive or self-referential `Union` (defined as `TypeAlias`)
    types are supported.
    """
    type JSON = str | int | float | bool | dict[str, JSON] | list[JSON] | None

    @dataclass
    class MyTestClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        name: str
        meta: str
        msg: JSON

    x = MyTestClass.from_dict(
        {
            "name": "name",
            "meta": "meta",
            "msg": [{"x": {"x": [{"x": ["x", 1, 1.0, True, None]}]}}],
        }
    )
    assert x == MyTestClass(
        name="name",
        meta="meta",
        msg=[{"x": {"x": [{"x": ["x", 1, 1.0, True, None]}]}}],
    )
