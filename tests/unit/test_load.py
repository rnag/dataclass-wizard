"""
Tests for the `loaders` module, but more importantly for the `parsers` module.

Note: I might refactor this into a separate `test_parsers.py` as time permits.
"""
import logging
from collections import namedtuple, defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, date, time
from typing import (
    List, Optional, Union, Tuple, Dict, NamedTuple, Type, DefaultDict,
    Set, FrozenSet
)

import pytest

from dataclass_wizard import JSONSerializable, json_field, json_key
from dataclass_wizard.errors import ParseError
from dataclass_wizard.parsers import OptionalParser, Parser
from dataclass_wizard.type_def import NoneType, T
from .conftest import MyUUIDSubclass
from ..conftest import *


log = logging.getLogger(__name__)


@pytest.mark.parametrize(
    'input,expected',
    [
        (True, True),
        ('TrUe', True),
        ('y', True),
        ('T', True),
        (1, True),
        (False, False),
        ('False', False),
        ('testing', False),
        (0, False),
    ]
)
def test_bool(input, expected):

    @dataclass
    class MyClass(JSONSerializable):
        my_bool: bool

    d = {'My_Bool': input}

    result = MyClass.from_dict(d)
    log.debug('Parsed object: %r', result)

    assert result.my_bool == expected


def test_from_dict_key_transform_with_json_field():
    """
    Specifying a custom mapping of JSON key to dataclass field, via the
    `json_field` helper function.
    """

    @dataclass
    class MyClass(JSONSerializable):
        my_str: str = json_field('myCustomStr')
        my_bool: bool = json_field(('my_json_bool', 'myTestBool'))

    value = 'Testing'
    d = {'myCustomStr': value, 'myTestBool': 'true'}

    result = MyClass.from_dict(d)
    log.debug('Parsed object: %r', result)

    assert result.my_str == value
    assert result.my_bool is True


def test_from_dict_key_transform_with_json_key():
    """
    Specifying a custom mapping of JSON key to dataclass field, via the
    `json_key` helper function.
    """

    @dataclass
    class MyClass(JSONSerializable):
        my_str: Annotated[str, json_key('myCustomStr')]
        my_bool: Annotated[bool, json_key('my_json_bool', 'myTestBool')]

    value = 'Testing'
    d = {'myCustomStr': value, 'myTestBool': 'true'}

    result = MyClass.from_dict(d)
    log.debug('Parsed object: %r', result)

    assert result.my_str == value
    assert result.my_bool is True


@pytest.mark.parametrize(
    'input,expected,expectation',
    [
        ([1, '2', 3], {1, 2, 3}, does_not_raise()),
        ('TrUe', True, pytest.raises(ParseError)),
        ((3.22, 2.11, 1.22), {3, 2, 1}, does_not_raise()),
    ]
)
def test_set(input, expected, expectation):

    @dataclass
    class MyClass(JSONSerializable):
        num_set: Set[int]
        any_set: set

    d = {'numSet': input, 'any_set': input}

    with expectation:
        result = MyClass.from_dict(d)
        log.debug('Parsed object: %r', result)

        assert isinstance(result.num_set, set)
        assert isinstance(result.any_set, set)

        assert result.num_set == expected
        assert result.any_set == set(input)


@pytest.mark.parametrize(
    'input,expected,expectation',
    [
        ([1, '2', 3], {1, 2, 3}, does_not_raise()),
        ('TrUe', True, pytest.raises(ParseError)),
        ((3.22, 2.11, 1.22), {1, 2, 3}, does_not_raise()),
    ]
)
def test_frozenset(input, expected, expectation):

    @dataclass
    class MyClass(JSONSerializable):
        num_set: FrozenSet[int]
        any_set: frozenset

    d = {'numSet': input, 'any_set': input}

    with expectation:
        result = MyClass.from_dict(d)
        log.debug('Parsed object: %r', result)

        assert isinstance(result.num_set, frozenset)
        assert isinstance(result.any_set, frozenset)

        assert result.num_set == expected
        assert result.any_set == frozenset(input)


@pytest.mark.parametrize(
    'input,expectation',
    [
        ('testing', pytest.raises(ParseError)),
        ('e1', does_not_raise()),
        (False, pytest.raises(ParseError)),
        (0, does_not_raise()),
    ]
)
def test_literal(input, expectation):

    @dataclass
    class MyClass(JSONSerializable):
        my_lit: Literal['e1', 'e2', 0]

    d = {'MyLit': input}

    with expectation:
        result = MyClass.from_dict(d)
        log.debug('Parsed object: %r', result)


@pytest.mark.parametrize(
    'input,expected',
    [
        (True, True),
        (None, None),
        ('TrUe', True),
        ('y', True),
        ('T', True),
        ('F', False),
        (1, True),
        (False, False),
        (0, False),
    ]
)
def test_annotated(input, expected):

    @dataclass(unsafe_hash=True)
    class MaxLen:
        length: int

    @dataclass
    class MyClass(JSONSerializable):
        bool_or_none: Annotated[Optional[bool], MaxLen(23), "testing", 123]

    d = {'Bool-OR-None': input}

    result = MyClass.from_dict(d)
    log.debug('Parsed object: %r', result)

    assert result.bool_or_none == expected


@pytest.mark.parametrize(
    'input',
    [
        '12345678-1234-1234-1234-1234567abcde',
        '{12345678-1234-5678-1234-567812345678}',
        '12345678123456781234567812345678',
        'urn:uuid:12345678-1234-5678-1234-567812345678'
    ]
)
def test_uuid(input):

    @dataclass
    class MyUUIDTestClass(JSONSerializable):
        my_id: MyUUIDSubclass

    d = {'MyID': input}

    result = MyUUIDTestClass.from_dict(d)
    log.debug('Parsed object: %r', result)

    expected = MyUUIDSubclass(input)

    assert result.my_id == expected
    assert isinstance(result.my_id, MyUUIDSubclass)


@pytest.mark.parametrize(
    'input,expectation,expected',
    [
        ('testing', does_not_raise(), 'testing'),
        (False, does_not_raise(), 'False'),
        (0, does_not_raise(), '0'),
        (None, does_not_raise(), None),
    ]
)
def test_optional(input, expectation, expected):

    @dataclass
    class MyClass(JSONSerializable):
        my_str: str
        my_opt_str: Optional[str]

    d = {'MyStr': input, 'MyOptStr': input}

    with expectation:
        result = MyClass.from_dict(d)
        log.debug('Parsed object: %r', result)

        assert result.my_opt_str == expected
        if input is None:
            assert result.my_str == '', \
                'expected `my_str` to be set to an empty string'


@pytest.mark.parametrize(
    'input,expectation,expected',
    [
        ('testing', does_not_raise(), 'testing'),
        # The actual value would end up being 0 (int) if we checked the type
        # using `isinstance` instead. However, we do an exact `type` check for
        # :class:`Union` types.
        #
        # NOTE: This is an xfail on Python 3.6 as mentioned below.
        # https://stackoverflow.com/q/60154326/10237506
        pytest.param(False, does_not_raise(), False,
                     marks=pytest.mark.skipif(
                         PY36, reason='requires python 3.7 or higher')),
        (0, does_not_raise(), 0),
        (None, does_not_raise(), None),
        # Since it's a float value, that results in a `TypeError` which gets
        # re-raised.
        (1.2, pytest.raises(ParseError), None)
    ]
)
def test_union(input, expectation, expected):

    @dataclass
    class MyClass(JSONSerializable):
        my_opt_str_int_or_bool: Union[str, int, bool, None]

    d = {'myOptSTRIntORBool': input}

    with expectation:
        result = MyClass.from_dict(d)
        log.debug('Parsed object: %r', result)

        assert result.my_opt_str_int_or_bool == expected


def test_forward_refs_are_resolved():
    """
    Confirm that :class:`typing.ForwardRef` usages, such as `List['B']`,
    are resolved correctly.

    """
    @dataclass
    class A(JSONSerializable):
        b: List['B']
        c: 'C'

    @dataclass
    class B:
        optional_int: Optional[int] = None

    @dataclass
    class C:
        my_str: str

    # This is trick that allows us to treat classes A, B, and C as if they
    # were defined at the module level. Otherwise, the forward refs won't
    # resolve as expected.
    globals().update(locals())

    d = {'b': [{}], 'c': {'my_str': 'testing'}}

    a = A.from_dict(d)

    log.debug(a)


@pytest.mark.parametrize(
    'input,expectation',
    [
        ('testing', pytest.raises(ValueError)),
        ('2020-01-02T01:02:03Z', does_not_raise()),
        ('2010-12-31 23:59:59-04:00', does_not_raise()),
        (123456789, does_not_raise()),
        (True, pytest.raises(TypeError)),
        (datetime(2010, 12, 31, 23, 59, 59), does_not_raise()),
    ]
)
def test_datetime(input, expectation):

    @dataclass
    class MyClass(JSONSerializable):
        my_dt: datetime

    d = {'myDT': input}

    with expectation:
        result = MyClass.from_dict(d)
        log.debug('Parsed object: %r', result)


@pytest.mark.parametrize(
    'input,expectation',
    [
        ('testing', pytest.raises(ValueError)),
        ('2020-01-02', does_not_raise()),
        ('2010-12-31', does_not_raise()),
        (123456789, does_not_raise()),
        (True, pytest.raises(TypeError)),
        (date(2010, 12, 31), does_not_raise()),
    ]
)
def test_date(input, expectation):

    @dataclass
    class MyClass(JSONSerializable):
        my_d: date

    d = {'myD': input}

    with expectation:
        result = MyClass.from_dict(d)
        log.debug('Parsed object: %r', result)


@pytest.mark.parametrize(
    'input,expectation',
    [
        ('testing', pytest.raises(ValueError)),
        ('01:02:03Z', does_not_raise()),
        ('23:59:59-04:00', does_not_raise()),
        (123456789, pytest.raises(TypeError)),
        (True, pytest.raises(TypeError)),
        (time(23, 59, 59), does_not_raise()),
    ]
)
def test_time(input, expectation):

    @dataclass
    class MyClass(JSONSerializable):
        my_t: time

    d = {'myT': input}

    with expectation:
        result = MyClass.from_dict(d)
        log.debug('Parsed object: %r', result)


@pytest.mark.parametrize(
    'input,expectation,expected',
    [
        (
            # For the `int` parser, only do explicit type checks against
            # `bool` currently (which is a special case) so this is expected
            # to pass.
            [{}], does_not_raise(), [0]),
        (
            # `bool` is a sub-class of int, so we explicitly check for this
            # type.
            [True, False], pytest.raises(TypeError), None),
        (
            ['hello', 'world'], pytest.raises(ValueError), None
        ),
        (
            [1, 'two', 3], pytest.raises(ValueError), None),
        (
            [1, '2', 3], does_not_raise(), [1, 2, 3]
        ),
        (
            'testing', pytest.raises(ParseError), None
        ),
    ]
)
def test_list(input, expectation, expected):

    @dataclass
    class MyClass(JSONSerializable):
        my_list: List[int]

    d = {'My_List': input}

    with expectation:
        result = MyClass.from_dict(d)

        log.debug('Parsed object: %r', result)
        assert result.my_list == expected


@pytest.mark.parametrize(
    'input,expectation,expected',
    [
        (
            ['hello', 'world'], pytest.raises(ParseError), None
        ),
        (
            [1, '2', 3], does_not_raise(), [1, 2, 3]
        ),
    ]
)
def test_deque(input, expectation, expected):

    @dataclass
    class MyClass(JSONSerializable):
        my_deque: Deque[int]

    d = {'My_Deque': input}

    with expectation:
        result = MyClass.from_dict(d)

        log.debug('Parsed object: %r', result)

        assert isinstance(result.my_deque, deque)
        assert list(result.my_deque) == expected


@pytest.mark.parametrize(
    'input,expectation,expected',
    [
        (
            [{}], does_not_raise(), [{}]),
        (
            [True, False], does_not_raise(), [True, False]),
        (
            ['hello', 'world'], does_not_raise(), ['hello', 'world']
        ),
        (
            [1, 'two', 3], does_not_raise(), [1, 'two', 3]),
        (
            [1, '2', 3], does_not_raise(), [1, '2', 3]
        ),
        # TODO maybe we should raise an error in this case?
        (
            'testing', does_not_raise(),
            ['t', 'e', 's', 't', 'i', 'n', 'g']
        ),
    ]
)
def test_list_without_type_hinting(input, expectation, expected):
    """
    Test case for annotating with a bare `list` (acts as just a pass-through
    for its elements)
    """

    @dataclass
    class MyClass(JSONSerializable):
        my_list: list

    d = {'My_List': input}

    with expectation:
        result = MyClass.from_dict(d)

        log.debug('Parsed object: %r', result)
        assert result.my_list == expected


@pytest.mark.parametrize(
    'input,expectation,expected',
    [
        (
            # Wrong number of elements (technically the wrong type)
            [{}], pytest.raises(ParseError), None),
        (
            [True, False, True], pytest.raises(TypeError), None),
        (
            [1, 'hello'], pytest.raises(ParseError), None
        ),
        (
            ['1', 'two', True], does_not_raise(), (1, 'two', True)),
        (
            'testing', pytest.raises(ParseError), None
        ),
    ]
)
def test_tuple(input, expectation, expected):

    @dataclass
    class MyClass(JSONSerializable):
        my_tuple: Tuple[int, str, bool]

    d = {'My__Tuple': input}

    with expectation:
        result = MyClass.from_dict(d)

        log.debug('Parsed object: %r', result)
        assert result.my_tuple == expected


@pytest.mark.parametrize(
    'input,expectation,expected',
    [
        (
            # Wrong number of elements (technically the wrong type)
            [{}], pytest.raises(ParseError), None),
        (
            [True, False, True], pytest.raises(TypeError), None),
        (
            [1, 'hello'], does_not_raise(), (1, 'hello')
        ),
        (
            ['1', 'two', 'tRuE'], does_not_raise(), (1, 'two', True)),
        (
            ['1', 'two', None, 3], does_not_raise(), (1, 'two', None, 3)),
        (
            ['1', 'two', 'false', None], does_not_raise(),
            (1, 'two', False, None)),
        (
            'testing', pytest.raises(ParseError), None
        ),
    ]
)
def test_tuple_with_optional_args(input, expectation, expected):
    """
    Test case when annotated type has any "optional" arguments, such as
    `Tuple[str, Optional[int]]` or
    `Tuple[bool, Optional[str], Union[int, None]]`.
    """

    @dataclass
    class MyClass(JSONSerializable):
        my_tuple: Tuple[int, str, Optional[bool], Union[str, int, None]]

    d = {'My__Tuple': input}

    with expectation:
        result = MyClass.from_dict(d)

        log.debug('Parsed object: %r', result)
        assert result.my_tuple == expected


@pytest.mark.parametrize(
    'input,expectation,expected',
    [
        (
            # This is when we don't really specify what elements the tuple is
            # expected to contain.
            [{}], does_not_raise(), ({},)),
        (
            [True, False, True], does_not_raise(), (True, False, True)),
        (
            [1, 'hello'], does_not_raise(), (1, 'hello')
        ),
        (
            ['1', 'two', True], does_not_raise(), ('1', 'two', True)),
        (
            'testing', does_not_raise(),
            ('t', 'e', 's', 't', 'i', 'n', 'g')
        ),
    ]
)
def test_tuple_without_type_hinting(input, expectation, expected):
    """
    Test case for annotating with a bare `tuple` (acts as just a pass-through
    for its elements)
    """
    @dataclass
    class MyClass(JSONSerializable):
        my_tuple: tuple

    d = {'My__Tuple': input}

    with expectation:
        result = MyClass.from_dict(d)

        log.debug('Parsed object: %r', result)
        assert result.my_tuple == expected


@pytest.mark.parametrize(
    'input,expectation,expected',
    [
        (
            # Technically this is the wrong type (dict != int) however the
            # conversion to `int` still succeeds. Might need to change this
            # behavior later if needed.
            [{}], does_not_raise(), (0, )),
        (
            [True, False, True], pytest.raises(TypeError), None),
        (
            # Raises a `ValueError` because `hello` cannot be converted to int
            [1, 'hello'], pytest.raises(ValueError), None
        ),
        (
            [1], does_not_raise(), (1, )),
        (
            ['1', 2, '3'], does_not_raise(), (1, 2, 3)),
        (
            ['1', '2', None, '4', 5, 6, '7'], does_not_raise(),
            (1, 2, 0, 4, 5, 6, 7)),
        (
            'testing', pytest.raises(ValueError), None
        ),
    ]
)
def test_tuple_with_variadic_args(input, expectation, expected):
    """
    Test case when annotated type is in the "variadic" format, i.e.
    `Tuple[str, ...]`
    """

    @dataclass
    class MyClass(JSONSerializable):
        my_tuple: Tuple[int, ...]

    d = {'My__Tuple': input}

    with expectation:
        result = MyClass.from_dict(d)

        log.debug('Parsed object: %r', result)
        assert result.my_tuple == expected


@pytest.mark.parametrize(
    'input,expectation,expected',
    [
        (
            None, pytest.raises(AttributeError), None
        ),
        (
            {}, does_not_raise(), {}
        ),
        (
            # Wrong types for both key and value
            {'key': 'value'}, pytest.raises(ValueError), None),
        (
            {'1': 'test', '2': 't', '3': 'false'}, does_not_raise(),
            {1: False, 2: True, 3: False}
        ),
        (
            {2: None}, does_not_raise(), {2: False}
        ),
        (
            # Incorrect type - `list`, but should be a `dict`
            [{'my_str': 'test', 'my_int': 2, 'my_bool': True}],
            pytest.raises(AttributeError), None
        )
    ]
)
def test_dict(input, expectation, expected):

    @dataclass
    class MyClass(JSONSerializable):
        my_dict: Dict[int, bool]

    d = {'myDict': input}

    with expectation:
        result = MyClass.from_dict(d)

        log.debug('Parsed object: %r', result)
        assert result.my_dict == expected


@pytest.mark.parametrize(
    'input,expectation,expected',
    [
        (
            None, pytest.raises(AttributeError), None
        ),
        (
            {}, does_not_raise(), {}
        ),
        (
            # Wrong types for both key and value
            {'key': 'value'}, pytest.raises(ValueError), None),
        (
            {'1': 'test', '2': 't', '3': ['false']}, does_not_raise(),
            {1: ['t', 'e', 's', 't'],
             2: ['t'],
             3: ['false']}
        ),
        (
            # Might need to change this behavior if needed: currently it
            # raises an error, which I think is good for now since we don't
            # want to add `null`s to a list anyway.
            {2: None}, pytest.raises(ParseError), None
        ),
        (
            # Incorrect type - `list`, but should be a `dict`
            [{'my_str': 'test', 'my_int': 2, 'my_bool': True}],
            pytest.raises(AttributeError), None
        )
    ]
)
def test_default_dict(input, expectation, expected):

    @dataclass
    class MyClass(JSONSerializable):
        my_def_dict: DefaultDict[int, list]

    d = {'myDefDict': input}

    with expectation:
        result = MyClass.from_dict(d)

        log.debug('Parsed object: %r', result)
        assert isinstance(result.my_def_dict, defaultdict)
        assert result.my_def_dict == expected


@pytest.mark.parametrize(
    'input,expectation,expected',
    [
        (
            None, pytest.raises(AttributeError), None
        ),
        (
            {}, does_not_raise(), {}
        ),
        (
            # Wrong types for both key and value
            {'key': 'value'}, does_not_raise(), {'key': 'value'}),
        (
            {'1': 'test', '2': 't', '3': 'false'}, does_not_raise(),
            {'1': 'test', '2': 't', '3': 'false'}
        ),
        (
            {2: None}, does_not_raise(), {2: None}
        ),
        (
            # Incorrect type - `list`, but should be a `dict`
            [{'my_str': 'test', 'my_int': 2, 'my_bool': True}],
            pytest.raises(AttributeError), None
        )
    ]
)
def test_dict_without_type_hinting(input, expectation, expected):
    """
    Test case for annotating with a bare `dict` (acts as just a pass-through
    for its key-value pairs)
    """
    @dataclass
    class MyClass(JSONSerializable):
        my_dict: dict

    d = {'myDict': input}

    with expectation:
        result = MyClass.from_dict(d)

        log.debug('Parsed object: %r', result)
        assert result.my_dict == expected


@pytest.mark.parametrize(
    'input,expectation,expected',
    [
        (
            {}, pytest.raises(ParseError), None
        ),
        (
            {'key': 'value'}, pytest.raises(ParseError), {}
        ),
        (
            {'my_str': 'test', 'my_int': 2,
             'my_bool': True, 'other_key': 'testing'}, does_not_raise(),
            {'my_str': 'test', 'my_int': 2, 'my_bool': True}
        ),
        (
            {'my_str': 3}, pytest.raises(ParseError), None
        ),
        (
            {'my_str': 'test', 'my_int': 'test', 'my_bool': True},
            pytest.raises(ValueError), None
        ),
        (
            {'my_str': 'test', 'my_int': 2, 'my_bool': True},
            does_not_raise(),
            {'my_str': 'test', 'my_int': 2, 'my_bool': True}
        ),
        (
            # Incorrect type - `list`, but should be a `dict`
            [{'my_str': 'test', 'my_int': 2, 'my_bool': True}],
            pytest.raises(ParseError), None
        )
    ]
)
def test_typed_dict(input, expectation, expected):

    class MyDict(TypedDict):
        my_str: str
        my_bool: bool
        my_int: int

    @dataclass
    class MyClass(JSONSerializable):
        my_typed_dict: MyDict

    d = {'myTypedDict': input}

    with expectation:
        result = MyClass.from_dict(d)

        log.debug('Parsed object: %r', result)
        assert result.my_typed_dict == expected


@pytest.mark.parametrize(
    'input,expectation,expected',
    [
        (
            {}, does_not_raise(), {}
        ),
        (
            {'key': 'value'}, does_not_raise(), {}
        ),
        (
            {'my_str': 'test', 'my_int': 2,
             'my_bool': True, 'other_key': 'testing'}, does_not_raise(),
            {'my_str': 'test', 'my_int': 2, 'my_bool': True}
        ),
        (
            {'my_str': 3}, does_not_raise(), {'my_str': '3'}
        ),
        (
            {'my_str': 'test', 'my_int': 'test', 'my_bool': True},
            pytest.raises(ValueError),
            {'my_str': 'test', 'my_int': 'test', 'my_bool': True}
        ),
        (
            {'my_str': 'test', 'my_int': 2, 'my_bool': True},
            does_not_raise(),
            {'my_str': 'test', 'my_int': 2, 'my_bool': True}
        )
    ]
)
def test_typed_dict_with_optional_fields(input, expectation, expected):
    """
    Test case for loading to a TypedDict which has `total=False`, indicating
    that all fields are optional.

    """
    class MyDict(TypedDict, total=False):
        my_str: str
        my_bool: bool
        my_int: int

    @dataclass
    class MyClass(JSONSerializable):
        my_typed_dict: MyDict

    d = {'myTypedDict': input}

    with expectation:
        result = MyClass.from_dict(d)

        log.debug('Parsed object: %r', result)
        assert result.my_typed_dict == expected


@pytest.mark.parametrize(
    'input,expectation,expected',
    [
        # TODO I guess these all technically should raise a ParseError
        (
            {}, pytest.raises(TypeError), None
        ),
        (
            {'key': 'value'}, pytest.raises(KeyError), {}
        ),
        (
            {'my_str': 'test', 'my_int': 2,
             'my_bool': True, 'other_key': 'testing'},
            # Unlike a TypedDict, extra arguments to a `NamedTuple` should
            # result in an error
            pytest.raises(KeyError), None
        ),
        (
            {'my_str': 'test', 'my_int': 'test', 'my_bool': True},
            pytest.raises(ValueError), None
        ),
        (
            # Should raise a `TypeError` (types for last two are wrong)
            ['test', 2, True],
            pytest.raises(TypeError), None
        ),
        (
            ['test', True, 2],
            does_not_raise(),
            ('test', True, 2)
        ),
        (
            {'my_str': 'test', 'my_int': 2, 'my_bool': True},
            does_not_raise(),
            {'my_str': 'test', 'my_int': 2, 'my_bool': True}
        ),
    ]
)
def test_named_tuple(input, expectation, expected):

    class MyNamedTuple(NamedTuple):
        my_str: str
        my_bool: bool
        my_int: int

    @dataclass
    class MyClass(JSONSerializable):
        my_nt: MyNamedTuple

    d = {'myNT': input}

    with expectation:
        result = MyClass.from_dict(d)

        log.debug('Parsed object: %r', result)
        if isinstance(expected, dict):
            expected = MyNamedTuple(**expected)

        assert result.my_nt == expected


@pytest.mark.parametrize(
    'input,expectation,expected',
    [
        # TODO I guess these all technically should raise a ParseError
        (
            {}, pytest.raises(TypeError), None
        ),
        (
            {'key': 'value'}, pytest.raises(TypeError), {}
        ),
        (
            {'my_str': 'test', 'my_int': 2,
             'my_bool': True, 'other_key': 'testing'},
            # Unlike a TypedDict, extra arguments to a `namedtuple` should
            # result in an error
            pytest.raises(TypeError), None
        ),
        (
            {'my_str': 'test', 'my_int': 'test', 'my_bool': True},
            does_not_raise(), ('test', True, 'test')
        ),
        (
            ['test', 2, True],
            does_not_raise(), ('test', 2, True)
        ),
        (
            ['test', True, 2],
            does_not_raise(),
            ('test', True, 2)
        ),
        (
            {'my_str': 'test', 'my_int': 2, 'my_bool': True},
            does_not_raise(),
            {'my_str': 'test', 'my_int': 2, 'my_bool': True}
        ),
    ]
)
def test_named_tuple_without_type_hinting(input, expectation, expected):
    """
    Test case for annotating with a bare :class:`collections.namedtuple`. In
    this case, we lose out on proper type checking and conversion, but at
    least we still have a check on the parameter names, as well as the no. of
    expected elements.

    """
    MyNamedTuple = namedtuple('MyNamedTuple', ['my_str', 'my_bool', 'my_int'])

    @dataclass
    class MyClass(JSONSerializable):
        my_nt: MyNamedTuple

    d = {'myNT': input}

    with expectation:
        result = MyClass.from_dict(d)

        log.debug('Parsed object: %r', result)
        if isinstance(expected, dict):
            expected = MyNamedTuple(**expected)

        assert result.my_nt == expected


@pytest.mark.parametrize(
    'input,expected',
    [
        (None, True),
        (NoneType, False),
        ('hello world', True),
        (123, False),
    ]
)
def test_optional_parser_contains(input, expected):
    """
    Test case for :meth:`OptionalParser.__contains__`, added for code
    coverage.

    """
    base_type: Type[T] = str
    mock_parser = Parser(None, None, lambda: None)
    optional_parser = OptionalParser(
        None, base_type, lambda a, b: mock_parser)

    actual = input in optional_parser
    assert actual == expected


def test_parser_with_unsupported_type():
    """
    Test case for :meth:`Parser.__call__` with an unknown or unsupported
    type, added for code coverage.

    """
    base_type: Type[T] = str
    mock_parser = Parser(None, base_type, hook=None)

    with pytest.raises(ParseError):
        _ = mock_parser('hello world')
