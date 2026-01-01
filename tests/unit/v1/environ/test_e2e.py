from collections import deque
from dataclasses import field
from datetime import datetime, date, timezone
from typing import Optional, Union, NamedTuple, Literal

import pytest

from dataclass_wizard import DataclassWizard, CatchAll
from dataclass_wizard.errors import ParseError, MissingVars, MissingFields
from dataclass_wizard.v1 import Alias, EnvWizard, env_config, AliasPath
from ..models import TN, CN, EnvContTF, EnvContTT, EnvContAllReq, Sub2

from ..utils_env import envsafe, from_env, assert_unordered_equal
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

    # TODO
    # assert '`dict` input is not supported for NamedTuple, use a dataclass instead' in str(e.value)

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
    assert_unordered_equal(new_dict, {'my_literal_dict': {'test': [123, ['Aa', 'Bb']]}})


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


def test_future_warning_with_deprecated_meta_field__is_logged():
    """Deprecated field `field_to_env_var` usage in `v1` opt-in should show user a warning."""

    with pytest.warns(FutureWarning, match=r"`field_to_env_var` is deprecated"):
        class MyClass(EnvWizard):
            class _(EnvWizard.Meta):
                field_to_env_var = {'my_value': 'MyVal', 'other_key': ('INT1', 'INT2')}

            my_value: float
            other_key: int = 3


    env = {'MyVal': '1.23', 'INT2': '7.0'}

    c = from_env(MyClass, env)

    assert c == MyClass(my_value=1.23, other_key=7)
    assert c.raw_dict() == {'my_value': 1.23, 'other_key': 7}


def test_env_bytes_from_string_is_utf8():
    class C(EnvWizard):
        b: bytes

    c = from_env(C, {'B': 'testing 123'})
    assert c.b == b'testing 123'


def test_env_bytearray_from_string_is_utf8():
    class C(EnvWizard):
        b: bytearray

    c = from_env(C, {'B': 'testing 123'})
    assert c.b == bytearray(b'testing 123')


def test_env_bytearray_from_bytes_and_list():
    class C(EnvWizard):
        b: bytearray

    assert C(__env__=env_config(mapping={'B': b'abc'})).b == bytearray(b'abc')
    assert C(__env__=env_config(mapping={'B': [1, 2, 3]})).b == bytearray([1, 2, 3])


def test_env_with_no_init_fields():
    """Test EnvWizard` subclass with no *init-only *dataclass fields."""
    class E1(EnvWizard):
        ...

    assert E1().raw_dict() == {}

    class E2(EnvWizard):
        my_field: str = field(init=False)

        def __post_init__(self, __env__=None):
            self.my_field = '123'

    assert E2().raw_dict() == {'my_field': '123'}


def test_env_with_catch_all():
    class E(EnvWizard):
        field: CatchAll = None

    class MyDict(dict):
        def __bool__(self):
            return True

    e = E(__env__={'mapping': MyDict()})
    assert e.field is None
    assert e.to_dict() == {}

    e = from_env(E, {'k1': 'v1', 'k2': ['v2']})
    assert e.to_dict() == e.field == {'k1': 'v1', 'k2': '["v2"]'}

    class E(EnvWizard):
        field: CatchAll

    e = from_env(E, {'k1': 'v1', 'k2': ['v2']})
    assert e.to_dict() == e.field == {'k1': 'v1', 'k2': '["v2"]'}

    class E(EnvWizard):
        my_int: int
        extras: CatchAll

    e = from_env(E, {'MY_INT': '123',
                     'k1': 'v1',
                     'k2': ['v2']})

    assert e.extras == {'k1': 'v1', 'k2': '["v2"]'}
    assert e.raw_dict() == {'my_int': 123, 'extras': {'k1': 'v1', 'k2': '["v2"]'}}
    assert e.to_dict() == {'my_int': 123, 'k1': 'v1', 'k2': '["v2"]'}


def test_env_precedence_env_only():
    class E(EnvWizard):
        my_value: float

        class _(EnvWizard.Meta):
            v1_env_precedence = 'ENV_ONLY'
            # contains `MY_VALUE=1.23`
            env_file = '.env.test'

    with pytest.raises(MissingVars) as e:
        _ = E()

    assert e.value.fields.lstrip() == '- my_value -> MY_VALUE'

    e = from_env(E, {'MY_VALUE': '3.21'})
    assert e.raw_dict() == {'my_value': 3.21}


def test_env_load_case_strict():
    class E(EnvWizard):
        my_value: float

        class _(EnvWizard.Meta):
            v1_load_case = 'STRICT'

    with pytest.raises(MissingVars) as e:
        _ = from_env(E, {'my_value': 3.21})

    assert e.value.fields.lstrip() == '- my_value -> my_value'

    e = E(my_value='3.21')
    assert e.raw_dict() == {'my_value': 3.21}


def test_env_alias_path_required():
    class E(EnvWizard):
        my_value: float = AliasPath('a.b.c')

    e = E(my_value=3.21)
    assert e.raw_dict() == {'my_value': 3.21}

    e = E(__env__={'mapping': {'a': {'b': {'c': '2.22'}}}})
    assert e.raw_dict() == {'my_value': 2.22}

    e = from_env(E, {'a': {'b': {'c': '1.11'}}})
    assert e.raw_dict() == {'my_value': 1.11}

    with pytest.raises(ParseError) as e:
        _ = from_env(E, {'a': {'b': {'z': '1.11'}}})
    assert e.value.kwargs['current_path'] == "'c'"

    with pytest.raises(ParseError) as e:
        _ = from_env(E, {'a': []})
    assert str(e.value.base_error) == 'Invalid path'


def test_env_alias_path_with_default_value():
    class E(EnvWizard):
        my_value: list[float] = AliasPath('a.b.c', default_factory=list)
        another_value: Optional[str] = AliasPath('x.y.z', default=None)

    e = E(my_value=[3.21])
    assert e.raw_dict() == {'my_value': [3.21], 'another_value': None}

    e = E(__env__={'mapping': {'a': {'b': {'c': ['2.22']}},
                                'x': {'y': {'z': 3.333}}}})
    assert e.raw_dict() == {'my_value': [2.22], 'another_value': '3.333'}

    e = from_env(E, {'a': {'b': {'c': ['1.11', '2.', 3.7]}},
                      'x': {'y': {'z': 5.55}}})
    assert e.raw_dict() == {'my_value': [1.11, 2.0, 3.7], 'another_value': '5.55'}

    e = from_env(E, {'a': {'b': {'z': '1.11'}}})
    assert e == E(my_value=[], another_value=None)

    with pytest.raises(ParseError) as e:
        _ = from_env(E, {'a': []})
    assert str(e.value.base_error) == 'Invalid path'


def test_env_alias_path_with_multiple_paths():
    class E2(EnvWizard):
        my_value: float = AliasPath('a.b.c', 'x.y.z[0]')

    e = E2(my_value='3.21')
    assert e.raw_dict() == {'my_value': 3.21}

    e = E2(__env__={'mapping': {'a': {'b': {'c': '2.22'}}}})
    assert e.raw_dict() == {'my_value': 2.22}

    e = from_env(E2, {'a': {'b': {'c': '1.11'}}})
    assert e.raw_dict() == {'my_value': 1.11}

    e = from_env(E2, {'x': {'y': {'z': ['3.33', '4.44']}}})
    assert e == E2(my_value=3.33)

    with pytest.raises(ParseError) as e:
        _ = from_env(E2, {'a': []})
    assert str(e.value.base_error) == 'Invalid path'


def test_namedtuple_dict_mode_roundtrip_and_defaults():
    class EnvContDict(EnvWizard):
        class _(EnvWizard.Meta):
            v1_namedtuple_as_dict = True

        tn: TN
        cn: CN

    o = from_env(EnvContDict, {"tn": {"a": 1}, "cn": {"a": 3}})
    assert o.tn == TN(a=1, b=2)
    assert o.cn == CN(a=3, b=2)

    d = o.to_dict()
    assert d == {"tn": {"a": 1, "b": 2}, "cn": {"a": 3, "b": 2}}


# TODO
# def test_namedtuple_dict_mode_missing_required_raises():
#     with pytest.raises(MissingFields, match=r'`TN\.__init__\(\)` missing required fields') as e:
#         from_env(EnvContDict, {"tn": {"b": 9}, "cn": {"a": 1}})
#
#     assert e.value.missing_fields == ['a']


def test_namedtuple_list_mode_roundtrip_and_defaults():
    class EnvContList(EnvWizard):
        class _(EnvWizard.Meta):
            v1_namedtuple_as_dict = False

        tn: TN
        cn: CN

    o = from_env(EnvContList, {"tn": [1], "cn": [3]})
    assert o.tn == TN(a=1, b=2)
    assert o.cn == CN(a=3, b=2)

    d = o.to_dict()
    assert d == {"tn": [1, 2], "cn": [3, 2]}


# def test_namedtuple_list_mode_rejects_dict_input_with_clear_error():
#     with pytest.raises(ParseError, match=r"Dict input is not supported for NamedTuple fields in list mode.*list.*Meta\.v1_namedtuple_as_dict = True"):
#         from_env(EnvContList, {"tn": {"a": 1}, "cn": {"a": 3}})


def test_typeddict_total_false_e2e_dict_roundtrip():
    o = from_env(EnvContTF, {"td": {"a": 1, "ro": 9}})
    assert o.td == {"a": 1, "ro": 9}

    d = o.to_dict()
    assert d == {"td": {"a": 1, "ro": 9}}


def test_typeddict_total_false_missing_required_raises():
    with pytest.raises(Exception):  # swap to MissingFields/TypeError etc
        from_env(EnvContTF, {"td": {"b": 2}})


def test_typeddict_total_true_e2e_optional_and_required_keys():
    o = from_env(EnvContTT, {"td": {"a": 1, "ro": 9}})
    assert o.td == {"a": 1, "ro": 9}

    d = o.to_dict()
    assert d == {"td": {"a": 1, "ro": 9}}

    with pytest.raises(Exception):
        from_env(EnvContTT, {"td": {"a": 1}})   # missing ro


def test_typeddict_all_required_e2e_inline_path():
    o = from_env(EnvContAllReq, {"td": {"x": 1, "y": "ok"}})
    assert o.td == {"x": 1, "y": "ok"}

    d = o.to_dict()
    assert d == {"td": {"x": 1, "y": "ok"}}

    with pytest.raises(Exception):
        from_env(EnvContAllReq, {"td": {"x": 1}})  # missing y


def test_v1_union_codegen_cache_nested_union_roundtrip_and_dump_error():
    class MyClass(EnvWizard):
        class _(EnvWizard.Meta):
            v1_unsafe_parse_dataclass_in_union = True

        complex_tp: 'list[int | Sub2] | list[int | str]'

    # First: pick the arm list[int|Sub2]
    o1 = from_env(MyClass, {"complex_tp": [{"my_float": "123."}, 7]})
    assert o1 == MyClass(complex_tp=[Sub2(my_float=123.0), 7])

    d1 = o1.to_dict()
    assert d1 == {"complex_tp": [{"my_float": 123.0}, 7]}

    # Second: pick the other arm list[int|str]
    # If inner-union codegen caching is wrong, this is where it tends to misbehave.
    o2 = from_env(MyClass, {"complex_tp": ["hello", 9]})
    assert o2 == MyClass(complex_tp=["hello", 9])

    d2 = o2.to_dict()
    assert d2 == {"complex_tp": ["hello", 9]}

    o1.complex_tp = '123'
    with pytest.raises(ParseError, match=r"Failed to dump field `complex_tp` in class `.*MyClass`"):
        _ = o1.to_dict()
