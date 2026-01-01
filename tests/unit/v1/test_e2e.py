import base64
import json
from collections import deque
from dataclasses import field, is_dataclass
from datetime import datetime, date, timezone
from typing import Optional, Union, NamedTuple, Literal

import pytest

from dataclass_wizard import asdict, fromdict, DataclassWizard, CatchAll
from dataclass_wizard.errors import ParseError, MissingFields
from dataclass_wizard.v1 import Alias
from .models import TN, CN, ContTF, ContTT, ContAllReq, Sub2, TNReq
from .utils_env import assert_unordered_equal
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
        'Boolean-Dict': {'test': [None, True, None]},
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

    # TODO
    # assert '`dict` input is not supported for NamedTuple, use a dataclass instead' in str(e.value)

    c = fromdict(MyClass, d)
    assert c == MyClass(nt_all_opts={'k': {NTAllOptionals()}},
                        nt_one_opt=[NTOneOptional(my_int=123, my_bool=False)])

    new_dict = asdict(c)
    assert new_dict == {
        'NtAllOpts': {
            'k': [['test', 1, True]]
        },
        'NtOneOpt': [
            [123, False]
        ]
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
    assert new_dict == {'my_td': {'test': [True, [{'a': 1, 'c': False, 'd': 23.0}]]}}


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
    assert_unordered_equal(new_dict, {'my_literal_dict': {'test': [123, ['Aa', 'Bb']]}})


def test_decode_date_and_datetime_from_numeric_and_string_timestamp_and_iso_format():

    class MyClass(DataclassWizard):
        my_value: float
        my_dt: datetime
        another_date: date

    d = {"another_date": "2021-12-17", "my_dt": "2022-04-27T16:30:45Z", "my_value": 1.23}
    expected_obj = MyClass(my_value=1.23,
                           my_dt=datetime(2022, 4, 27, 16, 30, 45, tzinfo=timezone.utc),
                           another_date=date(2021, 12, 17))
    expected_dict = {'my_value': 1.23, 'my_dt': '2022-04-27T16:30:45Z', 'another_date': '2021-12-17'}

    c1 = MyClass.from_dict(d)

    d = {"another_date": "1639763585", "my_dt": "1651077045", "my_value": '1.23'}
    c2 = MyClass.from_dict(d)

    d = {"another_date": 1639763585, "my_dt": 1651077045, "my_value": '1.23'}
    c3 = MyClass.from_dict(d)

    assert c1 == c2 == c3 == expected_obj
    assert c1.to_dict() == c2.to_dict() == c3.to_dict() == expected_dict


def test_json_bytes_roundtrip():
    class C(DataclassWizard):
        b: bytes

    raw = b'testing 123'
    c = C(b=raw)

    s = c.to_json()
    d = json.loads(s)

    # JSON representation should be base64 ascii string
    assert isinstance(d['b'], str)
    assert base64.b64decode(d['b']) == raw

    c2 = C.from_json(s)
    assert c2.b == raw


def test_json_bytearray_roundtrip():
    class C(DataclassWizard):
        b: bytearray

    raw = bytearray(b'abc')
    s = C(b=raw).to_json()
    c2 = C.from_json(s)
    assert c2.b == raw


def test_from_dict_bytes_requires_base64_str():
    class C(DataclassWizard):
        b: bytes

    with pytest.raises(ParseError):
        C.from_dict({'b': 'raw'})


def test_from_dict_bytes_accepts_bytes_and_bytearray():
    class C(DataclassWizard):
        b: bytes

    assert C.from_dict({'b': b'raw'}).b == b'raw'
    assert C.from_dict({'b': bytearray(b'raw')}).b == b'raw'


@pytest.mark.skipif(not PY310_OR_ABOVE, reason='requires Python 3.10 or higher')
def test_kw_only_fields_and_kw_only_catchall():
    from dataclasses import KW_ONLY

    class Sub(DataclassWizard):
        test: str
        _: KW_ONLY
        my_int: int

    class Parent(DataclassWizard, kw_only=True):
        opt: Optional[Sub]
        extras: CatchAll
        my_bool: bool = field(kw_only=False)

    p = Parent.from_dict({'my_bool': 'false',
                          'opt': {'my_int': '321', 'test': 123},
                          'hello': 0, 'world': 1})
    assert p == Parent(opt=Sub(test='123', my_int=321),
                       extras={'hello': 0, 'world': 1},
                       my_bool=False)

    assert p.to_dict() == {'my_bool': False,
                           'opt': {'test': '123', 'my_int': 321},
                           'hello': 0, 'world': 1}


def test_lazy_codegen_does_not_poison_subclasses():
    class A(DataclassWizard):
        a: int = 1

    class B(A):
        b: int = 2

    class C(B):
        c: int = 3

    assert is_dataclass(A) and is_dataclass(B) and is_dataclass(C)

    assert getattr(A.from_dict, '__func__', None) is fromdict
    assert getattr(B.from_dict, '__func__', None) is fromdict
    assert getattr(C.from_dict, '__func__', None) is fromdict

    a = A.from_dict({'a': '10'})
    assert type(a) is A
    assert a.a == 10

    b = B.from_dict({'a': '10', 'b': '20'})
    assert type(b) is B
    assert (b.a, b.b) == (10, 20)

    c = C.from_dict({'a': '10', 'b': '20', 'c': '30'})
    assert type(c) is C
    assert (c.a, c.b, c.c) == (10, 20, 30)

    # Ensure each class dumps its own fields correctly
    assert a.to_dict() == {'a': 10}
    assert b.to_dict() == {'a': 10, 'b': 20}
    assert c.to_dict() == {'a': 10, 'b': 20, 'c': 30}

    assert A.from_dict is not B.from_dict
    assert B.from_dict is not C.from_dict
    assert A.from_dict is not C.from_dict
    assert A.from_dict is not fromdict
    assert B.from_dict is not fromdict
    assert C.from_dict is not fromdict


class ContDict(DataclassWizard):
    class _(DataclassWizard.Meta):
        v1_namedtuple_as_dict = True

    tn: TN
    cn: CN


class ContDictReq(DataclassWizard):
    class _(DataclassWizard.Meta):
        v1_namedtuple_as_dict = True

    tn: TNReq


def test_namedtuple_dict_mode_roundtrip_and_defaults():
    o = ContDict.from_dict({"tn": {"a": 1}, "cn": {"a": 3}})
    assert o.tn == TN(a=1, b=2)
    assert o.cn == CN(a=3, b=2)

    d = o.to_dict()
    assert d == {"tn": {"a": 1, "b": 2}, "cn": {"a": 3, "b": 2}}


def test_namedtuple_no_field_defaults_dict_mode_roundtrip():
    o = ContDictReq.from_dict({"tn": {"b": 1, "a": 3}})

    assert o.tn == TN(a=3, b=1)

    d = o.to_dict()
    assert d == {'tn': {'a': 3, 'b': 1}}


def test_namedtuple_no_field_defaults_dict_mode_missing_required_raises():
    with pytest.raises(MissingFields, match=r'`TNReq.__init__\(\)` missing required fields') as e:
        _ = ContDictReq.from_dict({"tn": {"a": 1}})

    assert e.value.missing_fields == ['b']


def test_namedtuple_dict_mode_missing_required_raises():
    with pytest.raises(MissingFields, match=r'`TN\.__init__\(\)` missing required fields') as e:
        ContDict.from_dict({"tn": {"b": 9}, "cn": {"a": 1}})

    assert e.value.missing_fields == ['a']


class ContList(DataclassWizard):
    class _(DataclassWizard.Meta):
        v1_namedtuple_as_dict = False

    tn: TN
    cn: CN


def test_namedtuple_list_mode_roundtrip_and_defaults():
    o = ContList.from_dict({"tn": [1], "cn": [3]})
    assert o.tn == TN(a=1, b=2)
    assert o.cn == CN(a=3, b=2)

    d = o.to_dict()
    assert d == {"tn": [1, 2], "cn": [3, 2]}


def test_namedtuple_list_mode_rejects_dict_input_with_clear_error():
    with pytest.raises(ParseError, match=r"Dict input is not supported for NamedTuple fields in list mode.*list.*Meta\.v1_namedtuple_as_dict = True"):
        ContList.from_dict({"tn": {"a": 1}, "cn": {"a": 3}})


def test_namedtuple_dict_mode_rejects_dict_input_with_clear_error():
    with pytest.raises(ParseError, match=r"List/tuple input is not supported for NamedTuple fields in dict mode.*dict.*Meta\.v1_namedtuple_as_dict = False"):
        ContDict.from_dict({"tn": ['test'], "cn": {"a": 3}})


def test_typeddict_total_false_e2e_dict_roundtrip():
    o = ContTF.from_dict({"td": {"a": 1, "ro": 9}})
    assert o.td == {"a": 1, "ro": 9}

    d = o.to_dict()
    assert d == {"td": {"a": 1, "ro": 9}}


def test_typeddict_total_false_missing_required_raises():
    with pytest.raises(Exception):  # swap to MissingFields/TypeError etc
        ContTF.from_dict({"td": {"b": 2}})


def test_typeddict_total_true_e2e_optional_and_required_keys():
    o = ContTT.from_dict({"td": {"a": 1, "ro": 9}})
    assert o.td == {"a": 1, "ro": 9}

    d = o.to_dict()
    assert d == {"td": {"a": 1, "ro": 9}}

    with pytest.raises(Exception):
        ContTT.from_dict({"td": {"a": 1}})   # missing ro


def test_typeddict_all_required_e2e_inline_path():
    o = ContAllReq.from_dict({"td": {"x": 1, "y": "ok"}})
    assert o.td == {"x": 1, "y": "ok"}

    d = o.to_dict()
    assert d == {"td": {"x": 1, "y": "ok"}}

    with pytest.raises(Exception):
        ContAllReq.from_dict({"td": {"x": 1}})  # missing y


def test_v1_union_codegen_cache_nested_union_roundtrip_and_dump_error():
    class MyClass(DataclassWizard):
        class _(DataclassWizard.Meta):
            v1_unsafe_parse_dataclass_in_union = True

        complex_tp: 'list[int | Sub2] | list[int | str]'

    # First: pick the arm list[int|Sub2]
    o1 = MyClass.from_dict({"complex_tp": [{"my_float": "123."}, 7]})
    assert o1 == MyClass(complex_tp=[Sub2(my_float=123.0), 7])

    d1 = o1.to_dict()
    assert d1 == {"complex_tp": [{"my_float": 123.0}, 7]}

    # Second: pick the other arm list[int|str]
    # If inner-union codegen caching is wrong, this is where it tends to misbehave.
    o2 = MyClass.from_dict({"complex_tp": ["hello", 9]})
    assert o2 == MyClass(complex_tp=["hello", 9])

    d2 = o2.to_dict()
    assert d2 == {"complex_tp": ["hello", 9]}

    o1.complex_tp = '123'
    with pytest.raises(ParseError, match=r"Failed to dump field `complex_tp` in class `.*MyClass`"):
        _ = o1.to_dict()
