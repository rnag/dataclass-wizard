import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Set, FrozenSet, Optional, Union, List
from uuid import UUID

import pytest

from dataclass_wizard import *
from dataclass_wizard.errors import ParseError
from ..conftest import *


log = logging.getLogger(__name__)


def test_asdict_and_fromdict():
    """
    Confirm that Meta settings for both `fromdict` and `asdict` are merged
    as expected.
    """

    @dataclass
    class MyClass:
        my_bool: Optional[bool]
        myStrOrInt: Union[str, int]

    d = {'myBoolean': 'tRuE', 'my_str_or_int': 123}

    c = fromdict(MyClass, d, LoadMeta(
        MyClass,
        key_transform='CAMEL',
        json_key_to_field={'myBoolean': 'my_bool', '__all__': True}
    ))

    assert c.my_bool is True
    assert isinstance(c.myStrOrInt, int)
    assert c.myStrOrInt == 123

    new_dict = asdict(c, DumpMeta(MyClass, key_transform='SNAKE'))

    assert new_dict == {'myBoolean': True, 'my_str_or_int': 123}


def test_asdict_with_nested_dataclass():
    """Confirm that `asdict` works for nested dataclasses as well."""

    @dataclass
    class Container:
        id: int
        submittedDt: datetime
        myElements: List['MyElement']

    @dataclass
    class MyElement:
        order_index: Optional[int]
        status_code: Union[int, str]

    submitted_dt = datetime(2021, 1, 1, 5)
    elements = [MyElement(111, '200'), MyElement(222, 404)]

    c = Container(123, submitted_dt, myElements=elements)

    d = asdict(c, DumpMeta(Container,
                           key_transform='SNAKE',
                           marshal_date_time_as='TIMESTAMP'))

    expected = {
        'id': 123,
        'submitted_dt': round(submitted_dt.timestamp()),
        'my_elements': [
            # Key transform only applies to top-level dataclass
            # unfortunately. Need to setup `DumpMeta` for `MyElement`
            # if we need different key transform.
            {'orderIndex': 111, 'statusCode': '200'},
            {'orderIndex': 222, 'statusCode': 404}
        ]
    }

    assert d == expected


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
