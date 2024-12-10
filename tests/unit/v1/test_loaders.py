from typing import Annotated

import pytest

from dataclasses import dataclass

from dataclass_wizard import JSONWizard, Alias
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


def test_alias_mapping():

    # TODO fix bug with `JSONPyWizard`
    @dataclass
    class Test(JSONWizard):
        class _(JSONWizard.Meta):
            v1 = True
            key_transform_with_dump = 'NONE'
            v1_field_to_alias = {'my_int': 'MyInt'}

        my_str: str = Alias('a_str')
        my_bool_test: Annotated[bool, Alias('myBoolTest')]
        my_int: int
        my_float: float = 1.23

    d = {'a_str': 'test', 'myBoolTest': True, 'MyInt': 123, 'my_float': 42}

    t = Test.from_dict(d)
    assert t == Test(my_str='test', my_bool_test=True, my_int=123, my_float=42.0)

    assert t.to_dict() == {'a_str': 'test', 'myBoolTest': True, 'MyInt': 123, 'my_float': 42.0}


def test_alias_mapping_with_load_or_dump():

    @dataclass
    class Test(JSONWizard):
        class _(JSONWizard.Meta):
            v1 = True
            v1_key_case = 'C'
            key_transform_with_dump = 'NONE'
            v1_field_to_alias = {
                'my_int': 'MyInt',
                '__load__': False,
            }

        my_str: str = Alias(load='a_str')
        my_bool_test: Annotated[bool, Alias(dump='myDumpedBool')]
        my_int: int
        other_int: int = Alias(dump='DumpedInt')
        my_float: float = 1.23

    d = {'a_str': 'test',
         'myBoolTest': 'T',
         'myInt': 123,
         'otherInt': 321,
         'myFloat': 42}

    t = Test.from_dict(d)
    assert t == Test(my_str='test',
                     my_bool_test=True,
                     my_int=123,
                     other_int=321,
                     my_float=42.0)

    assert t.to_dict() == {'my_str': 'test',
                           'MyInt': 123,
                           'DumpedInt': 321,
                           'myDumpedBool': True,
                           'my_float': 42.0}
