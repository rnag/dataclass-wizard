from dataclasses import dataclass, is_dataclass
from dataclass_wizard import JSONWizard


def test_jsonwizard_is_not_a_dataclass_mixin():
    # If JSONWizard becomes a dataclass again, frozen subclasses can break.
    assert not is_dataclass(JSONWizard)


def test_v1_frozen_dataclass_can_inherit_from_jsonwizard():
    @dataclass(eq=False, frozen=True)
    class BaseClass(JSONWizard):
        class _(JSONWizard.Meta):
            v1 = True

        x: int = 1

    obj = BaseClass()
    assert obj.x == 1


def test_frozen_dataclass_can_inherit_from_jsonwizard():
    @dataclass(eq=False, frozen=True)
    class BaseClass(JSONWizard):
        x: int = 1

    obj = BaseClass()
    assert obj.x == 1
