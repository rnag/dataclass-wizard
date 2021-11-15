import logging
from abc import ABC
from collections import deque, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Set, FrozenSet, Optional, Union, List, DefaultDict
from uuid import UUID

import pytest

from dataclass_wizard import *
from dataclass_wizard.class_helper import get_meta
from dataclass_wizard.constants import TAG
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

    LoadMeta(
        key_transform='CAMEL',
        raise_on_unknown_json_key=True,
        json_key_to_field={'myBoolean': 'my_bool', '__all__': True}
    ).bind_to(MyClass)

    DumpMeta(key_transform='SNAKE').bind_to(MyClass)

    # Assert that meta is properly merged as expected
    meta = get_meta(MyClass)
    assert 'CAMEL' == meta.key_transform_with_load
    assert 'SNAKE' == meta.key_transform_with_dump
    assert True is meta.raise_on_unknown_json_key
    assert {'myBoolean': 'my_bool'} == meta.json_key_to_field

    c = fromdict(MyClass, d)

    assert c.my_bool is True
    assert isinstance(c.myStrOrInt, int)
    assert c.myStrOrInt == 123

    new_dict = asdict(c)

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

    DumpMeta(key_transform='SNAKE',
             marshal_date_time_as='TIMESTAMP').bind_to(Container)

    d = asdict(c)

    expected = {
        'id': 123,
        'submitted_dt': round(submitted_dt.timestamp()),
        'my_elements': [
            # Key transform now applies recursively to all nested dataclasses
            # by default! :-)
            {'order_index': 111, 'status_code': '200'},
            {'order_index': 222, 'status_code': 404}
        ]
    }

    assert d == expected


def test_tag_field_is_used_in_dump_process():
    """
    Confirm that the `_TAG` field appears in the serialized JSON or dict
    object (even for nested dataclasses) when a value is set in the
    `Meta` config for a JSONWizard sub-class.
    """

    @dataclass
    class Data(ABC):
        """ base class for a Member """
        number: float

    class DataA(Data):
        """ A type of Data"""
        pass

    class DataB(Data, JSONWizard):
        """ Another type of Data """
        class _(JSONWizard.Meta):
            """
            This defines a custom tag that shows up in de-serialized
            dictionary object.
            """
            tag = 'B'

    @dataclass
    class Container(JSONWizard):
        """ container holds a subclass of Data """
        class _(JSONWizard.Meta):
            tag = 'CONTAINER'

        data: Union[DataA, DataB]

    data_a = DataA(number=1.0)
    data_b = DataB(number=1.0)

    # initialize container with DataA
    container = Container(data=data_a)

    # export container to string and load new container from string
    d1 = container.to_dict()

    expected = {
        TAG: 'CONTAINER',
        'data': {'number': 1.0}
    }

    assert d1 == expected

    # initialize container with DataB
    container = Container(data=data_b)

    # export container to string and load new container from string
    d2 = container.to_dict()

    expected = {
        TAG: 'CONTAINER',
        'data': {
            TAG: 'B',
            'number': 1.0
        }
    }

    assert d2 == expected


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


def test_to_dict_with_skip_defaults():
    """
    When `skip_defaults` is enabled in the class Meta, fields with default
    values should be excluded from the serialization process.
    """

    @dataclass
    class MyClass(JSONWizard):
        class _(JSONWizard.Meta):
            skip_defaults = True

        my_str: str
        other_str: str = 'any value'
        optional_str: str = None
        my_list: List[str] = field(default_factory=list)
        my_dict: DefaultDict[str, List[float]] = field(
            default_factory=lambda: defaultdict(list))

    c = MyClass('abc')
    log.debug('Instance: %r', c)

    out_dict = c.to_dict()
    assert out_dict == {'myStr': 'abc'}


def test_to_dict_with_excluded_fields():
    """
    Excluding dataclass fields from the serialization process works
    as expected.
    """

    @dataclass
    class MyClass(JSONWizard):

        my_str: str
        other_str: Annotated[str, json_key('AnotherStr', dump=False)]
        my_bool: bool = json_field('TestBool', dump=False)
        my_int: int = 3

    data = {'MyStr': 'my string',
            'AnotherStr': 'testing 123',
            'TestBool': True}

    c = MyClass.from_dict(data)
    log.debug('Instance: %r', c)

    # dynamically exclude the `my_int` field from serialization
    additional_exclude = ('my_int', )

    out_dict = c.to_dict(exclude=additional_exclude)
    assert out_dict == {'myStr': 'my string'}


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
        (timedelta(seconds=12345), does_not_raise()),
        (timedelta(hours=1, minutes=32), does_not_raise()),
        (timedelta(days=1, minutes=51, seconds=7), does_not_raise()),
    ]
)
def test_timedelta(input, expectation):

    @dataclass
    class MyClass(JSONSerializable):
        class Meta(JSONSerializable.Meta):
            key_transform_with_dump = 'Snake'
        my_td: timedelta

    c = MyClass(my_td=input)
    expected = {'my_td': str(input)}

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
