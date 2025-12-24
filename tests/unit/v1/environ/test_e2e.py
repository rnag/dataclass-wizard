from collections import deque
from datetime import datetime, date, timezone
from typing import Optional, Union, NamedTuple, Literal

import pytest

from dataclass_wizard import DataclassWizard
from dataclass_wizard.errors import ParseError
from dataclass_wizard.v1 import Alias, EnvWizard

from ..utils_env import envsafe, from_env
from ...._typing import *


def test_none_is_deserialized():
    class MyClass(EnvWizard):
        test: Union[int, None]

    _input = {'TEST': 123}
    env = envsafe(_input)
    assert env == {'TEST': '123'}
    c = from_env(MyClass, _input)
    assert c.raw_dict() == {'test': 123}

    _input = {'TEST': None}  # None -> 'null'
    env = envsafe(_input)
    assert env == {'TEST': 'null'}
    c = from_env(MyClass, _input)
    assert c.raw_dict() == {'test': None}


def test_nested_union_with_complex_types_in_containers():
    class Sub(DataclassWizard):
        test: str

    class MyClass(EnvWizard):
        class _(EnvWizard.Meta):
            v1_case = 'CAMEL'
            v1_unsafe_parse_dataclass_in_union = True

        my_bool: dict[str, tuple[Optional[bool], ...]] = Alias(env='Boolean-Dict')
        unionInListWithClass: list[Union[str, Sub, None]]
        unionWithClass: Union[str, Sub]
        opt_class: Optional[Sub]


    _input = {'Boolean-Dict': {'v': [None, 'tRuE', None]},
              'UNION_IN_LIST_WITH_CLASS': ['s', {'test': 'hello'}, 'value'],
              'UNION_WITH_CLASS': {'test': 'world'},
              'OPT_CLASS': {'test': 'value'}}

    c = from_env(MyClass, _input)
    assert c.raw_dict() == {'my_bool': {'v': (None, True, None)},
                            'unionInListWithClass': ['s', Sub(test='hello'), 'value'],
                            'unionWithClass': Sub(test='world'), 'opt_class': Sub(test='value')}

    _input = {'Boolean-Dict': {'v': []},
              'UNION_IN_LIST_WITH_CLASS': ['', {'test': '123'}, None],
              'UNION_WITH_CLASS': 's',
              'OPT_CLASS': None}

    c = from_env(MyClass, _input)
    assert c.raw_dict() == {'my_bool': {'v': ()},
                            'unionInListWithClass': ['', Sub(test='123'), None], 'unionWithClass': 's',
                            'opt_class': None}


def test_named_tuples_with_optionals_in_container():

    class NTAllOptionals(NamedTuple):
        a: str = 'test'
        b: int = 1
        c: bool = True

    class NTOneOptional(NamedTuple):
        my_int: int
        my_bool: bool = False

    class MyClass(EnvWizard):
        class _(EnvWizard.Meta):
            # v1 = True
            v1_load_case = 'FIELD_FIRST'

        nt_all_opts: dict[str, set[NTAllOptionals]]
        nt_one_opt: list[NTOneOptional]

    _input = {'nt_one_opt': [['123']], 'nt_all_opts': {'k': [[]]}}

    with pytest.raises(ParseError) as e:
        _ = from_env(MyClass, {'nt_one_opt': [{}], 'nt_all_opts': {'k': [[]]}})

    assert '`dict` input is not supported for NamedTuple, use a dataclass instead' in str(e.value)

    c = from_env(MyClass, _input)

    assert c.raw_dict() == {
        'nt_all_opts': {
            'k': {NTAllOptionals()},
        },
        'nt_one_opt': [
            NTOneOptional(my_int=123, my_bool=False)
        ],
    }


def test_typed_dict_with_optionals_and_read_only_in_container():

    class TDWithReadOnlyAndOpts(TypedDict):
        a: int
        b: NotRequired[str]
        c: NotRequired[bool]
        d: ReadOnly[float]

    class MyClass(EnvWizard):
        my_td: dict[str, tuple[bool, deque[TDWithReadOnlyAndOpts]]]

    td_value = []
    d = {'my_td': {'test': ['True', [td_value]]}}

    with pytest.raises(ParseError) as e:
        _ = from_env(MyClass, d)
    assert 'Expected a type {}, got list' in str(e.value)

    td_value = {'d': '23'}
    d = {'my_td': {'test': ['True', [td_value]]}}

    with pytest.raises(ParseError) as e:
        _ = from_env(MyClass, d)
    assert 'Missing required key: \'a\'' in str(e.value)

    td_value = {'d': '23', 'a': '1', 'c': '0'}
    d = {'my_td': {'test': ['True', [td_value]]}}

    c = from_env(MyClass, d)
    assert c == MyClass(my_td={'test': (True, deque([{'a': 1, 'c': False, 'd': 23.0}]))})

    new_dict = c.raw_dict()
    assert new_dict == {'my_td': {'test': (True, deque([{'a': 1, 'c': False, 'd': 23.0}]))}}


def test_literal_in_container():
    class MyClass(EnvWizard):
        my_literal_dict: dict[str, tuple[int, frozenset[Literal['Aa', 'Bb']]]]

    d = {'my_literal_dict': {'test': ['123', ['aa', 'Bb']]}}

    with pytest.raises(ParseError) as e:
        _ = from_env(MyClass, d)
    assert 'Value not in expected Literal values' in str(e.value)

    d = {'my_literal_dict': {'test': ['123', ['Bb', 'Aa']]}}
    c = from_env(MyClass, d)
    # noinspection PyTypeChecker
    assert c == MyClass(my_literal_dict={'test': (123, frozenset({'Aa', 'Bb'}))})

    new_dict = c.to_dict()
    assert new_dict == {'my_literal_dict': {'test': (123, {'Aa', 'Bb'})}}


def test_decode_date_and_datetime_from_numeric_and_string_timestamp_and_iso_format():

    class MyClass(EnvWizard):
        my_value: float
        my_dt: datetime
        another_date: date

    d = {"another_date": "2021-12-17", "my_dt": "2022-04-27T16:30:45Z", "my_value": 1.23}

    expected_obj = MyClass(my_value=1.23,
                           my_dt=datetime(2022, 4, 27, 16, 30, 45, tzinfo=timezone.utc),
                           another_date=date(2021, 12, 17))
    expected_dict = {'my_value': 1.23, 'my_dt': '2022-04-27T16:30:45Z', 'another_date': '2021-12-17'}

    c1 = from_env(MyClass, d)

    d = {"another_date": "1639763585", "my_dt": "1651077045", "my_value": '1.23'}
    c2 = from_env(MyClass, d)

    d = {"another_date": 1639763585, "my_dt": 1651077045, "my_value": '1.23'}
    c3 = from_env(MyClass, d)

    assert c1 == c2 == c3 == expected_obj
    assert c1.to_dict() == c2.to_dict() == c3.to_dict() == expected_dict
