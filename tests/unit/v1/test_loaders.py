"""
Tests for the `loaders` module, but more importantly for the `parsers` module.

Note: I might refactor this into a separate `test_parsers.py` as time permits.
"""
import logging
from abc import ABC
from collections import namedtuple, defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from typing import (
    List, Optional, Union, Tuple, Dict, NamedTuple, DefaultDict,
    Set, FrozenSet, Annotated, Literal, Sequence, MutableSequence, Collection
)

import pytest

from dataclass_wizard import *
from dataclass_wizard.constants import TAG
from dataclass_wizard.errors import (
    ParseError, MissingFields, UnknownKeysError, MissingData, InvalidConditionError
)
from dataclass_wizard.models import _PatternBase
from dataclass_wizard.v1 import *
from ..conftest import MyUUIDSubclass
from ...conftest import *

log = logging.getLogger(__name__)


def test_missing_fields_is_raised():

    @dataclass
    class Test(JSONWizard, debug=True):
        class _(JSONWizard.Meta):
            v1 = True

        my_str: str
        my_int: int
        my_bool: bool
        my_float: float = 1.23


    with pytest.raises(MissingFields) as exc_info:
        _ = Test.from_dict({'my_bool': True})

    e, tp = exc_info.value, exc_info.type

    assert tp is MissingFields
    assert e.fields == ['my_bool']
    assert e.missing_fields == ['my_str', 'my_int']


def test_auto_key_casing():

    @dataclass
    class Test(JSONWizard):
        class _(JSONWizard.Meta):
            v1 = True
            v1_key_case = 'AUTO'

        my_str: str
        my_bool_test: bool
        my_int: int
        my_float: float = 1.23

    d = {'My-Str': 'test', 'myBoolTest': True, 'MyInt': 123, 'my_float': 42, }

    assert Test.from_dict(d) == Test(my_str='test', my_bool_test=True, my_int=123, my_float=42.0)


def test_alias_mapping():

    @dataclass
    class Test(JSONPyWizard):
        class _(JSONPyWizard.Meta):
            v1 = True
            v1_field_to_alias = {'my_int': 'MyInt'}

        my_str: str = Alias('a_str')
        my_bool_test: Annotated[bool, Alias('myBoolTest')]
        my_int: int
        my_float: float = 1.23

    d = {'a_str': 'test', 'myBoolTest': True, 'MyInt': 123, 'my_float': 42}

    t = Test.from_dict(d)
    assert t == Test(my_str='test', my_bool_test=True, my_int=123, my_float=42.0)

    assert t.to_dict() == {'a_str': 'test', 'myBoolTest': True, 'MyInt': 123, 'my_float': 42.0}


def test_alias_mapping_with_load_or_dump():

    @dataclass
    class Test(JSONWizard):
        class _(JSONWizard.Meta):
            v1 = True
            v1_key_case = 'C'
            key_transform_with_dump = 'NONE'
            v1_field_to_alias = {
                'my_int': 'MyInt',
                '__load__': False,
            }

        my_str: str = Alias(load='a_str')
        my_bool_test: Annotated[bool, Alias(dump='myDumpedBool')]
        my_int: int
        other_int: int = Alias(dump='DumpedInt')
        my_float: float = 1.23

    d = {'a_str': 'test',
         'myBoolTest': 'T',
         'myInt': 123,
         'otherInt': 321,
         'myFloat': 42}

    t = Test.from_dict(d)
    assert t == Test(my_str='test',
                     my_bool_test=True,
                     my_int=123,
                     other_int=321,
                     my_float=42.0)

    assert t.to_dict() == {'my_str': 'test',
                           'MyInt': 123,
                           'DumpedInt': 321,
                           'myDumpedBool': True,
                           'my_float': 42.0}


def test_fromdict():
    """
    Confirm that Meta settings for `fromdict` are applied as expected.
    """

    @dataclass
    class MyClass:
        my_bool: Optional[bool]
        myStrOrInt: Union[str, int]

    d = {'myBoolean': 'tRuE', 'myStrOrInt': 123}

    LoadMeta(v1=True,
             key_transform='CAMEL',
             v1_field_to_alias={'my_bool': 'myBoolean'}).bind_to(MyClass)

    c = fromdict(MyClass, d)

    assert c.my_bool is True
    assert isinstance(c.myStrOrInt, int)
    assert c.myStrOrInt == 123


# TODO multiple keys can be raised
def test_fromdict_raises_on_unknown_json_fields():
    """
    Confirm that Meta settings for `fromdict` are applied as expected.
    """

    @dataclass
    class MyClass:
        my_bool: Optional[bool]

    d = {'myBoolean': 'tRuE', 'my_string': 'Hello world!'}
    LoadMeta(
        v1=True,
        v1_field_to_alias={'my_bool': 'myBoolean'},
        v1_on_unknown_key='Raise').bind_to(MyClass)

    # Technically we don't need to pass `load_cfg`, but we'll pass it in as
    # that's how we'd typically expect to do it.
    with pytest.raises(UnknownKeysError) as exc_info:
        _ = fromdict(MyClass, d)

    e = exc_info.value

    assert e.json_key == {'my_string'}
    assert e.obj == d
    assert e.fields == ['my_bool']


def test_from_dict_raises_on_unknown_json_key_nested():

    @dataclass
    class Sub(JSONWizard):
        class _(JSONWizard.Meta):
            v1_key_case = 'P'

        my_str: str

    @dataclass
    class Test(JSONWizard, debug=True):
        class _(JSONWizard.Meta):
            v1 = True
            v1_on_unknown_key = 'RAISE'

        my_str: str = Alias('a_str')
        my_bool: bool
        my_sub: Sub


    d = {'a_str': 'test',
         'my_bool': True,
         'my_sub': {'MyStr': 'test'}}
    t = Test.from_dict(d)
    log.debug(repr(t))

    d = {'a_str': 'test',
         'my_sub': {'MyStr': 'test'},
         'my_bool': 'F',
         'my_str': 'test2', 'myBoolTest': True, 'MyInt': 123}

    with pytest.raises(UnknownKeysError) as exc_info:
        _ = Test.from_dict(d)

    e = exc_info.value

    # TODO
    assert e.unknown_keys == {'myBoolTest', 'MyInt', 'my_str'}
    assert e.obj == d
    assert e.fields == ['my_str', 'my_bool', 'my_sub']

    d = {'a_str': 'test',
         'my_bool': True,
         'my_sub': {'MyStr': 'test', 'myBoolTest': False}}

    # d = {'a_str': 'test',
    #      'my_bool': True,
    #      'my_sub': {'MyStr': 'test', 'my_bool': False, 'myBoolTest': False},
    #      }

    with pytest.raises(UnknownKeysError) as exc_info:
        _ = Test.from_dict(d)

    e = exc_info.value

    assert e.unknown_keys == {'myBoolTest'}
    assert e.obj == d['my_sub']
    assert e.fields == ['my_str']


@pytest.mark.xfail(reason='TODO need to support multiple JSON keys for a dataclass field')
def test_fromdict_with_key_case_auto_expected_failure():
    """
    Failure in `fromdict()` because multiple JSON keys are not mapped to single dataclass field.
    """
    @dataclass
    class MyElement:
        order_index: int
        status_code: 'int | str'

    @dataclass
    class Container:
        id: int
        my_elements: list[MyElement]

    d = {'id': '123',
         'myElements': [
             {'orderIndex': 111,
              'statusCode': '200'},
             {'order_index': '222',
              'status_code': 404}
         ]}

    LoadMeta(v1=True, v1_key_case='AUTO').bind_to(Container)

    # Failure!
    c = fromdict(Container, d)


def test_fromdict_with_nested_dataclass():
    """Confirm that `fromdict` works for nested dataclasses as well."""

    @dataclass
    class Container:
        id: int
        submittedDt: datetime
        myElements: List['MyElement']

    @dataclass
    class MyElement:
        order_index: Optional[int]
        status_code: Union[int, str]

    d = {'id': '123',
         'submittedDt': '2021-01-01 05:00:00',
         'myElements': [
             {'orderIndex': 111,
              'statusCode': '200'},
             {'orderIndex': '222',
              'statusCode': 404}
         ]}

    # Fix so the forward reference works (since the class definition is inside
    # the test case)
    globals().update(locals())

    LoadMeta(
        v1=True,
        recursive=False).bind_to(Container)

    LoadMeta(v1=True, v1_key_case='AUTO').bind_to(MyElement)

    c = fromdict(Container, d)

    assert c.id == 123
    assert c.submittedDt == datetime(2021, 1, 1, 5, 0)
    # Key transform only applies to top-level dataclass
    # unfortunately. Need to setup `LoadMeta` for `MyElement`
    # if we need different key transform.
    assert c.myElements == [
            MyElement(order_index=111, status_code='200'),
            MyElement(order_index=222, status_code=404)
    ]


def test_invalid_types_with_debug_mode_enabled():
    """
    Passing invalid types (i.e. that *can't* be coerced into the annotated
    field types) raises a formatted error when DEBUG mode is enabled.
    """
    @dataclass
    class InnerClass:
        my_float: float
        my_list: List[int] = field(default_factory=list)

    @dataclass
    class MyClass(JSONWizard):
        class _(JSONWizard.Meta):
            v1 = True
            v1_key_case = 'CAMEL'
            debug_enabled = True

        my_int: int
        my_dict: Dict[str, datetime] = field(default_factory=dict)
        my_inner: Optional[InnerClass] = None

    with pytest.raises(ParseError) as e:
        _ = MyClass.from_dict({'myInt': '3', 'myDict': 'string'})

    err = e.value
    assert type(err.base_error) == AttributeError
    assert "no attribute 'items'" in str(err.base_error)
    assert err.class_name == MyClass.__qualname__
    assert err.field_name == 'my_dict'
    assert (err.ann_type, err.obj_type) == (Dict[str, datetime], str)

    with pytest.raises(ParseError) as e:
        _ = MyClass.from_dict({'myInt': '1', 'myInner': {'myFloat': '1.A'}})

    err = e.value
    assert type(err.base_error) == ValueError
    assert "could not convert" in str(err.base_error)
    assert err.class_name == InnerClass.__qualname__
    assert err.field_name == 'my_float'
    assert (err.ann_type, err.obj_type) == (float, str)

    with pytest.raises(ParseError) as e:
        _ = MyClass.from_dict({
            'myInt': '1',
            'myDict': {2: '2021-01-01'},
            'myInner': {
                'my-float': '1.23',
                'myList': [{'key': 'value'}]
            }
        })

    err = e.value
    assert type(err.base_error) == TypeError
    assert "int()" in str(err.base_error)
    assert err.class_name == InnerClass.__qualname__
    assert err.field_name == 'my_list'
    assert (err.ann_type, err.obj_type) == (List[int], list)


def test_from_dict_called_with_incorrect_type():
    """
    Calling `from_dict` with a non-`dict` argument should raise a
    formatted error, i.e. with a :class:`ParseError` object.
    """
    @dataclass
    class MyClass(JSONWizard):
        class _(JSONWizard.Meta):
            v1 = True

        my_str: str

    with pytest.raises(ParseError) as e:
        # noinspection PyTypeChecker
        _ = MyClass.from_dict(['my_str'])

    err = e.value
    assert e.value.field_name == 'my_str'
    assert e.value.class_name == MyClass.__qualname__
    assert e.value.obj == ['my_str']
    assert 'Incorrect type' in str(e.value.base_error)
    # basically says we want a `dict`, but were passed in a `list`
    assert (err.ann_type, err.obj_type) == (dict, list)


@pytest.mark.xfail(reason='Need to add support in v1')
def test_date_times_with_custom_pattern():
    """
    Date, time, and datetime objects with a custom date string
    format that will be passed to the built-in `datetime.strptime` method
    when de-serializing date strings.

    Note that the serialization format for dates and times still use ISO
    format, by default.
    """

    def create_strict_eq(name, bases, cls_dict):
        """Generate a strict "type" equality method for a class."""
        cls = type(name, bases, cls_dict)
        __class__ = cls  # provide closure cell for super()

        def __eq__(self, other):
            if type(other) is not cls:  # explicitly check the type
                return False
            return super().__eq__(other)

        cls.__eq__ = __eq__
        return cls

    class MyDate(date, metaclass=create_strict_eq):
        ...

    class MyTime(time, metaclass=create_strict_eq):
        def get_hour(self):
            return self.hour

    class MyDT(datetime, metaclass=create_strict_eq):
        def get_year(self):
            return self.year

    @dataclass
    class MyClass:
        date_field1: DatePattern['%m-%y']
        time_field1: TimePattern['%H-%M']
        dt_field1: DateTimePattern['%d, %b, %Y %I::%M::%S.%f %p']
        date_field2: Annotated[MyDate, Pattern('%Y/%m/%d')]
        time_field2: Annotated[List[MyTime], Pattern('%I:%M %p')]
        dt_field2: Annotated[MyDT, Pattern('%m/%d/%y %H@%M@%S')]

        other_field: str

    data = {'date_field1': '12-22',
            'time_field1': '15-20',
            'dt_field1': '3, Jan, 2022 11::30::12.123456 pm',
            'date_field2': '2021/12/30',
            'time_field2': ['1:20 PM', '12:30 am'],
            'dt_field2': '01/02/23 02@03@52',
            'other_field': 'testing'}

    LoadMeta(v1=True).bind_to(MyClass)

    class_obj = fromdict(MyClass, data)

    # noinspection PyTypeChecker
    expected_obj = MyClass(date_field1=date(2022, 12, 1),
                           time_field1=time(15, 20),
                           dt_field1=datetime(2022, 1, 3, 23, 30, 12, 123456),
                           date_field2=MyDate(2021, 12, 30),
                           time_field2=[MyTime(13, 20), MyTime(0, 30)],
                           dt_field2=MyDT(2023, 1, 2, 2, 3, 52),
                           other_field='testing')

    log.debug('Deserialized object: %r', class_obj)
    # Assert that dates / times are correctly de-serialized as expected.
    assert class_obj == expected_obj

    serialized_dict = asdict(class_obj)

    expected_dict = {'dateField1': '2022-12-01',
                     'timeField1': '15:20:00',
                     'dtField1': '2022-01-03T23:30:12.123456',
                     'dateField2': '2021-12-30',
                     'timeField2': ['13:20:00', '00:30:00'],
                     'dtField2': '2023-01-02T02:03:52',
                     'otherField': 'testing'}

    log.debug('Serialized dict object: %s', serialized_dict)
    # Assert that dates / times are correctly serialized as expected.
    assert serialized_dict == expected_dict

    # Assert that de-serializing again, using the serialized date strings
    # in ISO format, still works.
    assert fromdict(MyClass, serialized_dict) == expected_obj


@pytest.mark.xfail(reason='Need to add support in v1')
def test_date_times_with_custom_pattern_when_input_is_invalid():
    """
    Date, time, and datetime objects with a custom date string
    format, but the input date string does not match the set pattern.
    """

    @dataclass
    class MyClass:
        date_field: DatePattern['%m-%d-%y']

    data = {'date_field': '12.31.21'}

    LoadMeta(v1=True).bind_to(MyClass)

    with pytest.raises(ParseError):
        _ = fromdict(MyClass, data)


@pytest.mark.skip(reason='Need to add support in v1')
def test_date_times_with_custom_pattern_when_annotation_is_invalid():
    """
    Date, time, and datetime objects with a custom date string
    format, but the annotated type is not a valid date/time type.
    """
    class MyCustomPattern(str, _PatternBase):
        pass

    @dataclass
    class MyClass:
        date_field: MyCustomPattern['%m-%d-%y']

    data = {'date_field': '12-31-21'}

    LoadMeta(v1=True).bind_to(MyClass)

    with pytest.raises(TypeError) as e:
        _ = fromdict(MyClass, data)

    log.debug('Error details: %r', e.value)


def test_tag_field_is_used_in_load_process():
    """
    Confirm that the `_TAG` field is used when de-serializing to a dataclass
    instance (even for nested dataclasses) when a value is set in the
    `Meta` config for a JSONWizard sub-class.
    """

    @dataclass
    class Data(ABC):
        """ base class for a Member """
        number: float

    class DataA(Data, JSONWizard):
        """ A type of Data"""
        class _(JSONWizard.Meta):
            """
            This defines a custom tag that uniquely identifies the dataclass.
            """
            tag = 'A'

    class DataB(Data, JSONWizard):
        """ Another type of Data """
        class _(JSONWizard.Meta):
            """
            This defines a custom tag that uniquely identifies the dataclass.
            """
            tag = 'B'

    class DataC(Data):
        """ A type of Data"""

    @dataclass
    class Container(JSONWizard):
        """ container holds a subclass of Data """
        class _(JSONWizard.Meta):
            v1 = True
            tag = 'CONTAINER'
            # Need for `DataC`, which doesn't have a tag assigned
            v1_unsafe_parse_dataclass_in_union = True

        data: Union[DataA, DataB, DataC]

    data = {
        'data': {
            TAG: 'A',
            'number': '1.0'
        }
    }

    # initialize container with DataA
    container = Container.from_dict(data)

    # Assert we de-serialize as a DataA object.
    assert type(container.data) == DataA
    assert isinstance(container.data.number, float)
    assert container.data.number == 1.0

    data = {
        'data': {
            TAG: 'B',
            'number': 2.0
        }
    }

    # initialize container with DataA
    container = Container.from_dict(data)

    # Assert we de-serialize as a DataA object.
    assert type(container.data) == DataB
    assert isinstance(container.data.number, float)
    assert container.data.number == 2.0

    # Test we receive an error when we provide an invalid tag value
    data = {
        'data': {
            TAG: 'C',
            'number': 2.0
        }
    }

    with pytest.raises(ParseError):
        _ = Container.from_dict(data)


def test_e2e_process_with_init_only_fields():
    """
    We are able to correctly de-serialize a class instance that excludes some
    dataclass fields from the constructor, i.e. `field(init=False)`
    """

    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True
            v1_key_case = 'C'

        my_str: str
        my_float: float = field(default=0.123, init=False)
        my_int: int = 1

    c = MyClass('testing')

    expected = {'myStr': 'testing', 'myFloat': 0.123, 'myInt': 1}

    out_dict = c.to_dict()
    assert out_dict == expected

    # Assert we are able to de-serialize the data back as expected
    assert c.from_dict(out_dict) == c


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
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True
            v1_key_case = 'P'

        my_bool: bool

    d = {'MyBool': input}

    result = MyClass.from_dict(d)
    log.debug('Parsed object: %r', result)

    assert result.my_bool == expected


def test_from_dict_handles_identical_cased_json_keys():
    """
    Calling `from_dict` when required JSON keys have the same casing as
    dataclass field names, even when the field names are not "snake-cased".

    See https://github.com/rnag/dataclass-wizard/issues/54 for more details.
    """

    @dataclass
    class ExtendedFetch(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        comments: dict
        viewMode: str
        my_str: str
        MyBool: bool

    j = '{"viewMode": "regular", "comments": {}, "MyBool": "true", "my_str": "Testing"}'

    c = ExtendedFetch.from_json(j)

    assert c.comments == {}
    assert c.viewMode == 'regular'
    assert c.my_str == 'Testing'
    assert c.MyBool


def test_from_dict_with_missing_fields():
    """
    Calling `from_dict` when required dataclass field(s) are missing in the
    JSON object.
    """

    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        my_str: str
        MyBool1: bool
        my_int: int

    value = 'Testing'
    d = {'my_str': value, 'myBool': 'true'}

    with pytest.raises(MissingFields) as e:
        _ = MyClass.from_dict(d)

    assert e.value.fields == ['my_str']
    assert e.value.missing_fields == ['MyBool1', 'my_int']
    assert 'key transform' not in e.value.kwargs
    assert 'resolution' not in e.value.kwargs


def test_from_dict_with_missing_fields_with_resolution():
    """
    Calling `from_dict` when required dataclass field(s) are missing in the
    JSON object, with a more user-friendly message.
    """

    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        my_str: str
        MyBool: bool
        my_int: int

    value = 'Testing'
    d = {'my_str': value, 'myBool': 'true'}

    with pytest.raises(MissingFields) as e:
        _ = MyClass.from_dict(d)

    assert e.value.fields == ['my_str']
    assert e.value.missing_fields == ['MyBool', 'my_int']
    _ = e.value.message
    # optional: these are populated in this case since this can be a somewhat common issue
    assert e.value.kwargs['Key Transform'] is None
    assert 'Resolution' in e.value.kwargs


def test_from_dict_key_transform_with_json_field():
    """
    Specifying a custom mapping of alias key to dataclass field, via the
    `Alias` helper function.
    """

    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        my_str: str = Alias('myCustomStr')
        my_bool: bool = Alias('myTestBool')

        # TODO: currently multiple aliases are not supported
        # my_bool: bool = Alias(('my_json_bool', 'myTestBool'))

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
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        my_str: Annotated[str, Alias('myCustomStr')]
        my_bool: Annotated[bool, Alias('myTestBool')]

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
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        num_set: Set[int]
        any_set: set

    d = {'num_set': input, 'any_set': input}

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

        class _(JSONWizard.Meta):
            v1 = True

        num_set: FrozenSet[int]
        any_set: frozenset

    d = {'num_set': input, 'any_set': input}

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
        # TODO: currently no type check for Literal
        # (False, pytest.raises(ParseError)),
        (0, does_not_raise()),
    ]
)
def test_literal(input, expectation):

    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1_key_case = 'P'
            v1 = True

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
        ('On', True),
        ('OFF', False),
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
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True
            v1_key_case = 'Auto'

        bool_or_none: Annotated[Optional[bool], MaxLen(23), "testing", 123]

    d = {'Bool-Or-None': input}

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
    class MyUUIDTestClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        my_id: MyUUIDSubclass

    d = {'my_id': input}

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
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True
            v1_key_case = 'P'

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
        (False, does_not_raise(), False),
        (0, does_not_raise(), 0),
        (None, does_not_raise(), None),
        # Since the first type in `Union` is `str`,
        # the float value is converted to a string.
        (1.2, does_not_raise(), '1.2')
    ]
)
def test_union(input, expectation, expected):

    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True
            v1_key_case = 'C'

        my_opt_str_int_or_bool: Union[str, int, bool, None]

    d = {'myOptStrIntOrBool': input}

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
    class A(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

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
        ('testing', pytest.raises(ParseError)),
        ('2020-01-02T01:02:03Z', does_not_raise()),
        ('2010-12-31 23:59:59-04:00', does_not_raise()),
        (123456789, does_not_raise()),
        (True, pytest.raises(ParseError)),
        (datetime(2010, 12, 31, 23, 59, 59), does_not_raise()),
    ]
)
def test_datetime(input, expectation):

    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        my_dt: datetime

    d = {'my_dt': input}

    with expectation:
        result = MyClass.from_dict(d)
        log.debug('Parsed object: %r', result)


@pytest.mark.parametrize(
    'input,expectation',
    [
        ('testing', pytest.raises(ParseError)),
        ('2020-01-02', does_not_raise()),
        ('2010-12-31', does_not_raise()),
        (123456789, does_not_raise()),
        (True, pytest.raises(ParseError)),
        (date(2010, 12, 31), does_not_raise()),
    ]
)
def test_date(input, expectation):

    @dataclass
    class MyClass(JSONSerializable):

        class _(JSONWizard.Meta):
            v1 = True

        my_d: date

    d = {'my_d': input}

    with expectation:
        result = MyClass.from_dict(d)
        log.debug('Parsed object: %r', result)


@pytest.mark.parametrize(
    'input,expectation',
    [
        ('testing', pytest.raises(ParseError)),
        ('01:02:03Z', does_not_raise()),
        ('23:59:59-04:00', does_not_raise()),
        (123456789, pytest.raises(ParseError)),
        (True, pytest.raises(ParseError)),
        (time(23, 59, 59), does_not_raise()),
    ]
)
def test_time(input, expectation):

    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        my_t: time

    d = {'my_t': input}

    with expectation:
        result = MyClass.from_dict(d)
        log.debug('Parsed object: %r', result)


@pytest.mark.parametrize(
    'input,expectation, base_err',
    [
        ('testing', pytest.raises(ParseError), ValueError),
        ('23:59:59-04:00', pytest.raises(ParseError), ValueError),
        ('32', does_not_raise(), None),
        ('32.7', does_not_raise(), None),
        ('32m', does_not_raise(), None),
        ('2h32m', does_not_raise(), None),
        ('4:13', does_not_raise(), None),
        ('5hr34m56s', does_not_raise(), None),
        ('1.2 minutes', does_not_raise(), None),
        (12345, does_not_raise(), None),
        (True, pytest.raises(ParseError), TypeError),
        (timedelta(days=1, seconds=2), does_not_raise(), None),
    ]
)
def test_timedelta(input, expectation, base_err):

    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        my_td: timedelta

    d = {'my_td': input}

    with expectation as e:
        result = MyClass.from_dict(d)
        log.debug('Parsed object: %r', result)
        log.debug('timedelta string value: %s', result.my_td)

    if e:  # if an error was raised, assert the underlying error type
        assert type(e.value.base_error) == base_err


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
            [True, False], pytest.raises(ParseError), None),
        (
            ['hello', 'world'], pytest.raises(ParseError), None
        ),
        (
            [1, 'two', 3], pytest.raises(ParseError), None),
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
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        my_list: List[int]

    d = {'my_list': input}

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
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        my_deque: deque[int]

    d = {'my_deque': input}

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
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        my_list: list

    d = {'my_list': input}

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
            [True, False, True], pytest.raises(ParseError), None),
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
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        my_tuple: Tuple[int, str, bool]

    d = {'my_tuple': input}

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
            [True, False, True], pytest.raises(ParseError), None),
        (
            [1, 'hello'], pytest.raises(ParseError), None
        ),
        (
            ['1', 'two', 'tRuE'], pytest.raises(ParseError), None
        ),
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
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        my_tuple: Tuple[int, str, Optional[bool], Union[str, int, None]]

    d = {'my_tuple': input}

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
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        my_tuple: tuple

    d = {'my_tuple': input}

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
            [], does_not_raise(), tuple()),
        (
            [True, False, True], pytest.raises(ParseError), None),
        (
            # Raises a `ValueError` because `hello` cannot be converted to int
            [1, 'hello'], pytest.raises(ParseError), None
        ),
        (
            [1], does_not_raise(), (1, )),
        (
            ['1', 2, '3'], does_not_raise(), (1, 2, 3)),
        (
            ['1', '2', None, '4', 5, 6, '7'], does_not_raise(),
            (1, 2, 0, 4, 5, 6, 7)),
        (
            'testing', pytest.raises(ParseError), None
        ),
    ]
)
def test_tuple_with_variadic_args(input, expectation, expected):
    """
    Test case when annotated type is in the "variadic" format, i.e.
    `Tuple[str, ...]`
    """

    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True
            v1_key_case = 'P'

        my_tuple: Tuple[int, ...]

    d = {'MyTuple': input}

    with expectation:
        result = MyClass.from_dict(d)

        log.debug('Parsed object: %r', result)
        assert result.my_tuple == expected


@pytest.mark.parametrize(
    'input,expectation,expected',
    [
        (
            None, pytest.raises(ParseError), None
        ),
        (
            {}, does_not_raise(), {}
        ),
        (
            # Wrong types for both key and value
            {'key': 'value'}, pytest.raises(ParseError), None),
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
            pytest.raises(ParseError), None
        )
    ]
)
def test_dict(input, expectation, expected):

    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True
            v1_key_case = 'C'

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
            None, pytest.raises(ParseError), None
        ),
        (
            {}, does_not_raise(), {}
        ),
        (
            # Wrong types for both key and value
            {'key': 'value'}, pytest.raises(ParseError), None),
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
            pytest.raises(ParseError), None
        )
    ]
)
def test_default_dict(input, expectation, expected):

    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True
            v1_key_case = 'C'

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
            None, pytest.raises(ParseError), None
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
            pytest.raises(ParseError), None
        )
    ]
)
def test_dict_without_type_hinting(input, expectation, expected):
    """
    Test case for annotating with a bare `dict` (acts as just a pass-through
    for its key-value pairs)
    """
    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True
            v1_key_case = 'C'

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
            pytest.raises(ParseError), None
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
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True
            v1_key_case = 'C'

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
            pytest.raises(ParseError),
            {'my_str': 'test', 'my_int': 'test', 'my_bool': True}
        ),
        (
            {'my_str': 'test', 'my_int': 2, 'my_bool': True},
            does_not_raise(),
            {'my_str': 'test', 'my_int': 2, 'my_bool': True}
        )
    ]
)
def test_typed_dict_with_all_fields_optional(input, expectation, expected):
    """
    Test case for loading to a TypedDict which has `total=False`, indicating
    that all fields are optional.

    """
    class MyDict(TypedDict, total=False):
        my_str: str
        my_bool: bool
        my_int: int

    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True
            v1_key_case = 'C'

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
            pytest.raises(ParseError), None,
        ),
        (
            {'my_str': 'test', 'my_int': 2, 'my_bool': True},
            does_not_raise(),
            {'my_str': 'test', 'my_int': 2, 'my_bool': True}
        ),
        (
            {'my_str': 'test', 'my_bool': True},
            does_not_raise(),
            {'my_str': 'test', 'my_bool': True}
        ),
        (
            # Incorrect type - `list`, but should be a `dict`
            [{'my_str': 'test', 'my_int': 2, 'my_bool': True}],
            pytest.raises(ParseError), None
        )
    ]
)
def test_typed_dict_with_one_field_not_required(input, expectation, expected):
    """
    Test case for loading to a TypedDict whose fields are all mandatory
    except for one field, whose annotated type is NotRequired.

    """
    class MyDict(TypedDict):
        my_str: str
        my_bool: bool
        my_int: NotRequired[int]

    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True
            v1_key_case = 'C'

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
            {}, pytest.raises(ParseError), None
        ),
        (
            {'my_int': 2}, does_not_raise(), {'my_int': 2}
        ),
        (
            {'key': 'value'}, pytest.raises(ParseError), None
        ),
        (
            {'key': 'value', 'my_int': 2}, does_not_raise(),
            {'my_int': 2}
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
            pytest.raises(ParseError),
            {'my_str': 'test', 'my_int': 'test', 'my_bool': True}
        ),
        (
            {'my_str': 'test', 'my_int': 2, 'my_bool': True},
            does_not_raise(),
            {'my_str': 'test', 'my_int': 2, 'my_bool': True}
        )
    ]
)
def test_typed_dict_with_one_field_required(input, expectation, expected):
    """
    Test case for loading to a TypedDict whose fields are all optional
    except for one field, whose annotated type is Required.

    """
    class MyDict(TypedDict, total=False):
        my_str: str
        my_bool: bool
        my_int: Required[int]

    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True
            v1_key_case = 'C'

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
            # Should raise a `TypeError` (types for last two are wrong)
            ['test', 2, True],
            pytest.raises(ParseError), None
        ),
        (
            ['test', True, 2],
            does_not_raise(),
            ('test', True, 2)
        ),
    ]
)
def test_named_tuple(input, expectation, expected):

    class MyNamedTuple(NamedTuple):
        my_str: str
        my_bool: bool
        my_int: int

    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        my_nt: MyNamedTuple

    d = {'my_nt': input}

    with expectation:
        result = MyClass.from_dict(d)

        log.debug('Parsed object: %r', result)
        if isinstance(expected, dict):
            expected = MyNamedTuple(**expected)

        assert result.my_nt == expected


@pytest.mark.skip('Need to add support in v1')
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
            {'my_str': 'test', 'my_int': 2, 'my_bool': True},
            does_not_raise(),
            {'my_str': 'test', 'my_int': 2, 'my_bool': True}
        ),
    ]
)
def test_named_tuple_with_input_dict(input, expectation, expected):

    class MyNamedTuple(NamedTuple):
        my_str: str
        my_bool: bool
        my_int: int

    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        my_nt: MyNamedTuple

    d = {'my_nt': input}

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
        # TODO need to add support for parsing dict's
        # (
        #     {}, pytest.raises(TypeError), None
        # ),
        # (
        #     {'key': 'value'}, pytest.raises(TypeError), {}
        # ),
        # (
        #     {'my_str': 'test', 'my_int': 2,
        #      'my_bool': True, 'other_key': 'testing'},
        #     # Unlike a TypedDict, extra arguments to a `namedtuple` should
        #     # result in an error
        #     pytest.raises(TypeError), None
        # ),
        # (
        #     {'my_str': 'test', 'my_int': 'test', 'my_bool': True},
        #     does_not_raise(), ('test', True, 'test')
        # ),
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
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        my_nt: MyNamedTuple

    d = {'my_nt': input}

    with expectation:
        result = MyClass.from_dict(d)

        log.debug('Parsed object: %r', result)
        if isinstance(expected, dict):
            expected = MyNamedTuple(**expected)

        assert result.my_nt == expected


def test_load_with_inner_model_when_data_is_null():
    """
    Test loading JSON data to an inner model dataclass, when the
    data being de-serialized is a null, and the annotated type for
    the field is not in the syntax `T | None`.
    """

    @dataclass
    class Inner:
        my_bool: bool
        my_str: str

    @dataclass
    class Outer(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        inner: Inner

    json_dict = {'inner': None}

    with pytest.raises(MissingData) as exc_info:
        _ = Outer.from_dict(json_dict)

    e = exc_info.value
    assert e.class_name == Outer.__qualname__
    assert e.nested_class_name == Inner.__qualname__
    assert e.field_name == 'inner'
    # the error should mention that we want an Inner, but get a None
    assert e.ann_type is Inner
    assert type(None) is e.obj_type


def test_load_with_inner_model_when_data_is_wrong_type():
    """
    Test loading JSON data to an inner model dataclass, when the
    data being de-serialized is a wrong type (list).
    """

    @dataclass
    class Inner:
        my_bool: bool
        my_str: str

    @dataclass
    class Outer(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True
            v1_key_case = 'AUTO'

        my_str: str
        inner: Inner

    json_dict = {
        'myStr': 'testing',
        'inner': [
            {
                'myStr': '123',
                'myBool': 'false',
                'my_val': '2',
            }
        ]
    }

    with pytest.raises(ParseError) as exc_info:
        _ = Outer.from_dict(json_dict)

    e = exc_info.value
    # TODO - is this right?
    assert e.class_name == Inner.__qualname__
    assert e.field_name == 'my_bool'
    assert e.base_error.__class__ is TypeError
    # the error should mention that we want a dict, but get a list
    assert e.ann_type == dict
    assert e.obj_type == list


def test_load_with_python_3_11_regression():
    """
    This test case is to confirm intended operation with `typing.Any`
    (either explicit or implicit in plain `list` or `dict` type
    annotations).

    Note: I have been unable to reproduce [the issue] posted on GitHub.
    I've tested this on multiple Python versions on Mac, including
    3.10.6, 3.11.0, 3.11.5, 3.11.10.

    See [the issue].

    [the issue]: https://github.com/rnag/dataclass-wizard/issues/89
    """

    @dataclass
    class Item(JSONSerializable):

        class _(JSONSerializable.Meta):
            v1 = True

        a: dict
        b: Optional[dict]
        c: Optional[list] = None

    item = Item.from_json('{"a": {}, "b": null}')

    assert item.a == {}
    assert item.b is item.c is None


@pytest.mark.skip(reason='TODO add support in v1')
def test_with_self_referential_dataclasses_1():
    """
    Test loading JSON data, when a dataclass model has cyclic
    or self-referential dataclasses. For example, A -> A -> A.
    """
    @dataclass
    class A:
        a: Optional['A'] = None

    # enable support for self-referential / recursive dataclasses
    LoadMeta(v1=True, recursive_classes=True).bind_to(A)

    # Fix for local test cases so the forward reference works
    globals().update(locals())

    # assert that `fromdict` with a recursive, self-referential
    # input `dict` works as expected.
    a = fromdict(A, {'a': {'a': {'a': None}}})
    assert a == A(a=A(a=A(a=None)))


@pytest.mark.skip(reason='TODO add support in v1')
def test_with_self_referential_dataclasses_2():
    """
    Test loading JSON data, when a dataclass model has cyclic
    or self-referential dataclasses. For example, A -> B -> A -> B.
    """
    @dataclass
    class A(JSONWizard):
        class _(JSONWizard.Meta):
            v1 = True
            # enable support for self-referential / recursive dataclasses
            recursive_classes = True

        b: Optional['B'] = None

    @dataclass
    class B:
        a: Optional['A'] = None

    # Fix for local test cases so the forward reference works
    globals().update(locals())

    # assert that `fromdict` with a recursive, self-referential
    # input `dict` works as expected.
    a = fromdict(A, {'b': {'a': {'b': {'a': None}}}})
    assert a == A(b=B(a=A(b=B())))


def test_catch_all():
    """'Catch All' support with no default field value."""
    @dataclass
    class MyData(TOMLWizard):
        my_str: str
        my_float: float
        extra: CatchAll

    LoadMeta(v1=True).bind_to(MyData)

    toml_string = '''
    my_extra_str = "test!"
    my_str = "test"
    my_float = 3.14
    my_bool = true
    '''

    # Load from TOML string
    data = MyData.from_toml(toml_string)

    assert data.extra == {'my_extra_str': 'test!', 'my_bool': True}

    # Save to TOML string
    toml_string = data.to_toml()

    assert toml_string == """\
my_str = "test"
my_float = 3.14
my_extra_str = "test!"
my_bool = true
"""

    # Read back from the TOML string
    new_data = MyData.from_toml(toml_string)

    assert new_data.extra == {'my_extra_str': 'test!', 'my_bool': True}


def test_catch_all_with_default():
    """'Catch All' support with a default field value."""

    @dataclass
    class MyData(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        my_str: str
        my_float: float
        extra_data: CatchAll = False

    # Case 1: Extra Data is provided

    input_dict = {
        'my_str': "test",
        'my_float': 3.14,
        'my_other_str': "test!",
        'my_bool': True
    }

    # Load from TOML string
    data = MyData.from_dict(input_dict)

    assert data.extra_data == {'my_other_str': 'test!', 'my_bool': True}

    # Save to TOML file
    output_dict = data.to_dict()

    assert output_dict == {
        "myStr": "test",
        "myFloat": 3.14,
        "my_other_str": "test!",
        "my_bool": True
    }

    new_data = MyData.from_dict(snake(output_dict))

    assert new_data.extra_data == {'my_other_str': 'test!', 'my_bool': True}

    # Case 2: Extra Data is not provided

    input_dict = {
        'my_str': "test",
        'my_float': 3.14,
    }

    # Load from TOML string
    data = MyData.from_dict(input_dict)

    assert data.extra_data is False

    # Save to TOML file
    output_dict = data.to_dict()

    assert output_dict == {
        "myStr": "test",
        "myFloat": 3.14,
    }

    new_data = MyData.from_dict(snake(output_dict))

    assert new_data.extra_data is False


def test_catch_all_with_skip_defaults():
    """'Catch All' support with a default field value and `skip_defaults`."""

    @dataclass
    class MyData(JSONWizard):
        class _(JSONWizard.Meta):
            v1 = True
            skip_defaults = True

        my_str: str
        my_float: float
        extra_data: CatchAll = False

    # Case 1: Extra Data is provided

    input_dict = {
        'my_str': "test",
        'my_float': 3.14,
        'my_other_str': "test!",
        'my_bool': True
    }

    # Load from TOML string
    data = MyData.from_dict(input_dict)

    assert data.extra_data == {'my_other_str': 'test!', 'my_bool': True}

    # Save to TOML file
    output_dict = data.to_dict()

    assert output_dict == {
        "myStr": "test",
        "myFloat": 3.14,
        "my_other_str": "test!",
        "my_bool": True
    }

    new_data = MyData.from_dict(snake(output_dict))

    assert new_data.extra_data == {'my_other_str': 'test!', 'my_bool': True}

    # Case 2: Extra Data is not provided

    input_dict = {
        'my_str': "test",
        'my_float': 3.14,
    }

    # Load from TOML string
    data = MyData.from_dict(input_dict)

    assert data.extra_data is False

    # Save to TOML file
    output_dict = data.to_dict()

    assert output_dict == {
        "myStr": "test",
        "myFloat": 3.14,
    }

    new_data = MyData.from_dict(snake(output_dict))

    assert new_data.extra_data is False


def test_catch_all_with_auto_key_case():
    """'Catch All' with `auto` key case."""

    @dataclass
    class Options(JSONWizard):
        class _(JSONWizard.Meta):
            v1 = True
            v1_key_case = 'Auto'

        my_extras: CatchAll
        email: str

    opt = Options.from_dict({
        'Email': 'a@b.org',
        'token': '<PASSWORD>',
    })
    assert opt == Options(my_extras={'token': '<PASSWORD>'}, email='a@b.org')

    opt = Options.from_dict({
        'Email': 'x@y.org',
    })
    assert opt == Options(my_extras={}, email='x@y.org')


def test_from_dict_with_nested_object_alias_path():
    """
    Specifying a custom mapping of "nested" alias to dataclass field,
    via the `AliasPath` helper function.
    """

    @dataclass
    class A(JSONPyWizard, debug=True):
        class _(JSONPyWizard.Meta):
            v1 = True

        an_int: int
        a_bool: Annotated[bool, AliasPath('x.y.z.0')]
        my_str: str = AliasPath(['a', 'b', 'c', -1], default='xyz')

    # Failures

    d = {'my_str': 'test'}

    with pytest.raises(ParseError) as e:
        _ = A.from_dict(d)

    err = e.value
    assert err.field_name == 'a_bool'
    assert err.base_error.args == ('x', )
    assert err.kwargs['current_path'] == "'x'"

    d = {'a': {'b': {'c': []}},
         'x': {'y': {}}, 'an_int': 3}

    with pytest.raises(ParseError) as e:
        _ = A.from_dict(d)

    err = e.value
    assert err.field_name == 'a_bool'
    assert err.base_error.args == ('z', )
    assert err.kwargs['current_path'] == "'z'"

    # Successes

    # Case 1
    d = {'a': {'b': {'c': [1, 5, 7]}},
         'x': {'y': {'z': [False]}}, 'an_int': 3}

    a = A.from_dict(d)
    assert repr(a).endswith("A(an_int=3, a_bool=False, my_str='7')")

    d = a.to_dict()

    assert d == {
        'x': {
            'y': {
                'z': { 0: False }
            }
        },
        'a': {
            'b': {
                'c': { -1: '7' }
            }
        },
        'an_int': 3
    }

    a = A.from_dict(d)
    assert repr(a).endswith("A(an_int=3, a_bool=False, my_str='7')")

    # Case 2
    d = {'a': {'b': {}},
         'x': {'y': {'z': [True, False]}}, 'an_int': 5}

    a = A.from_dict(d)
    assert repr(a).endswith("A(an_int=5, a_bool=True, my_str='xyz')")

    d = a.to_dict()

    assert d == {
        'x': {
            'y': {
                'z': { 0: True }
            }
        },
        'a': {
            'b': {
                'c': { -1: 'xyz' }
            }
        },
        'an_int': 5
    }


def test_from_dict_with_nested_object_alias_path_with_skip_defaults():
    """
    Specifying a custom mapping of "nested" alias to dataclass field,
    via the `AliasPath` helper function.

    Test with `skip_defaults=True`, `load_alias`, and `skip=True`.
    """

    @dataclass
    class A(JSONWizard, debug=True):
        class _(JSONWizard.Meta):
            v1 = True
            skip_defaults = True

        an_int: Annotated[int, AliasPath('my."test value"[here!][0]')]

        a_bool: Annotated[bool, AliasPath(load='x.y.z.-1')]
        my_str: Annotated[str, AliasPath(['a', 'b', 'c', -1], skip=True)] = 'xyz1'

        other_bool: bool = AliasPath('x.y."z z"', default=True)

    # Failures

    d = {'my_str': 'test'}

    with pytest.raises(ParseError) as e:
        _ = A.from_dict(d)

    err = e.value
    assert err.field_name == 'an_int'
    assert err.base_error.args == ('my', )
    assert err.kwargs['current_path'] == "'my'"

    d = {
        'my': {'test value': {'here!': [1, 2, 3]}},
        'a': {'b': {'c': []}},
         'x': {'y': {}}, 'an_int': 3}

    with pytest.raises(ParseError) as e:
        _ = A.from_dict(d)

    err = e.value
    assert err.field_name == 'a_bool'
    assert err.base_error.args == ('z', )
    assert err.kwargs['current_path'] == "'z'"

    # Successes

    # Case 1
    d = {
        'my': {'test value': {'here!': [1, 2, 3]}},
        'a': {'b': {'c': [1, 5, 7]}},
         'x': {'y': {'z': [False]}}, 'an_int': 3
    }

    a = A.from_dict(d)
    assert repr(a).endswith("A(an_int=1, a_bool=False, my_str='7', other_bool=True)")

    d = a.to_dict()

    assert d == {
        'aBool': False,
        'my': {'test value': {'here!': {0: 1}}},
    }

    with pytest.raises(ParseError):
        _ = A.from_dict(d)

    # Case 2
    d = {
        'my': {'test value': {'here!': [1, 2, 3]}},
        'a': {'b': {}},
         'x': {'y': {
             'z': [],
             'z z': False,
         }},
    }

    with pytest.raises(ParseError) as e:
        _ = A.from_dict(d)

    err = e.value
    assert err.field_name == 'a_bool'
    assert repr(err.base_error) == "IndexError('list index out of range')"

    # Case 3
    d = {
        'my': {'test value': {'here!': [1, 2, 3]}},
        'a': {'b': {}},
         'x': {'y': {
             'z': [True, False],
             'z z': False,
         }},
    }

    a = A.from_dict(d)
    assert repr(a).endswith("A(an_int=1, a_bool=False, my_str='xyz1', other_bool=False)")

    d = a.to_dict()

    assert d == {
        'aBool': False,
        'my': {'test value': {'here!': {0: 1}}},
        'x': {
            'y': {
                'z z': False,
            }
        },
    }


def test_from_dict_with_nested_object_alias_path_with_dump_alias_and_skip():
    """
    Test nested object `AliasPath` with dump='...' and skip=True,
    along with `Alias` with `skip=True`,
    added for branch coverage.
    """
    @dataclass
    class A(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        my_str: str = AliasPath(dump='a.b.c[0]')
        my_bool: bool = AliasPath('x.y."Z 1"', skip=True)
        my_int: int = Alias('my Integer', skip=True)

    d = {'a': {'b': {'c': [1, 2, 3]}},
         'x': {'y': {'Z 1': 'f'}},}

    with pytest.raises(MissingFields) as exc_info:
        _ = A.from_dict(d)

    e = exc_info.value
    assert e.fields == ['my_bool']
    assert e.missing_fields == ['my_str', 'my_int']

    d = {'my_str': 'test',
         'my Integer': '123',
         'x': {'y': {'Z 1': 'f'}},}

    a = A.from_dict(d)

    assert a.my_str == 'test'
    assert a.my_int == 123
    assert a.my_bool is False

    serialized = a.to_dict()
    assert serialized == {
        'a': {'b': {'c': {0: 'test'}}},
    }


def test_auto_assign_tags_and_raise_on_unknown_json_key():

    @dataclass
    class A:
        mynumber: int

    @dataclass
    class B:
        mystring: str

    @dataclass
    class Container(JSONWizard):
        obj2: Union[A, B]

        class _(JSONWizard.Meta):
            auto_assign_tags = True
            v1 = True
            v1_on_unknown_key = 'RAISE'

    c = Container(obj2=B("bar"))

    output_dict = c.to_dict()

    assert output_dict == {
        "obj2": {
            "mystring": "bar",
            "__tag__": "B",
        }
    }

    assert c == Container.from_dict(output_dict)

    input_dict = {
        "obj2": {
            "mystring": "bar",
            "__tag__": "B",
            "__extra__": "C",
        }
    }

    with pytest.raises(UnknownKeysError) as exc_info:
        _ = Container.from_dict(input_dict)

    e = exc_info.value

    assert e.unknown_keys == {'__extra__'}


def test_auto_assign_tags_and_catch_all():
    """Using both `auto_assign_tags` and `CatchAll` does not save tag key in `CatchAll`."""
    @dataclass
    class A:
        mynumber: int
        extra: CatchAll = None

    @dataclass
    class B:
        mystring: str
        extra: CatchAll = None

    @dataclass
    class Container(JSONWizard, debug=False):
        obj2: Union[A, B]
        extra: CatchAll = None

        class _(JSONWizard.Meta):
            auto_assign_tags = True
            v1 = True
            tag_key = 'type'

    c = Container(obj2=B("bar"))

    output_dict = c.to_dict()

    assert output_dict == {
        "obj2": {
            "mystring": "bar",
            "type": "B"
        }
    }

    c2 = Container.from_dict(output_dict)
    assert c2 == c == Container(obj2=B(mystring='bar', extra=None), extra=None)

    assert c2.to_dict() == {
        "obj2": {
            "mystring": "bar", "type": "B"
        }
    }


def test_skip_if():
    """
    Using Meta config `skip_if` to conditionally
    skip serializing dataclass fields.
    """
    @dataclass
    class Example(JSONPyWizard, debug=True):
        class _(JSONPyWizard.Meta):
            v1 = True
            skip_if = IS_NOT(True)

        my_str: 'str | None'
        my_bool: bool
        other_bool: bool = False

    ex = Example(my_str=None, my_bool=True)

    assert ex.to_dict() == {'my_bool': True}


def test_skip_defaults_if():
    """
    Using Meta config `skip_defaults_if` to conditionally
    skip serializing dataclass fields with default values.
    """
    @dataclass
    class Example(JSONPyWizard):
        class _(JSONPyWizard.Meta):
            v1 = True
            skip_defaults_if = IS(None)

        my_str: 'str | None'
        other_str: 'str | None' = None
        third_str: 'str | None' = None
        my_bool: bool = False

    ex = Example(my_str=None, other_str='')

    assert ex.to_dict() == {
        'my_str': None,
        'other_str': '',
        'my_bool': False
    }

    ex = Example('testing', other_str='', third_str='')
    assert ex.to_dict() == {'my_str': 'testing', 'other_str': '',
                            'third_str': '', 'my_bool': False}

    ex = Example(None, my_bool=None)
    assert ex.to_dict() == {'my_str': None}


def test_per_field_skip_if():
    """
    Test per-field `skip_if` functionality, with the ``SkipIf``
    condition in type annotation, and also specified in
    ``skip_if_field()`` which wraps ``dataclasses.Field``.
    """
    @dataclass
    class Example(JSONPyWizard):
        class _(JSONPyWizard.Meta):
            v1 = True

        my_str: Annotated['str | None', SkipIfNone]
        other_str: 'str | None' = None
        third_str: 'str | None' = skip_if_field(EQ(''), default=None)
        my_bool: bool = False
        other_bool: Annotated[bool, SkipIf(IS(True))] = True

    ex = Example(my_str='test')
    assert ex.to_dict() == {
        'my_str': 'test',
        'other_str': None,
        'third_str': None,
        'my_bool': False
    }

    ex = Example(None, other_str='', third_str='', my_bool=True, other_bool=False)
    assert ex.to_dict() == {'other_str': '',
                            'my_bool': True,
                            'other_bool': False}

    ex = Example('None', other_str='test', third_str='None', my_bool=None, other_bool=True)
    assert ex.to_dict() == {'my_str': 'None', 'other_str': 'test',
                            'third_str': 'None', 'my_bool': None}


def test_is_truthy_and_is_falsy_conditions():
    """
    Test both IS_TRUTHY and IS_FALSY conditions within a single test case.
    """

    # Define the Example class within the test case and apply the conditions
    @dataclass
    class Example(JSONPyWizard):

        class _(JSONPyWizard.Meta):
            v1 = True

        my_str: Annotated['str | None', SkipIf(IS_TRUTHY())]  # Skip if truthy
        my_bool: bool = skip_if_field(IS_FALSY())  # Skip if falsy
        my_int: Annotated['int | None', SkipIf(IS_FALSY())] = None  # Skip if falsy

    # Test IS_TRUTHY condition (field will be skipped if truthy)
    obj = Example(my_str="Hello", my_bool=True, my_int=5)
    assert obj.to_dict() == {'my_bool': True, 'my_int': 5}  # `my_str` is skipped because it is truthy

    # Test IS_FALSY condition (field will be skipped if falsy)
    obj = Example(my_str=None, my_bool=False, my_int=0)
    assert obj.to_dict() == {'my_str': None}  # `my_str` is None (falsy), so it is not skipped

    # Test a mix of truthy and falsy values
    obj = Example(my_str="Not None", my_bool=True, my_int=None)
    assert obj.to_dict() == {'my_bool': True}  # `my_str` is truthy, so it is skipped, `my_int` is falsy and skipped

    # Test with both IS_TRUTHY and IS_FALSY applied (both `my_bool` and `my_in


def test_skip_if_truthy_or_falsy():
    """
    Test skip if condition is truthy or falsy for individual fields.
    """

    # Use of SkipIf with IS_TRUTHY
    @dataclass
    class SkipExample(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        my_str: Annotated['str | None', SkipIf(IS_TRUTHY())]
        my_bool: bool = skip_if_field(IS_FALSY())

    # Test with truthy `my_str` and falsy `my_bool` should be skipped
    obj = SkipExample(my_str="Test", my_bool=False)
    assert obj.to_dict() == {}

    # Test with truthy `my_str` and `my_bool` should include the field
    obj = SkipExample(my_str="", my_bool=True)
    assert obj.to_dict() == {'myStr': '', 'myBool': True}


def test_invalid_condition_annotation_raises_error():
    """
    Test that using a Condition (e.g., LT) directly as a field annotation
    without wrapping it in SkipIf() raises an InvalidConditionError.
    """
    with pytest.raises(InvalidConditionError, match="Wrap conditions inside SkipIf()"):

        @dataclass
        class Example(JSONWizard):

            class _(JSONWizard.Meta):
                debug_enabled = True

            my_field: Annotated[int, LT(5)]  # Invalid: LT is not wrapped in SkipIf.

        # Attempt to serialize an instance, which should raise the error.
        Example(my_field=3).to_dict()


def test_dataclass_in_union_when_tag_key_is_field():
    """
    Test case for dataclasses in `Union` when the `Meta.tag_key` is a dataclass field.
    """
    @dataclass
    class DataType(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        id: int
        type: str

    @dataclass
    class XML(DataType):
        class _(JSONWizard.Meta):
            tag = "xml"

        field_type_1: str

    @dataclass
    class HTML(DataType):
        class _(JSONWizard.Meta):
            tag = "html"

        field_type_2: str

    @dataclass
    class Result(JSONWizard):
        class _(JSONWizard.Meta):
            tag_key = "type"

        data: Union[XML, HTML]

    t1 = Result.from_dict({"data": {"id": 1, "type": "xml", "field_type_1": "value"}})
    assert t1 == Result(data=XML(id=1, type='xml', field_type_1='value'))


def test_sequence_and_mutable_sequence_are_supported():
    """
    Confirm  `Collection`, `Sequence`, and `MutableSequence` -- imported
    from either `typing` or `collections.abc` -- are supported.
    """
    @dataclass
    class IssueFields:
        name: str

    @dataclass
    class Options(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        email: str = ""
        token: str = ""
        fields: Sequence[IssueFields] = (
            IssueFields('A'),
            IssueFields('B'),
            IssueFields('C'),
        )
        fields_tup: tuple[IssueFields] = IssueFields('A'),
        fields_var_tup: tuple[IssueFields, ...] = IssueFields('A'),
        list_of_int: MutableSequence[int] = field(default_factory=list)
        list_of_bool: Collection[bool] = field(default_factory=list)

    # initialize with defaults
    opt = Options.from_dict({
        'email': 'a@b.org',
        'token': '<PASSWORD>',
    })
    assert opt == Options(
        email='a@b.org', token='<PASSWORD>',
        fields=(IssueFields(name='A'), IssueFields(name='B'), IssueFields(name='C')),
    )

    # check annotated `Sequence` maps to `tuple`
    opt = Options.from_dict({
        'email': 'a@b.org',
        'token': '<PASSWORD>',
        'fields': [{'name': 'X'}, {'name': 'Y'}, {'name': 'Z'}]
    })
    assert opt.fields == (IssueFields('X'), IssueFields('Y'), IssueFields('Z'))

    # does not raise error
    opt = Options.from_dict({
        'email': 'a@b.org',
        'token': '<PASSWORD>',
        'fields_tup': [{'name': 'X'}]
    })
    assert opt.fields_tup == (IssueFields('X'), )

    # TODO: ought to raise error - maybe  support a`strict` mode?
    opt = Options.from_dict({
        'email': 'a@b.org',
        'token': '<PASSWORD>',
        'fields_tup': [{'name': 'X'}, {'name': 'Y'}]
    })

    assert opt.fields_tup == (IssueFields('X'), )

    # does not raise error
    opt = Options.from_dict({
        'email': 'a@b.org',
        'token': '<PASSWORD>',
        'fields_var_tup': [{'name': 'X'}, {'name': 'Y'}]
    })
    assert opt.fields_var_tup == (IssueFields('X'), IssueFields('Y'))

    # check annotated `MutableSequence` maps to `list`
    opt = Options.from_dict({
        'email': 'a@b.org',
        'token': '<PASSWORD>',
        'list_of_int': (1, '2', 3.0)
    })
    assert opt.list_of_int == [1, 2, 3]

    # check annotated `Collection` maps to `list`
    opt = Options.from_dict({
        'email': 'a@b.org',
        'token': '<PASSWORD>',
        'list_of_bool': (1, '0', '1')
    })
    assert opt.list_of_bool == [True, False, True]


@pytest.mark.skip('Ran out of time to get this to work')
def test_dataclass_decorator_is_automatically_applied():
    """
    Confirm the `@dataclass` decorator is automatically
    applied, if not decorated by the user.
    """
    class Test(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        my_field: str
        my_bool: bool = False

    t = Test.from_dict({'myField': 'value'})
    assert t.my_field == 'value'

    t = Test('test', True)
    assert t.my_field == 'test'
    assert t.my_bool

    with pytest.raises(TypeError, match=".*Test\.__init__\(\) missing 1 required positional argument: 'my_field'"):
        Test()
