import tempfile

from dataclasses import field, dataclass
from datetime import datetime, time, date, timezone
from logging import getLogger, DEBUG, StreamHandler
from pathlib import Path
from textwrap import dedent
from typing import ClassVar, List, Dict, Union, DefaultDict, Set, TypedDict, Optional

import pytest

import dataclass_wizard.bases_meta
from dataclass_wizard.class_helper import get_meta
from dataclass_wizard.constants import PY311_OR_ABOVE
from dataclass_wizard.errors import MissingVars, ParseError, MissingFields
from dataclass_wizard import EnvWizard as EnvWizardV0, DataclassWizard
from dataclass_wizard.v1 import Alias, EnvWizard, Env
from tests._typing import PY310_OR_ABOVE

from ..utils_env import from_env, envsafe


log = getLogger(__name__)

# quick access to the `tests/unit` directory
here = Path(__file__).parent


def test_v1_enabled_with_v0_base_class_raises_error():
    with pytest.raises(TypeError, match=r'MyClass is using Meta\(v1=True\) but does not inherit from `dataclass_wizard.v1.EnvWizard`.'):
        class MyClass(EnvWizardV0):
            class _(EnvWizardV0.Meta):
                v1 = True

            my_value: str


@pytest.mark.skipif(not PY310_OR_ABOVE, reason='Requires Python 3.10 or higher')
def test_envwizard_nested_envwizard_from_env_and_instance_passthrough():
    class Child(EnvWizard):
        x: int

    class Parent(EnvWizard):
        child: Child

    # 1) Instance passthrough (no parsing)
    c = Child(x=5)
    p1 = Parent(child=c)
    assert p1.child is c
    assert p1.child.x == 5

    # 2) Env mapping with wrong casing should fail
    with pytest.raises(MissingFields) as e:
        from_env(Parent, {"CHILD": {"X": "123"}})
    assert e.value.missing_fields == ["x"]

    # 3) Env mapping with correct keys should parse
    p2 = from_env(Parent, {"CHILD": {"x": "123"}})
    assert p2.child.x == 123


@pytest.mark.skipif(not PY310_OR_ABOVE, reason='Requires Python 3.10 or higher')
def test_dataclasswizard_nested_envwizard_from_dict():
    class Child(EnvWizard):
        x: int

    class Parent(DataclassWizard):
        child: Child

    p = Parent.from_dict({"child": {"x": 7}})
    assert p.child.x == 7


def test_envwizard_optional_nested_dataclass_instance_and_env_dict():
    class Sub(DataclassWizard):
        test: str

    class Parent(EnvWizard):
        opt: Optional[Sub]

    # 1) Passing an instance should passthrough (no parsing)
    s = Sub(test="true")
    p1 = Parent(opt=s)
    assert p1.opt is s
    assert p1.opt.test == "true"

    # 2) Env dict with wrong casing should fail (if your loader expects exact keys)
    with pytest.raises(MissingFields) as e:
        from_env(Parent, {"OPT": {"TEST": "true"}})
    assert e.value.missing_fields == ["test"]

    # 3) Env dict with correct keys should parse
    p2 = from_env(Parent, {"OPT": {"test": "true"}})
    assert p2.opt == Sub(test="true")


def test_load_and_dump():
    """Basic example with simple types (str, int) and collection types such as list."""

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

    env = {
        'hello_world': 'Test',
        'MY_STR': 'This STRING',
        'MY_TEST_VALUE123': '11',
        'THIS_NUM': '23',
        'my_list': '["1", 2, "3", "4.0", 5.0]',
        'my_other_list': 'rob@test.org, this@email.com , hello-world_123@tst.org,z@ab.c'
    }

    e = from_env(MyClass, env)
    log.debug(e.raw_dict())

    assert not hasattr(e, 'my_cls_var')
    assert e.other_var == 21

    assert e.my_str == 'This STRING'
    assert e.this_num == 23
    assert e.my_list == [1, 2, 3, 4, 5]
    assert e.my_other_list == ['rob@test.org', 'this@email.com', 'hello-world_123@tst.org', 'z@ab.c']
    assert e.my_test_value123 == 11
    assert e.my_field_not_in_env == 'testing'

    assert e.to_dict() == {
        'my_str': 'This STRING',
        'this_num': 23,
        'my_list': [1, 2, 3, 4, 5],
        'my_other_list': ['rob@test.org',
                          'this@email.com',
                          'hello-world_123@tst.org',
                          'z@ab.c'],
        'my_test_value123': 11,
        'my_field_not_in_env': 'testing',
    }


def test_load_and_dump_with_dict():
    """Example with more complex types such as dict, TypedDict, and defaultdict."""

    class MyTypedDict(TypedDict):
        my_bool: bool

    # Fix so the forward reference works
    globals().update(locals())

    class ClassWithDict(EnvWizard):
        class _(EnvWizard.Meta):
            v1_field_to_env_load = {'my_other_dict': 'My.Other.Dict'}

        my_dict: Dict[int, bool]
        my_other_dict: Dict[str, Union[int, str]]
        my_default_dict: DefaultDict[float, datetime]
        my_typed_dict: MyTypedDict

    env = {
        'MY_DICT': '{"123": "True", "5": "false"}',
        'My.Other.Dict': 'some_key=value,  anotherKey=123 ,LastKey=just a test~',
        'my_default_dict': '  {  "1.2": "2021-01-02T13:57:21"  }  ',
        'MY_TYPED_DICT': 'my_bool=true'
    }

    c = from_env(ClassWithDict, env)

    log.debug(c.raw_dict())

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

    class MyClass(EnvWizard):
        class _(EnvWizard.Meta):
            v1_field_to_env_load = {
                'answer_to_life': 'the_number',
                'emails': ('EMAILS', 'My_Other_List'),
            }

        my_str: str = Env('the_string', 'hello_world')
        answer_to_life: int
        list_of_nums: List[int] = Alias(env='my_list')
        emails: List[str]
        # added for code coverage.
        # case where `Alias` is used, but an alas is not defined.
        my_test_value123: int = Alias(default=21)

    env = {
        'hello_world': 'Test',
        'MY_TEST_VALUE123': '11',
        'the_number': '42',
        'my_list': '3, 2,  1,0',
        'My_Other_List': 'rob@test.org, this@email.com , hello-world_123@tst.org,z@ab.c'
    }

    c = from_env(MyClass, env)
    log.debug(c.raw_dict())

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

    assert str(e.value) == dedent("""
    `test_load_with_missing_env_variables.<locals>.MyClass` has 3 required fields missing in the environment:
        - missing_field_1 -> MISSING_FIELD_1
        - missing_field_2 -> MISSING_FIELD_2
        - missing_field_3 -> MISSING_FIELD_3

    **Resolution options**

    1. Set a default value for the field:

        class test_load_with_missing_env_variables.<locals>.MyClass:
            missing_field_1: str = ''
            missing_field_2: datetime = None
            missing_field_3: typing.Dict[str, int] = None

    2. Provide the value during initialization:

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
    class MyClass(EnvWizard):
        my_str: int

    with pytest.raises(ParseError) as e:
        _ = from_env(MyClass, {'MY_STR': 'abc'})

    assert str(e.value.base_error) == "invalid literal for int() with base 10: 'abc'"
    # TODO right now we don't surface this info
    # assert e.value.kwargs['env_variable'] == 'MY_STR'


def test_load_with_parse_error_when_env_var_is_specified():
    """
    Raising `ParseError` when a dataclass field to env var mapping is
    specified. Added for code coverage.
    """
    class MyClass(EnvWizard):
        a_string: int = Env('MY_STR')

    with pytest.raises(ParseError) as e:
        _ = from_env(MyClass, {'MY_STR': 'abc'})

    assert str(e.value.base_error) == "invalid literal for int() with base 10: 'abc'"
    # assert e.value.kwargs['env_variable'] == 'MY_STR'


def test_load_with_dotenv_file():
    """Test reading from the `.env` file in project root directory."""

    class MyClass(EnvWizard):
        class _(EnvWizard.Meta):
            env_file = True
            v1_load_case = 'FIELD_FIRST'
            v1_dump_case = 'SNAKE'

        my_str: int
        my_time: time
        MyDate: date = None

    assert MyClass().raw_dict() == {'my_str': 42,
                                    'my_time': time(15, 20),
                                    'MyDate': date(2022, 1, 21)}
    assert MyClass().to_dict() == {'my_date': '2022-01-21',
                                   'my_str': 42,
                                   'my_time': '15:20:00'}


def test_load_with_dotenv_file_with_path():
    """Test reading from the `.env.test` file in `tests/unit` directory."""

    class MyClass(EnvWizard):
        class _(EnvWizard.Meta):
            env_file = here / '.env.test'

        my_value: float
        my_dt: datetime
        another_date: date

    c = MyClass()

    assert c.raw_dict() == {'my_value': 1.23,
                            'my_dt': datetime(2022, 4, 27, 16, 30, 45, tzinfo=timezone.utc),
                            'another_date': date(2021, 12, 17)}

    expected_json = '{"another_date": "2021-12-17", "my_dt": "2022-04-27T16:30:45Z", "my_value": 1.23}'
    assert c.to_json(sort_keys=True) == expected_json



def test_load_with_tuple_of_dotenv_and_env_file_param_to_init():
    """
    Test when `env_file` is specified as a tuple of dotenv files, and
    the `file` parameter is also passed in to the constructor
    or __init__() method.
    """

    class MyClass(EnvWizard):
        class _(EnvWizard.Meta):
            env_file = '.env', here / '.env.test'
            v1_env_precedence = 'SECRETS_DOTENV_ENV'

        my_value: float
        my_str: str
        other_key: int = 3

    env = {'MY_STR': 'default from env', 'MY_VALUE': '3322.11', 'other_key': '5'}

    # pass `file=False` so we don't load the Meta `env_file`
    c = from_env(MyClass, env, {'file': False})

    assert c.raw_dict() == {'my_str': 'default from env',
                            'my_value': 3322.11,
                            'other_key': 5}

    # load variables from the Meta `env_file` tuple, and also pass
    # in `other_key` to the constructor method.
    c = from_env(MyClass, env, other_key=7)

    assert c.raw_dict() == {'my_str': '42',
                            'my_value': 1.23,
                            'other_key': 7}

    # load variables from the `file` argument to the constructor
    # method, overriding values from `env_file` in the Meta config.
    c = from_env(MyClass, env, {'file': here/ '.env.prod'})

    assert c.raw_dict() == {'my_str': 'hello world!',
                            'my_value': 3.21,
                            'other_key': 5}


def test_load_when_constructor_kwargs_are_passed():
    """
    Using the constructor method of an `EnvWizard` subclass when
    passing keyword arguments instead of the Environment.
    """
    env = {'MY_STRING_VAR': 'hello world'}

    class MyTestClass(EnvWizard):
        my_string_var: str

    c = from_env(MyTestClass, env, my_string_var='test!!')
    #c = MyTestClass(my_string_var='test!!')
    assert c.my_string_var == 'test!!'

    c = from_env(MyTestClass, env)
    assert c.my_string_var == 'hello world'


#
# # TODO
#
# # def test_extra_keyword_arguments_when_deny_extra():
# #     """
# #     Passing extra keyword arguments to the constructor method of an `EnvWizard`
# #     subclass raises an error by default, as `Extra.DENY` is the default behavior.
# #     """
# #
# #     os.environ['A_FIELD'] = 'hello world!'
# #
# #     class MyClass(EnvWizard, reload_env=True):
# #         a_field: str
# #
# #     with pytest.raises(ExtraData) as e:
# #         _ = MyClass(another_field=123, third_field=None)
# #
# #     log.error(e.value)
# #
# #
# # def test_extra_keyword_arguments_when_allow_extra():
# #     """
# #     Passing extra keyword arguments to the constructor method of an `EnvWizard`
# #     subclass does not raise an error and instead accepts or "passes through"
# #     extra keyword arguments, when `Extra.ALLOW` is specified for the
# #     `extra` Meta field.
# #     """
# #
# #     os.environ['A_FIELD'] = 'hello world!'
# #
# #     class MyClass(EnvWizard, reload_env=True):
# #
# #         class _(EnvWizard.Meta):
# #             extra = 'ALLOW'
# #
# #         a_field: str
# #
# #     c = MyClass(another_field=123, third_field=None)
# #
# #     assert getattr(c, 'another_field') == 123
# #     assert hasattr(c, 'third_field')
# #
# #     assert c.to_json() == '{"a_field": "hello world!"}'
# #
# #
# # def test_extra_keyword_arguments_when_ignore_extra():
# #     """
# #     Passing extra keyword arguments to the constructor method of an `EnvWizard`
# #     subclass does not raise an error and instead ignores extra keyword
# #     arguments, when `Extra.IGNORE` is specified for the `extra` Meta field.
# #     """
# #
# #     os.environ['A_FIELD'] = 'hello world!'
# #
# #     class MyClass(EnvWizard, reload_env=True):
# #
# #         class _(EnvWizard.Meta):
# #             extra = 'IGNORE'
# #
# #         a_field: str
# #
# #     c = MyClass(another_field=123, third_field=None)
# #
# #     assert not hasattr(c, 'another_field')
# #     assert not hasattr(c, 'third_field')
# #
# #     assert c.to_json() == '{"a_field": "hello world!"}'


def test_init_method_declaration_is_logged_when_debug_mode_is_enabled(mock_debug_log):

    class _EnvSettings(EnvWizard):
        auth_key: str = Env('my_auth_key')
        api_key: str = Env('hello', 'test')
        domains: Set[str] = field(default_factory=set)
        answer_to_life: int = 42

    from_env(_EnvSettings, {'my_auth_key': 'v', 'test': 'k'})

    # assert that the __init__() method declaration is logged
    assert mock_debug_log.records[-2].levelname == 'DEBUG'
    assert "setattr(_EnvSettings, '__init__', __dataclass_wizard_init__EnvSettings__)" in mock_debug_log.records[-2].message

    # reset global flag for other tests that
    # rely on `debug_enabled` functionality
    dataclass_wizard.bases_meta._debug_was_enabled = False


def test_load_with_tuple_of_dotenv_and_env_prefix_param_to_init():
    """
    Test when `env_file` is specified as a tuple of dotenv files, and
    the `file` parameter is also passed in to the constructor
    or __init__() method. Additionally, test prefixing environment
    variables using `Meta.env_prefix` and `prefix` in __init__().
    """

    class MyClass(EnvWizard):
        class _(EnvWizard.Meta):
            env_file = '.env', here / '.env.test'
            env_prefix = 'PREFIXED_'  # Static prefix
            v1_env_precedence = 'SECRETS_DOTENV_ENV'

        my_value: float
        my_str: str
        other_key: int = 3

    env = {
        'PREFIXED_MY_STR': 'prefixed string',
        'PREFIXED_MY_VALUE': '12.34',
        'PREFIXED_OTHER_KEY': '10',
        'MY_STR': 'default from env',
        'MY_VALUE': '3322.11',
        'OTHER_KEY': '5',
    }

    # Test without prefix
    c = from_env(MyClass, env, {'file': False, 'prefix': ''})

    assert c.raw_dict() == {'my_str': 'default from env',
                            'my_value': 3322.11,
                            'other_key': 5}

    # Test with Meta.env_prefix applied
    c = from_env(MyClass, env, other_key=7)

    assert c.raw_dict() == {'my_str': 'prefixed string',
                            'my_value': 12.34,
                            'other_key': 7}

    # Override prefix dynamically with prefix
    c = from_env(MyClass, env, {'file': False, 'prefix': ''})

    assert c.raw_dict() == {'my_str': 'default from env',
                            'my_value': 3322.11,
                            'other_key': 5}

    # Dynamically set a new prefix via prefix
    c = from_env(MyClass, env, {'prefix': 'PREFIXED_'})

    assert c.raw_dict() == {'my_str': 'prefixed string',
                            'my_value': 12.34,
                            'other_key': 10}

    # Otherwise, this would take priority, as it's named `My_Value` in `.env.prod`
    del env['MY_VALUE']

    # Load from `file` argument, ignoring prefixes
    c = from_env(MyClass, env, {'file': here / '.env.prod', 'prefix': ''})

    assert c.raw_dict() == {'my_str': 'hello world!',
                            'my_value': 3.21,
                            'other_key': 5}


def test_env_prefix_with_env_file():
    """
    Test `env_prefix` with `env_file` where file has prefixed env variables.

    Contents of `.env.prefix`:
        MY_PREFIX_STR='my prefix value'
        MY_PREFIX_BOOL=t
        MY_PREFIX_INT='123.0'

    """
    class MyPrefixTest(EnvWizard):
        class _(EnvWizard.Meta):
            env_prefix = 'MY_PREFIX_'
            env_file = here / '.env.prefix'

        a_str: str
        a_bool: bool
        an_int: int

    expected = MyPrefixTest(a_str='my prefix value',
                            a_bool=True,
                            an_int=123)

    assert MyPrefixTest() == expected


def test_secrets_dir_and_override():
    """
    Test `Meta.secrets_dir` and `_secrets_dir` for handling secrets.
    """
    # Create temporary directories and files to simulate secrets
    with tempfile.TemporaryDirectory() as default_secrets_dir, tempfile.TemporaryDirectory() as override_secrets_dir:
        # Paths for default secrets
        default_dir_path = Path(default_secrets_dir)
        (default_dir_path / "MY_SECRET_KEY").write_text("default-secret-key")
        (default_dir_path / "ANOTHER_SECRET").write_text("default-another-secret")

        # Paths for override secrets
        override_dir_path = Path(override_secrets_dir)
        (override_dir_path / "MY_SECRET_KEY").write_text("override-secret-key")
        (override_dir_path / "NEW_SECRET").write_text("new-secret-value")

        # Define an EnvWizard class with Meta.secrets_dir
        class MySecretClass(EnvWizard):
            class _(EnvWizard.Meta):
                secrets_dir = default_dir_path  # Static default secrets directory

            my_secret_key: str
            another_secret: str = "default"
            new_secret: str = "default-new"

        # Test case 1: Use Meta.secrets_dir
        instance = MySecretClass()
        assert instance.raw_dict() == {
            "my_secret_key": "default-secret-key",
            "another_secret": "default-another-secret",
            "new_secret": "default-new",
        }

        # Test case 2: Override secrets_dir using _secrets_dir
        instance = MySecretClass(__env__={'secrets_dir': override_dir_path})
        assert instance.raw_dict() == {
            "my_secret_key": "override-secret-key",  # Overridden by override directory
            "another_secret": "default",  # No longer from Meta.secrets_dir (explicit value overrides it)
            "new_secret": "new-secret-value",  # Only in override directory
        }

        # Test case 3: Missing secrets fallback to defaults
        instance = MySecretClass()
        assert instance.raw_dict() == {
            "my_secret_key": "default-secret-key",  # From default directory
            "another_secret": "default-another-secret",  # From default directory
            "new_secret": "default-new",  # From the field default
        }

        # Test case 4: Invalid secrets_dir scenarios
        # Case 4a: Directory doesn't exist (ignored with warning)
        instance = MySecretClass(__env__={'secrets_dir': (default_dir_path, Path("/non/existent/directory"))})
        assert instance.raw_dict() == {
            "my_secret_key": "default-secret-key",  # Fallback to default secrets
            "another_secret": "default-another-secret",
            "new_secret": "default-new",
        }

        # Case 4b: secrets_dir is a file (raises error)
        with tempfile.NamedTemporaryFile() as temp_file:
            invalid_secrets_path = Path(temp_file.name)
            with pytest.raises(ValueError, match="Secrets directory .* is a file, not a directory"):
                MySecretClass(__env__={'secrets_dir': invalid_secrets_path})


def test_env_wizard_handles_nested_dataclass_field_with_multiple_input_types():
    """
    Test that EnvWizard correctly handles a field typed as a nested dataclass:

    - When specified as an environment variable (JSON-encoded string).
    - When passed as a dictionary to the constructor.
    - When passed as an instance of the nested dataclass.
    """

    @dataclass
    class DatabaseSettings:
        host: str
        port: int

    class Settings(EnvWizard):
        database: DatabaseSettings

        class Config(EnvWizard.Meta):
            env_prefix='test'
            env_nested_delimiter = '_'

    # Field `database` is specified as an env var
    assert envsafe({'testdatabase': {"host": "localhost", "port": "5432"}}) == {'testdatabase': '{"host":"localhost","port":"5432"}'}

    settings = from_env(Settings, {'testdatabase': {"host": "localhost", "port": "5432"}})
    assert settings.database == DatabaseSettings(host='localhost', port=5432)

    # Field `database` is specified as a dict
    settings = Settings(database={"host": "localhost", "port": "4000"})
    assert settings == Settings(database=DatabaseSettings(host='localhost', port=4000))

    # Field `database` is passed in to constructor (__init__)
    settings = Settings(database={"host": "localhost", "port": "27017"})
    assert settings == Settings(database=DatabaseSettings(host='localhost', port=27017))


def test_env_wizard_with_no_apply_dataclass():
    """Subclass `EnvWizard` with `_apply_dataclass=False`."""
    @dataclass(init=False)
    class MyClass(EnvWizard, _apply_dataclass=False):
        my_str: str

    assert from_env(MyClass, {'my_str': ''}) == MyClass(my_str='')


def test_env_wizard_with_debug(restore_logger):
    """Subclass `EnvWizard` with `debug=True`."""
    logger = restore_logger

    class _(EnvWizard, debug=True):
        ...

    assert get_meta(_).v1_debug == DEBUG

    assert logger.level == DEBUG
    assert logger.propagate is False
    assert any(isinstance(h, StreamHandler) for h in logger.handlers)
    # optional: ensure it didn't add duplicates
    assert sum(isinstance(h, StreamHandler) for h in logger.handlers) == 1
