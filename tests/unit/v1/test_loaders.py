import pytest

from dataclasses import dataclass

from dataclass_wizard import JSONWizard
from dataclass_wizard.errors import MissingFields


def test_missing_fields_is_raised():

    @dataclass
    class Test(JSONWizard, debug=True):
        class _(JSONWizard.Meta):
            v1 = True

        my_str: str
        my_int: int
        my_bool: bool
        my_float: float = 1.23


    with pytest.raises(MissingFields) as exc_info:
        _ = Test.from_dict({'my_bool': True})

    e, tp = exc_info.value, exc_info.type

    assert tp is MissingFields
    assert e.fields == ['my_bool']
    assert e.missing_fields == ['my_str', 'my_int']


def test_auto_key_casing():

    @dataclass
    class Test(JSONWizard):
        class _(JSONWizard.Meta):
            v1 = True
            v1_key_case = 'AUTO'

        my_str: str
        my_bool_test: bool
        my_int: int
        my_float: float = 1.23

    d = {'My-Str': 'test', 'myBoolTest': True, 'MyInt': 123, 'my_float': 42, }

    assert Test.from_dict(d) == Test(my_str='test', my_bool_test=True, my_int=123, my_float=42.0)
