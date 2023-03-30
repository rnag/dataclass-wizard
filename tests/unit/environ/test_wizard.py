import logging
import os
from dataclasses import field
from datetime import datetime, time, date, timezone
from pathlib import Path
from textwrap import dedent
from typing import ClassVar, List, Dict, Union, DefaultDict, Set

import pytest

from dataclass_wizard import EnvWizard, json_field
from dataclass_wizard.errors import MissingVars, ParseError, ExtraData

from ...conftest import *


log = logging.getLogger(__name__)

# quick access to the `tests/unit` directory
here = Path(__file__).parent


def test_load_and_dump():
    """Basic example with simple types (str, int) and collection types such as list."""

    os.environ.update({
        'hello_world': 'Test',
        'MyStr': 'This STRING',
        'MY_TEST_VALUE123': '11',
        'THIS_Num': '23',
        'my_list': '["1", 2, "3", "4.5", 5.7]',
        'my_other_list': 'rob@test.org, this@email.com , hello-world_123@tst.org,z@ab.c'
    })

    class MyClass(EnvWizard, reload_env=True):
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
    """Example with more complex types such as dict, TypedDict, and defaultdict."""

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


def test_load_and_dump_with_aliases():
    """
    Example with fields that are aliased to differently-named env variables
    in the Environment.
    """

    os.environ.update({
        'hello_world': 'Test',
        'MY_TEST_VALUE123': '11',
        'the_number': '42',
        'my_list': '3, 2,  1,0',
        'My_Other_List': 'rob@test.org, this@email.com , hello-world_123@tst.org,z@ab.c'
    })

    class MyClass(EnvWizard, reload_env=True):
        class _(EnvWizard.Meta):
            field_to_env_var = {
                'answer_to_life': 'the_number',
                'emails': ('EMAILS', 'My_Other_List'),
            }

        my_str: str = json_field(('the_string', 'hello_world'))
        answer_to_life: int
        list_of_nums: List[int] = json_field('my_list')
        emails: List[str]
        # added for code coverage.
        # case where `json_field` is used, but an alas is not defined.
        my_test_value123: int = json_field(..., default=21)

    c = MyClass()
    log.debug(c.dict())

    assert c.my_str == 'Test'
    assert c.answer_to_life == 42
    assert c.list_of_nums == [3, 2, 1, 0]
    assert c.emails == ['rob@test.org', 'this@email.com', 'hello-world_123@tst.org', 'z@ab.c']
    assert c.my_test_value123 == 11

    assert c.to_dict() == {
        'answer_to_life': 42,
        'emails': ['rob@test.org',
                   'this@email.com',
                   'hello-world_123@tst.org',
                   'z@ab.c'],
        'list_of_nums': [3, 2, 1, 0],
        'my_str': 'Test',
        'my_test_value123': 11,
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
        default_field: Set[str] = field(default_factory=set)

    with pytest.raises(MissingVars) as e:
        _ = MyClass()

    assert str(e.value) == dedent("""\
    There are 3 required fields in class `test_load_with_missing_env_variables.<locals>.MyClass` missing in the Environment:
        - missing_field_1
        - missing_field_2
        - missing_field_3

    resolution #1: set a default value for any optional fields, as below.

    class test_load_with_missing_env_variables.<locals>.MyClass:
        missing_field_1: str = ''
        missing_field_2: datetime = None
        missing_field_3: typing.Dict[str, int] = None

    ...
    resolution #2: pass in values for required fields to test_load_with_missing_env_variables.<locals>.MyClass.__init__():

        instance = test_load_with_missing_env_variables.<locals>.MyClass(missing_field_1='', missing_field_2=None, missing_field_3=None)
    """.rstrip())

    # added for code coverage.
    # test when only missing a single (1) required field.
    with pytest.raises(MissingVars) as e:
        _ = MyClass(missing_field_1='test', missing_field_3='key=123')

    error_info = str(e.value)
    assert '1 required field' in error_info
    assert 'missing_field_2' in error_info


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


def test_load_with_parse_error_when_env_var_is_specified():
    """
    Raising `ParseError` when a dataclass field to env var mapping is
    specified. Added for code coverage.
    """

    os.environ.update(MY_STR='abc')

    class MyClass(EnvWizard, reload_env=True):
        class _(EnvWizard.Meta):
            debug_enabled = True

        a_string: int = json_field('MY_STR')

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
            env_file = here / '.env.test'
            key_lookup_with_load = 'PASCAL'

        my_value: float
        my_dt: datetime
        another_date: date

    c = MyClass()

    assert c.dict() == {'my_value': 1.23,
                        'my_dt': datetime(2022, 4, 27, 16, 30, 45, tzinfo=timezone.utc),
                        'another_date': date(2021, 12, 17)}

    expected_json = '{"another_date": "2021-12-17", "my_dt": "2022-04-27T16:30:45Z", "my_value": 1.23}'
    assert c.to_json(sort_keys=True) == expected_json


def test_load_with_tuple_of_dotenv_and_env_file_param_to_init():
    """
    Test when `env_file` is specified as a tuple of dotenv files, and
    the `_env_file` parameter is also passed in to the constructor
    or __init__() method.
    """

    os.environ.update(
        MY_STR='default from env',
        myValue='3322.11',
        Other_Key='5',
    )

    class MyClass(EnvWizard):
        class _(EnvWizard.Meta):
            env_file = '.env', here / '.env.test'
            key_lookup_with_load = 'PASCAL'

        my_value: float
        my_str: str
        other_key: int = 3

    # pass `_env_file=False` so we don't load the Meta `env_file`
    c = MyClass(_env_file=False, _reload_env=True)

    assert c.dict() == {'my_str': 'default from env',
                        'my_value': 3322.11,
                        'other_key': 5}

    # load variables from the Meta `env_file` tuple, and also pass
    # in `other_key` to the constructor method.
    c = MyClass(other_key=7)

    assert c.dict() == {'my_str': '42',
                        'my_value': 1.23,
                        'other_key': 7}

    # load variables from the `_env_file` argument to the constructor
    # method, overriding values from `env_file` in the Meta config.
    c = MyClass(_env_file=here / '.env.prod')

    assert c.dict() == {'my_str': 'hello world!',
                        'my_value': 3.21,
                        'other_key': 5}


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


def test_extra_keyword_arguments_when_deny_extra():
    """
    Passing extra keyword arguments to the constructor method of an `EnvWizard`
    subclass raises an error by default, as `Extra.DENY` is the default behavior.
    """

    os.environ['A_FIELD'] = 'hello world!'

    class MyClass(EnvWizard, reload_env=True):
        a_field: str

    with pytest.raises(ExtraData) as e:
        _ = MyClass(another_field=123, third_field=None)

    log.error(e.value)


def test_extra_keyword_arguments_when_allow_extra():
    """
    Passing extra keyword arguments to the constructor method of an `EnvWizard`
    subclass does not raise an error and instead accepts or "passes through"
    extra keyword arguments, when `Extra.ALLOW` is specified for the
    `extra` Meta field.
    """

    os.environ['A_FIELD'] = 'hello world!'

    class MyClass(EnvWizard, reload_env=True):

        class _(EnvWizard.Meta):
            extra = 'ALLOW'

        a_field: str

    c = MyClass(another_field=123, third_field=None)

    assert getattr(c, 'another_field') == 123
    assert hasattr(c, 'third_field')

    assert c.to_json() == '{"a_field": "hello world!"}'


def test_extra_keyword_arguments_when_ignore_extra():
    """
    Passing extra keyword arguments to the constructor method of an `EnvWizard`
    subclass does not raise an error and instead ignores extra keyword
    arguments, when `Extra.IGNORE` is specified for the `extra` Meta field.
    """

    os.environ['A_FIELD'] = 'hello world!'

    class MyClass(EnvWizard, reload_env=True):

        class _(EnvWizard.Meta):
            extra = 'IGNORE'

        a_field: str

    c = MyClass(another_field=123, third_field=None)

    assert not hasattr(c, 'another_field')
    assert not hasattr(c, 'third_field')

    assert c.to_json() == '{"a_field": "hello world!"}'


def test_init_method_declaration_is_logged_when_debug_mode_is_enabled(mock_log):

    class _EnvSettings(EnvWizard):

        class _(EnvWizard.Meta):
            debug_enabled = True
            extra = 'ALLOW'

        auth_key: str = json_field('my_auth_key')
        api_key: str = json_field(('hello', 'test'))
        domains: Set[str] = field(default_factory=set)
        answer_to_life: int = 42

    # assert that the __init__() method declaration is logged
    assert mock_log.records[-1].levelname == 'INFO'
    assert '_EnvSettings.__init__()' in mock_log.records[-1].message
