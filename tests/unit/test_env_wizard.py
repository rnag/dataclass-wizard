import logging
import os
from datetime import datetime, time, date
from pathlib import Path
from textwrap import dedent
from typing import ClassVar, List, Dict, Union, DefaultDict

import pytest

from dataclass_wizard.errors import MissingVars, ParseError

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
        my_list: List[int]
        my_other_list: List[str]
        my_test_value123: int = 21
        # missing from environment
        my_field_not_in_env: str = 'testing'

    e = MyClass()
    log.debug(e.dict())

    assert not hasattr(e, 'my_cls_var')
    assert e.other_var == 21

    assert e.my_str == 'This STRING'
    assert e.this_num == 23
    assert e.my_list == [1, 2, 3, 4, 6]
    assert e.my_other_list == ['rob@test.org', 'this@email.com', 'hello-world_123@tst.org', 'z@ab.c']
    assert e.my_test_value123 == 11
    assert e.my_field_not_in_env == 'testing'

    assert e.to_dict() == {
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

        my_dict: Dict[int, bool]
        my_other_dict: Dict[str, Union[int, str]]
        my_default_dict: DefaultDict[float, datetime]
        my_typed_dict: MyTypedDict

    c = ClassWithDict()
    log.debug(c.dict())

    assert c.my_dict == {123: True, 5: False}

    # note that the value for 'anotherKey' is a string value ('123') here,
    # but we might want to see if we can update it to a numeric value (123)
    # instead.
    assert c.my_other_dict == {
        'some_key': 'value',
        'anotherKey': '123',
        'LastKey': 'just a test~',
    }

    assert c.my_default_dict == {1.2: datetime(2021, 1, 2, 13, 57, 21)}
    assert c.my_typed_dict == {'my_bool': True}

    assert c.to_dict() == {
        'my_dict': {5: False, 123: True},
        'my_other_dict': {'LastKey': 'just a test~',
                          'anotherKey': '123',
                          'some_key': 'value'},
        'my_default_dict': {1.2: '2021-01-02T13:57:21'},
        'my_typed_dict': {'my_bool': True}
    }


def test_load_with_missing_env_variables():
    """
    Test calling the constructor of an `EnvWizard` subclass when the
    associated vars are missing in the Environment.
    """

    class MyClass(EnvWizard):
        missing_field_1: str
        missing_field_2: datetime
        missing_field_3: Dict[str, int]

    with pytest.raises(MissingVars) as e:
        _ = MyClass()

    assert str(e.value) == dedent("""\
    There are 3 required fields in class `test_load_with_missing_env_variables.<locals>.MyClass` missing in the Environment:
        - missing_field_1
        - missing_field_2
        - missing_field_3

    Resolution: set a default value for any optional fields, as below.

    class test_load_with_missing_env_variables.<locals>.MyClass:
        missing_field_1: str = ''
        missing_field_2: datetime = None
        missing_field_3: Dict = None
    """.rstrip())


def test_load_with_parse_error():
    os.environ.update(MY_STR='abc')

    class MyClass(EnvWizard, reload_env=True):
        class _(EnvWizard.Meta):
            debug_enabled = True

        my_str: int

    with pytest.raises(ParseError) as e:
        _ = MyClass()

    assert str(e.value.base_error) == "invalid literal for int() with base 10: 'abc'"
    assert e.value.kwargs['env_variable'] == 'MY_STR'


def test_load_with_dotenv_file():
    """Test reading from the `.env` file in project root directory."""

    class MyClass(EnvWizard):
        class _(EnvWizard.Meta):
            env_file = True

        my_str: int
        my_time: time
        my_date: date = None

    assert MyClass().dict() == {'my_str': 42,
                                'my_time': time(15, 20),
                                'my_date': date(2022, 1, 21)}


def test_load_with_dotenv_file_with_path():
    """Test reading from the `.env.test` file in `tests/unit` directory."""

    class MyClass(EnvWizard):
        class _(EnvWizard.Meta):
            env_file = Path(__file__).parent / '.env.test'
            key_lookup_with_load = 'PASCAL'

        my_value: float
        my_dt: datetime
        another_date: date

    c = MyClass()

    assert c.dict() == {'my_value': 1.23,
                        'my_dt': datetime(2022, 4, 27, 12, 30, 45),
                        'another_date': date(2021, 12, 17)}

    expected_json = '{"another_date": "2021-12-17", "my_dt": "2022-04-27T12:30:45", "my_value": 1.23}'
    assert c.to_json(sort_keys=True) == expected_json


def test_load_when_constructor_kwargs_are_passed():
    """
    Using the constructor method of an `EnvWizard` subclass when
    passing keyword arguments instead of the Environment.
    """
    os.environ.update(MY_STRING_VAR='hello world')

    class MyTestClass(EnvWizard, reload_env=True):
        my_string_var: str

    c = MyTestClass(my_string_var='test!!')
    assert c.my_string_var == 'test!!'

    c = MyTestClass()
    assert c.my_string_var == 'hello world'


def test_load_with_constructor():
    """
    Using the constructor method of an `EnvWizard` subclass raises an error
    when `init` is not disabled.
    """
    os.environ.update(MY_STRING_VAR='hello world')

    class MyTestClass(EnvWizard, reload_env=True, init=False):
        my_string_var: str

    env = MyTestClass()
    assert env.to_json() == '{"my_string_var": "hello world"}'
