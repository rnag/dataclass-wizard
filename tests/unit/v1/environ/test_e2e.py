import json
from collections import deque
from typing import Optional, Union, NamedTuple, Literal, Mapping

import pytest

from dataclass_wizard import asdict, fromdict, DataclassWizard
from dataclass_wizard.errors import ParseError
from dataclass_wizard.v1 import Alias, EnvWizard, env_config

from ...._typing import *


def make_environ_safe(mapping: Mapping, *, dumps=json.dumps) -> dict[str, str]:
    """
    Convert a mapping into an env-like mapping: str keys, str values.

    - str values are kept as-is (no extra quoting).
    - everything else is JSON-encoded (stable representation for nested types).
    """
    out: dict[str, str] = {}
    for k, v in mapping.items():
        key = str(k)
        if isinstance(v, str):
            out[key] = v
        else:
            # stable JSON helps reproducible tests
            out[key] = dumps(v, separators=(",", ":"), sort_keys=True)
    return out


def test_nested_union_with_complex_types_in_containers():
    class Sub(DataclassWizard):
        test: str

    class MyClass(EnvWizard, debug=True):
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

    env = make_environ_safe(_input)

    c = MyClass(__env__=env_config(mapping=env))

    assert c.raw_dict() == {'my_bool': {'v': (None, True, None)},
                            'unionInListWithClass': ['s', Sub(test='hello'), 'value'],
                            'unionWithClass': Sub(test='world'), 'opt_class': Sub(test='value')}

    _input = {'Boolean-Dict': {'v': []},
              'UNION_IN_LIST_WITH_CLASS': ['', {'test': '123'}, None],
              'UNION_WITH_CLASS': 's',
              'OPT_CLASS': None}
    env = make_environ_safe(_input)

    c = MyClass(__env__=env_config(mapping=env))

    assert c.raw_dict() == {'my_bool': {'v': ()},
                            'unionInListWithClass': ['', Sub(test='123'), None], 'unionWithClass': 's',
                            'opt_class': None}


# def test_named_tuples_with_optionals_in_container():
#
#     class NTAllOptionals(NamedTuple):
#         a: str = 'test'
#         b: int = 1
#         c: bool = True
#
#     class NTOneOptional(NamedTuple):
#         my_int: int
#         my_bool: bool = False
#
#     class MyClass(EnvWizard):
#         class _(EnvWizard.Meta):
#             # v1 = True
#             v1_case = 'PASCAL'
#
#         nt_all_opts: dict[str, set[NTAllOptionals]]
#         nt_one_opt: list[NTOneOptional]
#
#     d = {'NtOneOpt': [['123']], 'NtAllOpts': {'k': [[]]}}
#
#     with pytest.raises(ParseError) as e:
#         _ = fromdict(MyClass, {'NtOneOpt': [{}], 'NtAllOpts': {'k': [[]]}})
#
#     assert '`dict` input is not supported for NamedTuple, use a dataclass instead' in str(e.value)
#
#     c = fromdict(MyClass, d)
#     assert c == MyClass(nt_all_opts={'k': {NTAllOptionals()}},
#                         nt_one_opt=[NTOneOptional(my_int=123, my_bool=False)])
#
#     new_dict = asdict(c)
#     assert new_dict == {
#         'NtAllOpts': {
#             'k': {NTAllOptionals()},
#         },
#         'NtOneOpt': [
#             NTOneOptional(my_int=123, my_bool=False)
#         ],
#     }
#
#
# def test_typed_dict_with_optionals_and_read_only_in_container():
#
#     class TDWithReadOnlyAndOpts(TypedDict):
#         a: int
#         b: NotRequired[str]
#         c: NotRequired[bool]
#         d: ReadOnly[float]
#
#     class MyClass(EnvWizard):
#         my_td: dict[str, tuple[bool, deque[TDWithReadOnlyAndOpts]]]
#
#     td_value = []
#     d = {'my_td': {'test': ['True', [td_value]]}}
#
#     with pytest.raises(ParseError) as e:
#         _ = fromdict(MyClass, d)
#     assert 'Expected a type {}, got list' in str(e.value)
#
#     td_value = {'d': '23'}
#     d = {'my_td': {'test': ['True', [td_value]]}}
#
#     with pytest.raises(ParseError) as e:
#         _ = fromdict(MyClass, d)
#     assert 'Missing required key: \'a\'' in str(e.value)
#
#     td_value = {'d': '23', 'a': '1', 'c': '0'}
#     d = {'my_td': {'test': ['True', [td_value]]}}
#
#     c = fromdict(MyClass, d)
#     assert c == MyClass(my_td={'test': (True, deque([{'a': 1, 'c': False, 'd': 23.0}]))})
#
#     new_dict = asdict(c)
#     assert new_dict == {'my_td': {'test': (True, deque([{'a': 1, 'c': False, 'd': 23.0}]))}}
#
#
# def test_literal_in_container():
#     class MyClass(EnvWizard):
#         my_literal_dict: dict[str, tuple[int, frozenset[Literal['Aa', 'Bb']]]]
#
#     d = {'my_literal_dict': {'test': ['123', ['aa', 'Bb']]}}
#
#     with pytest.raises(ParseError) as e:
#         _ = MyClass.from_dict(d)
#     assert 'Value not in expected Literal values' in str(e.value)
#
#     d = {'my_literal_dict': {'test': ['123', ['Bb', 'Aa']]}}
#     c = MyClass.from_dict(d)
#     # noinspection PyTypeChecker
#     assert c == MyClass(my_literal_dict={'test': (123, frozenset({'Aa', 'Bb'}))})
#
#     new_dict = c.to_dict()
#     assert new_dict == {'my_literal_dict': {'test': (123, {'Aa', 'Bb'})}}
