from collections import deque
from typing import Optional, Union, NamedTuple, Literal

import pytest

from dataclass_wizard import asdict, fromdict, DataclassWizard
from dataclass_wizard.errors import ParseError
from dataclass_wizard.v1 import Alias

from ..._typing import *


def test_nested_union_with_complex_types_in_containers():

    class Sub(DataclassWizard):
        test: str

    class MyClass(DataclassWizard):
        class _(DataclassWizard.Meta):
            v1_case = 'CAMEL'
            auto_assign_tags = True

        # noinspection PyDataclass
        my_bool: dict[str, tuple[Optional[bool], ...]] = Alias('Boolean-Dict')
        nestedUnionWithClass: list[Union[str, Sub]]

    d = {'Boolean-Dict': {'test': [None, 'tRuE', None]}, 'nestedUnionWithClass': [123, {'__tag__': 'Sub', 'test': 'value'}]}

    c = fromdict(MyClass, d)
    assert c == MyClass(
        my_bool={'test': (None, True, None)},
        nestedUnionWithClass=['123', Sub(test='value')],
    )

    new_dict = asdict(c)
    assert new_dict == {
        'Boolean-Dict': {'test': (None, True, None)},
        'nestedUnionWithClass': ['123', {'test': 'value', '__tag__': 'Sub'}]
    }


def test_named_tuples_with_optionals_in_container():

    class NTAllOptionals(NamedTuple):
        a: str = 'test'
        b: int = 1
        c: bool = True

    class NTOneOptional(NamedTuple):
        my_int: int
        my_bool: bool = False

    class MyClass(DataclassWizard):
        class _(DataclassWizard.Meta):
            # v1 = True
            v1_case = 'PASCAL'

        nt_all_opts: dict[str, set[NTAllOptionals]]
        nt_one_opt: list[NTOneOptional]

    d = {'NtOneOpt': [['123']], 'NtAllOpts': {'k': [[]]}}

    with pytest.raises(ParseError) as e:
        _ = fromdict(MyClass, {'NtOneOpt': [{}], 'NtAllOpts': {'k': [[]]}})

    assert '`dict` input is not supported for NamedTuple, use a dataclass instead' in str(e.value)

    c = fromdict(MyClass, d)
    assert c == MyClass(nt_all_opts={'k': {NTAllOptionals()}},
                        nt_one_opt=[NTOneOptional(my_int=123, my_bool=False)])

    new_dict = asdict(c)
    assert new_dict == {
        'NtAllOpts': {
            'k': {NTAllOptionals()},
        },
        'NtOneOpt': [
            NTOneOptional(my_int=123, my_bool=False)
        ],
    }


def test_typed_dict_with_optionals_and_read_only_in_container():

    class TDWithReadOnlyAndOpts(TypedDict):
        a: int
        b: NotRequired[str]
        c: NotRequired[bool]
        d: ReadOnly[float]

    class MyClass(DataclassWizard):
        my_td: dict[str, tuple[bool, deque[TDWithReadOnlyAndOpts]]]

    td_value = []
    d = {'my_td': {'test': ['True', [td_value]]}}

    with pytest.raises(ParseError) as e:
        _ = fromdict(MyClass, d)
    assert 'Expected a type {}, got list' in str(e.value)

    td_value = {'d': '23'}
    d = {'my_td': {'test': ['True', [td_value]]}}

    with pytest.raises(ParseError) as e:
        _ = fromdict(MyClass, d)
    assert 'Missing required key: \'a\'' in str(e.value)

    td_value = {'d': '23', 'a': '1', 'c': '0'}
    d = {'my_td': {'test': ['True', [td_value]]}}

    c = fromdict(MyClass, d)
    assert c == MyClass(my_td={'test': (True, deque([{'a': 1, 'c': False, 'd': 23.0}]))})

    new_dict = asdict(c)
    assert new_dict == {'my_td': {'test': (True, deque([{'a': 1, 'c': False, 'd': 23.0}]))}}


def test_literal_in_container():
    class MyClass(DataclassWizard):
        my_literal_dict: dict[str, tuple[int, frozenset[Literal['Aa', 'Bb']]]]

    d = {'my_literal_dict': {'test': ['123', ['aa', 'Bb']]}}

    with pytest.raises(ParseError) as e:
        _ = MyClass.from_dict(d)
    assert 'Value not in expected Literal values' in str(e.value)

    d = {'my_literal_dict': {'test': ['123', ['Bb', 'Aa']]}}
    c = MyClass.from_dict(d)
    # noinspection PyTypeChecker
    assert c == MyClass(my_literal_dict={'test': (123, frozenset({'Aa', 'Bb'}))})

    new_dict = c.to_dict()
    assert new_dict == {'my_literal_dict': {'test': (123, {'Aa', 'Bb'})}}
