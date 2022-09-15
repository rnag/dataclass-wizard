import os
from collections import namedtuple
from datetime import datetime, date
from typing import Tuple, NamedTuple

import pytest

from dataclass_wizard import EnvWizard
from dataclass_wizard.environ.loaders import EnvLoader


def test_load_to_bytes():
    assert EnvLoader.load_to_bytes('testing 123', bytes) == b'testing 123'


@pytest.mark.parametrize(
    'input,expected',
    [
        ('testing 123', bytearray(b'testing 123')),
        (b'test', bytearray(b'test')),
        ([1, 2, 3], bytearray([1, 2, 3]))
    ]
)
def test_load_to_bytearray(input, expected):
    assert EnvLoader.load_to_byte_array(input, bytearray) == expected


def test_load_to_tuple_and_named_tuple():
    os.environ['MY_TUP'] = '1,2,3'
    os.environ['MY_NT'] = '[1.23, "string"]'
    os.environ['my_untyped_nt'] = 'hello ,  world, 123'

    class MyNT(NamedTuple):
        my_float: float
        my_str: str

    untyped_tup = namedtuple('untyped_tup', ('a', 'b', 'c'))

    class MyClass(EnvWizard, reload_env=True):
        my_tup: Tuple[int, ...]
        my_nt: MyNT
        my_untyped_nt: untyped_tup

    c = MyClass()

    assert c.dict() == {'my_nt': MyNT(my_float=1.23, my_str='string'),
                        'my_tup': (1, 2, 3),
                        'my_untyped_nt': untyped_tup(a='hello', b='world', c='123')}

    assert c.to_dict() == {'my_nt': MyNT(my_float=1.23, my_str='string'),
                           'my_tup': (1, 2, 3),
                           'my_untyped_nt': untyped_tup(a='hello', b='world', c='123')}


@pytest.mark.parametrize(
    'input,expected',
    [
        ('2021-11-28T17:35:55', datetime(2021, 11, 28, 17, 35, 55)),
        (1577952245, datetime(2020, 1, 2, 3, 4, 5)),
        (datetime.min, datetime.min)
    ]
)
def test_load_to_datetime(input, expected):
    assert EnvLoader.load_to_datetime(input, datetime) == expected


@pytest.mark.parametrize(
    'input,expected',
    [
        ('2021-11-28', date(2021, 11, 28)),
        (1577952245, date(2020, 1, 2)),
        (date.min, date.min)
    ]
)
def test_load_to_date(input, expected):
    assert EnvLoader.load_to_date(input, date) == expected
