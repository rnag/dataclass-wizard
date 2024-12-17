import io
from dataclasses import dataclass
from typing import List, Optional, Dict

import pytest
from pytest_mock import MockerFixture

from dataclass_wizard import Container
from dataclass_wizard.wizard_mixins import (
    JSONListWizard, JSONFileWizard, TOMLWizard, YAMLWizard
)
from .conftest import SampleClass


class MyListWizard(SampleClass, JSONListWizard):
    ...


class MyFileWizard(SampleClass, JSONFileWizard):
    ...


@dataclass
class MyYAMLWizard(YAMLWizard):
    my_str: str
    inner: Optional['Inner'] = None


@dataclass
class Inner:
    my_float: float
    my_list: List[str]


@pytest.fixture
def mock_open(mocker: MockerFixture):
    return mocker.patch('dataclass_wizard.wizard_mixins.open')


def test_json_list_wizard_methods():
    """Test and coverage the base methods in JSONListWizard."""
    c1 = MyListWizard.from_json('{"f1": "hello", "f2": 111}')
    assert c1.__class__ is MyListWizard

    c2 = MyListWizard.from_json('[{"f1": "hello", "f2": 111}]')
    assert c2.__class__ is Container

    c3 = MyListWizard.from_list([{"f1": "hello", "f2": 111}])
    assert c3.__class__ is Container

    assert c2 == c3


def test_json_file_wizard_methods(mocker: MockerFixture, mock_open):
    """Test and coverage the base methods in JSONFileWizard."""
    filename = 'my_file.json'
    my_dict = {'f1': 'Hello world!', 'f2': 123}

    mock_decoder = mocker.Mock()
    mock_decoder.return_value = my_dict

    c = MyFileWizard.from_json_file(filename,
                                    decoder=mock_decoder)

    mock_open.assert_called_once_with(filename)
    mock_decoder.assert_called_once()

    mock_encoder = mocker.Mock()
    mock_open.reset_mock()

    c.to_json_file(filename,
                   encoder=mock_encoder)

    mock_open.assert_called_once_with(filename, 'w')
    mock_encoder.assert_called_once_with(my_dict, mocker.ANY)


def test_yaml_wizard_methods(mocker: MockerFixture):
    """Test and coverage the base methods in YAMLWizard."""
    yaml_data = """\
    my_str: test value
    inner:
        my_float: 1.2
        my_list:
            - hello, world!
            - 123\
    """

    # Patch open() to return a file-like object which returns our string data.
    m = mocker.patch('dataclass_wizard.wizard_mixins.open',
                     mocker.mock_open(read_data=yaml_data))

    filename = 'my_file.yaml'

    obj = MyYAMLWizard.from_yaml_file(filename)

    m.assert_called_once_with(filename)
    m.reset_mock()

    assert obj == MyYAMLWizard(my_str='test value',
                               inner=Inner(my_float=1.2,
                                           my_list=['hello, world!', '123']))

    mock_open.return_value = mocker.mock_open()

    obj.to_yaml_file(filename)

    m.assert_called_once_with(filename, 'w')

    # default key casing for the dump process will be `lisp-case`
    m().write.assert_has_calls(
        [mocker.call('my-str'),
         mocker.call('inner'),
         mocker.call('my-float'),
         mocker.call('1.2'),
         mocker.call('my-list'),
         mocker.call('world!')],
        any_order=True)


def test_yaml_wizard_list_to_json():
    """Test and coverage the `list_to_json` method in YAMLWizard."""
    @dataclass
    class MyClass(YAMLWizard, key_transform='SNAKE'):
        my_str: str
        my_dict: Dict[int, str]

    yaml_string = MyClass.list_to_yaml([
        MyClass('42', {111: 'hello', 222: 'world'}),
        MyClass('testing!', {333: 'this is a test.'})
    ])

    assert yaml_string == """\
- my_dict:
    111: hello
    222: world
  my_str: '42'
- my_dict:
    333: this is a test.
  my_str: testing!
"""


def test_yaml_wizard_for_branch_coverage(mocker: MockerFixture):
    """
    For branching logic in YAMLWizard, mainly for code coverage purposes.
    """

    # This is to coverage the `if` condition in the `__init_subclass__`
    @dataclass
    class MyClass(YAMLWizard, key_transform=None):
        ...

    # from_yaml: To cover the case of passing in `decoder`
    mock_return_val = {'my_str': 'test string'}

    mock_decoder = mocker.Mock()
    mock_decoder.return_value = mock_return_val

    result = MyYAMLWizard.from_yaml('my stream', decoder=mock_decoder)

    assert result == MyYAMLWizard('test string')
    mock_decoder.assert_called_once()

    # to_yaml: To cover the case of passing in `encoder`
    mock_encoder = mocker.Mock()
    mock_encoder.return_value = mock_return_val

    m = MyYAMLWizard('test string')
    result = m.to_yaml(encoder=mock_encoder)

    assert result == mock_return_val
    mock_encoder.assert_called_once()

    # list_to_yaml: To cover the case of passing in `encoder`
    result = MyYAMLWizard.list_to_yaml([], encoder=mock_encoder)

    assert result == mock_return_val
    mock_encoder.assert_any_call([])


@dataclass
class MyTOMLWizard(TOMLWizard):
    my_str: str
    inner: Optional['Inner'] = None


def test_toml_wizard_methods(mocker: MockerFixture):
    """Test and cover the base methods in TOMLWizard."""
    toml_data = b"""\
my_str = "test value"
[inner]
my_float = 1.2
my_list = ["hello, world!", "123"]
    """

    # Mock open to return the TOML data as a string directly.
    mock_open = mocker.patch("dataclass_wizard.wizard_mixins.open", mocker.mock_open(read_data=toml_data))

    filename = 'my_file.toml'

    # Test reading from TOML file
    obj = MyTOMLWizard.from_toml_file(filename)

    mock_open.assert_called_once_with(filename, 'rb')
    mock_open.reset_mock()

    assert obj == MyTOMLWizard(my_str="test value",
                               inner=Inner(my_float=1.2,
                                           my_list=["hello, world!", "123"]))

    # Test writing to TOML file
    # Mock open for writing to the TOML file.
    mock_open_write = mocker.mock_open()
    mocker.patch("dataclass_wizard.wizard_mixins.open", mock_open_write)

    obj.to_toml_file(filename)

    mock_open_write.assert_called_once_with(filename, 'wb')


def test_toml_wizard_list_to_toml():
    """Test and cover the `list_to_toml` method in TOMLWizard."""
    @dataclass
    class MyClass(TOMLWizard, key_transform='SNAKE'):
        my_str: str
        my_dict: Dict[str, str]

    toml_string = MyClass.list_to_toml([
        MyClass('42', {'111': 'hello', '222': 'world'}),
        MyClass('testing!', {'333': 'this is a test.'})
    ])

    # print(toml_string)

    assert toml_string == """\
items = [
    { my_str = "42", my_dict = { 111 = "hello", 222 = "world" } },
    { my_str = "testing!", my_dict = { 333 = "this is a test." } },
]
"""


def test_toml_wizard_for_branch_coverage(mocker: MockerFixture):
    """Test branching logic in TOMLWizard, mainly for code coverage purposes."""

    # This is to cover the `if` condition in the `__init_subclass__`
    @dataclass
    class MyClass(TOMLWizard, key_transform=None):
        ...

    # from_toml: To cover the case of passing in `decoder`
    mock_return_val = {'my_str': 'test string'}

    mock_decoder = mocker.Mock()
    mock_decoder.return_value = mock_return_val

    result = MyTOMLWizard.from_toml('my stream', decoder=mock_decoder)

    assert result == MyTOMLWizard('test string')
    mock_decoder.assert_called_once()

    # to_toml: To cover the case of passing in `encoder`
    mock_encoder = mocker.Mock()
    mock_encoder.return_value = mock_return_val

    m = MyTOMLWizard('test string')
    result = m.to_toml(encoder=mock_encoder)

    assert result == mock_return_val
    mock_encoder.assert_called_once()

    # list_to_toml: To cover the case of passing in `encoder`
    result = MyTOMLWizard.list_to_toml([], encoder=mock_encoder)

    assert result == mock_return_val
    mock_encoder.assert_any_call({'items': []})
