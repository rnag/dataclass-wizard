from __future__ import annotations

import logging
import os
from collections import defaultdict
from datetime import datetime
from textwrap import dedent
from typing import ClassVar

import pytest

from dataclass_wizard.errors import MissingVars

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict

from dataclass_wizard import EnvWizard


log = logging.getLogger(__name__)


def test_load_and_dump():
    os.environ.update({
        'hello_world': 'Test',
        'MyStr': 'This STRING',
        'MY_TEST_VALUE123': '11',
        'THIS_Num': '23',
        'my_list': '["1", 2, "3", "4.5", 5.7]',
        'my_other_list': 'rob@test.org, this@email.com , hello-world_123@tst.org,z@ab.c'
    })

    class MyClass(EnvWizard):
        # these are class-level fields, and should be ignored
        my_cls_var: ClassVar[str]
        other_var = 21

        my_str: str
        this_num: int
        my_list: list[int]
        my_other_list: list[str]
        my_test_value123: int = 21
        # missing from environment
        my_field_not_in_env: str = 'testing'

    log.debug(MyClass.dict())

    assert not hasattr(MyClass, 'my_cls_var')
    assert MyClass.other_var == 21

    assert MyClass.my_str == 'This STRING'
    assert MyClass.this_num == 23
    assert MyClass.my_list == [1, 2, 3, 4, 6]
    assert MyClass.my_other_list == ['rob@test.org', 'this@email.com', 'hello-world_123@tst.org', 'z@ab.c']
    assert MyClass.my_test_value123 == 11
    assert MyClass.my_field_not_in_env == 'testing'

    assert MyClass.to_dict() == {
        'my_str': 'This STRING',
        'this_num': 23,
        'my_list': [1, 2, 3, 4, 6],
        'my_other_list': ['rob@test.org',
                          'this@email.com',
                          'hello-world_123@tst.org',
                          'z@ab.c'],
        'my_test_value123': 11,
        'my_field_not_in_env': 'testing',
    }


def test_load_and_dump_with_dict():
    os.environ.update({
        'MY_DICT': '{"123": "True", "5": "false"}',
        'My.Other.Dict': 'some_key=value,  anotherKey=123 ,LastKey=just a test~',
        'My_Default_Dict': '  {  "1.2": "2021-01-02T13:57:21"  }  ',
        'myTypedDict': 'my_bool=true'
    })

    class MyTypedDict(TypedDict):
        my_bool: bool

    # Fix so the forward reference works
    globals().update(locals())

    class ClassWithDict(EnvWizard, reload_env=True):
        class _(EnvWizard.Meta):
            field_to_env_var = {'my_other_dict': 'My.Other.Dict'}

        my_dict: dict[int, bool]
        my_other_dict: dict[str, int | str]
        my_default_dict: defaultdict[float, datetime]
        my_typed_dict: MyTypedDict

    log.debug(ClassWithDict.dict())

    assert ClassWithDict.my_dict == {123: True, 5: False}

    # note that the value for 'anotherKey' is a string value ('123') here,
    # but we might want to see if we can update it to a numeric value (123)
    # instead.
    assert ClassWithDict.my_other_dict == {
        'some_key': 'value',
        'anotherKey': '123',
        'LastKey': 'just a test~',
    }

    assert ClassWithDict.my_default_dict == {1.2: datetime(2021, 1, 2, 13, 57, 21)}
    assert ClassWithDict.my_typed_dict == {'my_bool': True}

    assert ClassWithDict.to_dict() == {
        'my_dict': {5: False, 123: True},
        'my_other_dict': {'LastKey': 'just a test~',
                          'anotherKey': '123',
                          'some_key': 'value'},
        'my_default_dict': {1.2: '2021-01-02T13:57:21'},
        'my_typed_dict': {'my_bool': True}
    }


def test_load_with_missing_env_variables():
    """
    Test loading a `EnvWizard` subclass when the associated vars are missing
    in the Environment.
    """
    with pytest.raises(MissingVars) as e:

        class MyClass(EnvWizard):
            missing_field_1: str
            missing_field_2: datetime
            missing_field_3: dict[str, int]

    assert str(e.value) == dedent("""\
    There are 3 required fields in class `test_load_with_missing_env_variables.<locals>.MyClass` missing in the Environment:
        - missing_field_1
        - missing_field_2
        - missing_field_3

    Resolution: set a default value for any optional fields, as below.

    class test_load_with_missing_env_variables.<locals>.MyClass:
        missing_field_1: str = ''
        missing_field_2: datetime = None
        missing_field_3: dict = {}
    """.rstrip())
