import logging
from collections import deque
from dataclasses import dataclass
from typing import Set, FrozenSet
from uuid import UUID

import pytest

from dataclass_wizard import JSONSerializable, json_field, json_key
from dataclass_wizard.errors import ParseError
from ..conftest import *


log = logging.getLogger(__name__)


def test_to_dict_key_transform_with_json_field():
    """
    Specifying a custom mapping of JSON key to dataclass field, via the
    `json_field` helper function.
    """

    @dataclass
    class MyClass(JSONSerializable):
        my_str: str = json_field('myCustomStr', all=True)
        my_bool: bool = json_field(('my_json_bool', 'myTestBool'), all=True)

    value = 'Testing'
    expected = {'myCustomStr': value, 'my_json_bool': True}

    c = MyClass(my_str=value, my_bool=True)

    result = c.to_dict()
    log.debug('Parsed object: %r', result)

    assert result == expected


def test_to_dict_key_transform_with_json_key():
    """
    Specifying a custom mapping of JSON key to dataclass field, via the
    `json_key` helper function.
    """

    @dataclass
    class MyClass(JSONSerializable):
        my_str: Annotated[str, json_key('myCustomStr', all=True)]
        my_bool: Annotated[bool, json_key(
            'my_json_bool', 'myTestBool', all=True)]

    value = 'Testing'
    expected = {'myCustomStr': value, 'my_json_bool': True}

    c = MyClass(my_str=value, my_bool=True)

    result = c.to_dict()
    log.debug('Parsed object: %r', result)

    result = c.to_dict()
    log.debug('Parsed object: %r', result)

    assert result == expected


@pytest.mark.parametrize(
    'input,expected,expectation',
    [
        ({1, 2, 3}, [1, 2, 3], does_not_raise()),
        ((3.22, 2.11, 1.22), [3.22, 2.11, 1.22], does_not_raise()),
    ]
)
def test_set(input, expected, expectation):

    @dataclass
    class MyClass(JSONSerializable):
        num_set: Set[int]
        any_set: set

    # Sort expected so the assertions succeed
    expected = sorted(expected)

    input_set = set(input)
    c = MyClass(num_set=input_set, any_set=input_set)

    with expectation:
        result = c.to_dict()
        log.debug('Parsed object: %r', result)

        assert all(key in result for key in ('numSet', 'anySet'))

        # Set should be converted to list or tuple, as only those are JSON
        # serializable.
        assert isinstance(result['numSet'], (list, tuple))
        assert isinstance(result['anySet'], (list, tuple))

        assert sorted(result['numSet']) == expected
        assert sorted(result['anySet']) == expected


@pytest.mark.parametrize(
    'input,expected,expectation',
    [
        ({1, 2, 3}, [1, 2, 3], does_not_raise()),
        ((3.22, 2.11, 1.22), [3.22, 2.11, 1.22], does_not_raise()),
    ]
)
def test_frozenset(input, expected, expectation):

    @dataclass
    class MyClass(JSONSerializable):
        num_set: FrozenSet[int]
        any_set: frozenset

    # Sort expected so the assertions succeed
    expected = sorted(expected)

    input_set = frozenset(input)
    c = MyClass(num_set=input_set, any_set=input_set)

    with expectation:
        result = c.to_dict()
        log.debug('Parsed object: %r', result)

        assert all(key in result for key in ('numSet', 'anySet'))

        # Set should be converted to list or tuple, as only those are JSON
        # serializable.
        assert isinstance(result['numSet'], (list, tuple))
        assert isinstance(result['anySet'], (list, tuple))

        assert sorted(result['numSet']) == expected
        assert sorted(result['anySet']) == expected


@pytest.mark.parametrize(
    'input,expected,expectation',
    [
        ({1, 2, 3}, [1, 2, 3], does_not_raise()),
        ((3.22, 2.11, 1.22), [3.22, 2.11, 1.22], does_not_raise()),
    ]
)
def test_deque(input, expected, expectation):

    @dataclass
    class MyQClass(JSONSerializable):
        num_deque: Deque[int]
        any_deque: deque

    input_deque = deque(input)
    c = MyQClass(num_deque=input_deque, any_deque=input_deque)

    with expectation:
        result = c.to_dict()
        log.debug('Parsed object: %r', result)

        assert all(key in result for key in ('numDeque', 'anyDeque'))

        # Set should be converted to list or tuple, as only those are JSON
        # serializable.
        assert isinstance(result['numDeque'], list)
        assert isinstance(result['anyDeque'], list)

        assert result['numDeque'] == expected
        assert result['anyDeque'] == expected


@pytest.mark.parametrize(
    'input,expectation',
    [
        ('testing', pytest.raises(ParseError)),
        ('e1', does_not_raise()),
        (False, pytest.raises(ParseError)),
        (0, does_not_raise()),
    ]
)
@pytest.mark.xfail(reason='still need to add the dump hook for this type')
def test_literal(input, expectation):

    @dataclass
    class MyClass(JSONSerializable):
        class Meta(JSONSerializable.Meta):
            key_transform_with_dump = 'PASCAL'

        my_lit: Literal['e1', 'e2', 0]

    c = MyClass(my_lit=input)
    expected = {'MyLit': input}

    with expectation:
        actual = c.to_dict()

        assert actual == expected
        log.debug('Parsed object: %r', actual)


@pytest.mark.parametrize(
    'input,expectation',
    [
        (UUID('12345678-1234-1234-1234-1234567abcde'), does_not_raise()),
        (UUID('{12345678-1234-5678-1234-567812345678}'), does_not_raise()),
        (UUID('12345678123456781234567812345678'), does_not_raise()),
        (UUID('urn:uuid:12345678-1234-5678-1234-567812345678'), does_not_raise()),
    ]
)
def test_uuid(input, expectation):

    @dataclass
    class MyClass(JSONSerializable):
        class Meta(JSONSerializable.Meta):
            key_transform_with_dump = 'Snake'

        my_id: UUID

    c = MyClass(my_id=input)
    expected = {'my_id': input.hex}

    with expectation:
        actual = c.to_dict()

        assert actual == expected
        log.debug('Parsed object: %r', actual)


@pytest.mark.parametrize(
    'input,expectation',
    [
        (
            {}, pytest.raises(ParseError)),
        (
            {'key': 'value'}, pytest.raises(ParseError)),
        (
            {'my_str': 'test', 'my_int': 2,
             'my_bool': True, 'other_key': 'testing'}, does_not_raise()),
        (
            {'my_str': 3}, pytest.raises(ParseError)),
        (
            {'my_str': 'test', 'my_int': 'test', 'my_bool': True},
            pytest.raises(ValueError)),
        (
            {'my_str': 'test', 'my_int': 2, 'my_bool': True},
            does_not_raise(),
        )
    ]
)
@pytest.mark.xfail(reason='still need to add the dump hook for this type')
def test_typed_dict(input, expectation):

    class MyDict(TypedDict):
        my_str: str
        my_bool: bool
        my_int: int

    @dataclass
    class MyClass(JSONSerializable):
        my_typed_dict: MyDict

    c = MyClass(my_typed_dict=input)

    with expectation:
        result = c.to_dict()
        log.debug('Parsed object: %r', result)
