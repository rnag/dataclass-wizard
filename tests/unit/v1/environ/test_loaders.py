from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime, date, timezone
from typing import Tuple, NamedTuple, List

import pytest

from dataclass_wizard import DataclassWizard
from dataclass_wizard.v1 import EnvWizard

from ..utils_env import from_env


def test_load_to_bytes():
    class E(EnvWizard):
        b: bytes

    e = E(b='testing 123')
    assert e.b == b'testing 123'


@pytest.mark.parametrize(
    'input,expected',
    [
        ('testing 123', bytearray(b'testing 123')),
        (b'test', bytearray(b'test')),
        ([1, 2, 3], bytearray([1, 2, 3]))
    ]
)
def test_load_to_bytearray(input, expected):
    class MyClass(EnvWizard):
        my_btarr: bytearray

    assert MyClass(my_btarr=input).my_btarr == expected


def test_load_to_tuple_and_named_tuple():

    class MyNT(NamedTuple):
        my_float: float
        my_str: str

    untyped_tup = namedtuple('untyped_tup', ('a', 'b', 'c'))

    class MyClass(EnvWizard):
        my_tup: Tuple[int, ...]
        my_nt: MyNT
        my_untyped_nt: untyped_tup

    env = {'MY_TUP': '1,2,3',
           'MY_NT': '[1.23, "string"]',
           'my_untyped_nt': 'hello ,  world, 123'}

    c = from_env(MyClass, env)

    assert c.raw_dict() == {
        'my_nt': MyNT(my_float=1.23, my_str='string'),
        'my_tup': (1, 2, 3),
        'my_untyped_nt': untyped_tup(a='hello', b='world', c='123'),
    }

    assert c.to_dict() == {'my_nt': [1.23, 'string'],
                           'my_tup': [1, 2, 3],
                           'my_untyped_nt': ['hello', 'world', '123']}


def test_load_to_dataclass():
    """When an `EnvWizard` subclass has a nested dataclass schema."""

    @dataclass
    class Inner1:
        my_bool: bool
        my_string: str

    class Inner2(DataclassWizard, load_case='AUTO'):
        answer_to_life: int
        my_list: List[str]

    class MyClass(EnvWizard):

        inner_cls_1: Inner1
        inner_cls_2: Inner2

    env = {'inner_cls_1': 'my_bool=false, my_string=test',
           'inner_cls_2': '{"answerToLife": "42", "MyList": "testing, 123 , hello!"}'}

    c = from_env(MyClass, env)
    # print(c)

    assert c.raw_dict() == {
        'inner_cls_1': Inner1(my_bool=False,
                              my_string='test'),
        'inner_cls_2': Inner2(answer_to_life=42,
                              my_list=['testing', '123', 'hello!']),
    }

    assert c.to_dict() == {
        'inner_cls_1': {'my_bool': False,
                        'my_string': 'test'},
        'inner_cls_2': {'answer_to_life': 42,
                        'my_list': ['testing', '123', 'hello!']}
    }


@pytest.mark.parametrize(
    'input,expected',
    [
        ('2021-11-28T17:35:55', datetime(2021, 11, 28, 17, 35, 55)),
        (1577952245, datetime(2020, 1, 2, 8, 4, 5, tzinfo=timezone.utc)),
        (datetime.min, datetime.min)
    ]
)
def test_load_to_datetime(input, expected):
    class MyClass(EnvWizard):
        my_dt: datetime

    assert MyClass(my_dt=input).my_dt == expected


@pytest.mark.parametrize(
    'input,expected',
    [
        ('2021-11-28', date(2021, 11, 28)),
        (1577952245, date(2020, 1, 2)),
        (date.min, date.min)
    ]
)
def test_load_to_date(input, expected):
    class MyClass(EnvWizard):
        my_date: date

    assert MyClass(my_date=input).my_date == expected
