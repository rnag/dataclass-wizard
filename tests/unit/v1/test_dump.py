import logging
from abc import ABC
from base64 import b64decode
from collections import deque, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone, date
from typing import (Set, FrozenSet, Optional, Union, List,
                    DefaultDict, Annotated, Literal)
from uuid import UUID

import pytest

from dataclass_wizard import *
from dataclass_wizard.class_helper import get_meta
from dataclass_wizard.constants import TAG
from dataclass_wizard.errors import ParseError
from dataclass_wizard.v1.enums import KeyAction
from dataclass_wizard.v1.models import Alias
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

    d = {'myBoolean': 'tRuE', 'myStrOrInt': 123}

    # v1 opt-in + v1 config
    LoadMeta(
        v1=True,
        v1_case='CAMEL',
        v1_on_unknown_key='RAISE',
        v1_field_to_alias={'my_bool': 'myBoolean'},
    ).bind_to(MyClass)

    # Keep same dump output as before: `myBoolean` for my_bool + snake for the rest.
    DumpMeta(
        v1=True,
        v1_case='SNAKE',
        v1_field_to_alias={'myStrOrInt': 'My String-Or-Num'},
    ).bind_to(MyClass)

    meta = get_meta(MyClass)

    assert meta.v1 is True
    # The library normalizes these internally; accept common representations.
    assert meta.v1_case is None

    assert str(meta.v1_load_case).upper() in ('CAMEL', 'C')
    assert str(meta.v1_dump_case).upper() in ('SNAKE', 'S')
    assert meta.v1_on_unknown_key is KeyAction.RAISE
    assert meta.v1_field_to_alias_load == {'my_bool': 'myBoolean'}
    assert meta.v1_field_to_alias_dump == {'myStrOrInt': 'My String-Or-Num'}

    c = fromdict(MyClass, d)

    assert c.my_bool is True
    assert isinstance(c.myStrOrInt, int)
    assert c.myStrOrInt == 123

    new_dict = asdict(c)
    assert new_dict == {'my_bool': True, 'My String-Or-Num': 123}


def test_asdict_with_nested_dataclass():
    """Confirm that `asdict` works for nested dataclasses as well."""

    @dataclass
    class Container:
        id: int
        submittedDate: date
        submittedDt: datetime
        myElements: List['MyElement']

    @dataclass
    class MyElement:
        order_index: Optional[int]
        status_code: Union[int, str]

    submitted_date = date(2019, 11, 30)
    naive_dt = datetime(2021, 1, 1, 5)
    elements = [MyElement(111, '200'), MyElement(222, 404)]

    # Fix so the forward reference works (since the class definition is inside
    # the test case)
    globals().update(locals())

    DumpMeta(
        v1=True,
        v1_case='SNAKE',
        v1_dump_date_time_as='TIMESTAMP',
        v1_assume_naive_datetime_tz=timezone.utc,
    ).bind_to(Container)

    # Case 1: naive dt -> assumed UTC -> timestamp
    c1 = Container(123, submitted_date, naive_dt, myElements=elements)
    d1 = asdict(c1)

    expected1 = {
        "id": 123,
        "submitted_date": round(datetime(2019, 11, 30, tzinfo=timezone.utc).timestamp()),
        "submitted_dt": round(naive_dt.replace(tzinfo=timezone.utc).timestamp()),
        "my_elements": [
            {"order_index": 111, "status_code": "200"},
            {"order_index": 222, "status_code": 404},
        ],
    }
    assert d1 == expected1

    # Case 2: aware dt (fixed offset "EST") -> convert to UTC -> timestamp
    est_fixed = timezone(timedelta(hours=-5))
    aware_dt = naive_dt.replace(tzinfo=est_fixed)

    c2 = Container(123, submitted_date, aware_dt, myElements=elements)
    d2 = asdict(c2)

    expected2 = dict(expected1)
    expected2["submitted_dt"] = round(aware_dt.timestamp())
    assert d2 == expected2


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
            v1 = True
            """
            This defines a custom tag that shows up in de-serialized
            dictionary object.
            """
            tag = 'B'

    @dataclass
    class Container(JSONWizard, debug=True):
        """ container holds a subclass of Data """

        class _(JSONWizard.Meta):
            v1 = True
            tag = 'CONTAINER'

        data: Union[DataA, DataB]

    data_a = DataA(number=1.0)
    data_b = DataB(number=1.0)

    container = Container(data=data_a)
    d1 = container.to_dict()

    # TODO: Right now `tag` is only populated for dataclasses in `Union`,
    #  but I don't think it's a big issue.

    expected = {
        # TAG: 'CONTAINER',
        'data': {'number': 1.0}
    }
    assert d1 == expected

    container = Container(data=data_b)
    d2 = container.to_dict()

    expected = {
        # TAG: 'CONTAINER',
        'data': {
            TAG: 'B',
            'number': 1.0
        }
    }
    assert d2 == expected


def test_to_dict_key_transform_with_json_field():
    """
    Specifying a custom mapping of JSON key to dataclass field.

    v1: use Alias(...) instead of json_field/json_key.
    """

    @dataclass
    class MyClass(JSONSerializable):
        class _(JSONSerializable.Meta):
            v1 = True

        my_str: str = Alias('myCustomStr')
        my_bool: bool = Alias('my_json_bool', 'myTestBool')

    value = 'Testing'
    expected = {'myCustomStr': value, 'my_json_bool': True}

    c = MyClass(my_str=value, my_bool=True)

    result = c.to_dict()
    log.debug('Parsed object: %r', result)

    assert result == expected


def test_to_dict_key_transform_with_json_key():
    """
    Specifying a custom mapping of JSON key to dataclass field.

    v1: use Annotated[..., Alias(...)].
    """

    @dataclass
    class MyClass(JSONSerializable):
        class _(JSONSerializable.Meta):
            v1 = True

        my_str: Annotated[str, Alias('myCustomStr')]
        my_bool: Annotated[bool, Alias('my_json_bool', 'myTestBool')]

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
            v1 = True
            v1_dump_case = 'C'
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
        class _(JSONWizard.Meta):
            v1 = True

        my_str: str
        # v1: map load alias + disable dump
        other_str: Annotated[str, Alias(load='AnotherStr', skip=True)]
        my_bool: bool = Alias(load='TestBool', skip=True)
        my_int: int = 3

    data = {'my_str': 'my string',
            'AnotherStr': 'testing 123',
            'TestBool': True}

    c = MyClass.from_dict(data)
    log.debug('Instance: %r', c)

    additional_exclude = ('my_int', )

    out_dict = c.to_dict(exclude=additional_exclude)
    assert out_dict == {'my_str': 'my string'}


@pytest.mark.xfail(reason='I will fix this in next minor release!')
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
        class _(JSONSerializable.Meta):
            v1 = True

        num_set: Set[int]
        any_set: set

    expected = sorted(expected)

    input_set = set(input)
    c = MyClass(num_set=input_set, any_set=input_set)

    with expectation:
        result = c.to_dict()
        log.debug('Parsed object: %r', result)

        assert all(key in result for key in ('numSet', 'anySet'))
        assert isinstance(result['numSet'], (list, tuple))
        assert isinstance(result['anySet'], (list, tuple))

        assert sorted(result['numSet']) == expected
        assert sorted(result['anySet']) == expected


@pytest.mark.xfail(reason='I will fix this in next minor release!')
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
        class _(JSONSerializable.Meta):
            v1 = True

        num_set: FrozenSet[int]
        any_set: frozenset

    expected = sorted(expected)

    input_set = frozenset(input)
    c = MyClass(num_set=input_set, any_set=input_set)

    with expectation:
        result = c.to_dict()
        log.debug('Parsed object: %r', result)

        assert all(key in result for key in ('numSet', 'anySet'))
        assert isinstance(result['numSet'], (list, tuple))
        assert isinstance(result['anySet'], (list, tuple))

        assert sorted(result['numSet']) == expected
        assert sorted(result['anySet']) == expected


@pytest.mark.xfail(reason='I will fix this in next minor release!')
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
        class _(JSONSerializable.Meta):
            v1 = True

        num_deque: deque[int]
        any_deque: deque

    input_deque = deque(input)
    c = MyQClass(num_deque=input_deque, any_deque=input_deque)

    with expectation:
        result = c.to_dict()
        log.debug('Parsed object: %r', result)

        assert all(key in result for key in ('numDeque', 'anyDeque'))
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
        class _(JSONSerializable.Meta):
            v1 = True
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
        class _(JSONSerializable.Meta):
            v1 = True
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
        class _(JSONSerializable.Meta):
            v1 = True
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
        ({}, pytest.raises(ParseError)),
        ({'key': 'value'}, pytest.raises(ParseError)),
        ({'my_str': 'test', 'my_int': 2,
          'my_bool': True, 'other_key': 'testing'}, does_not_raise()),
        ({'my_str': 3}, pytest.raises(ParseError)),
        ({'my_str': 'test', 'my_int': 'test', 'my_bool': True}, pytest.raises(ValueError)),
        ({'my_str': 'test', 'my_int': 2, 'my_bool': True}, does_not_raise()),
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
        class _(JSONSerializable.Meta):
            v1 = True

        my_typed_dict: MyDict

    c = MyClass(my_typed_dict=input)

    with expectation:
        result = c.to_dict()
        log.debug('Parsed object: %r', result)


def test_using_dataclass_in_dict():
    """
    Using dataclass in a dictionary (i.e., dict[str, Test])
    works as expected.

    See https://github.com/rnag/dataclass-wizard/issues/159
    """
    @dataclass
    class Test:
        field: str

    @dataclass
    class Config:
        tests: dict[str, Test]

    config = {"tests": {"test_a": {"field": "a"}, "test_b": {"field": "b"}}}

    # v1 opt-in for plain dataclasses used with fromdict/asdict
    LoadMeta(v1=True).bind_to(Config)
    LoadMeta(v1=True).bind_to(Test)

    assert fromdict(Config, config) == Config(
        tests={'test_a': Test(field='a'),
               'test_b': Test(field='b')})


def test_bytes_and_bytes_array_are_supported():
    """Confirm dump with `bytes` and `bytesarray` is supported."""

    @dataclass
    class Foo(JSONWizard, debug=True):
        class _(JSONWizard.Meta):
            v1 = True

        b: bytes = None
        barray: bytearray = None
        s: str = None

    data = {'b': 'AAAA', 'barray': 'SGVsbG8sIFdvcmxkIQ==', 's': 'foobar'}

    foo = Foo(b=b64decode('AAAA'),
              barray=bytearray(b'Hello, World!'),
              s='foobar')

    assert foo.to_dict() == data
