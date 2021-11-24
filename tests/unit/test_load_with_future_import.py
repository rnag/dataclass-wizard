from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

import pytest

from dataclass_wizard import JSONWizard, DumpMeta
from dataclass_wizard.errors import ParseError
from ..conftest import *

log = logging.getLogger(__name__)


@dataclass
class B:
    date_field: datetime.datetime | None


@dataclass
class C:
    ...


@dataclass
class D:
    ...


@dataclass
class DummyClass:
    ...


@pytest.mark.parametrize(
    'input,expectation',
    [
        # Wrong type: `my_field1` is passed in a float (not in valid Union types)
        ({'my_field1': 3.1, 'my_field2': [], 'my_field3': (3,)}, pytest.raises(ParseError)),
        # Wrong type: `my_field3` is passed a float type
        ({'my_field1': 3, 'my_field2': [], 'my_field3': 2.1}, pytest.raises(ParseError)),
        # Wrong type: `my_field3` is passed a list type
        ({'my_field1': 3, 'my_field2': [], 'my_field3': [1]}, pytest.raises(ParseError)),
        # Wrong type: `my_field3` is passed in a tuple of float (invalid Union type)
        ({'my_field1': 3, 'my_field2': [], 'my_field3': (1.0,)}, pytest.raises(ParseError)),
        # OK: `my_field3` is passed in a tuple of int (one of the valid Union types)
        ({'my_field1': 3, 'my_field2': [], 'my_field3': (1,)}, does_not_raise()),
        # Wrong number of elements for `my_field3`: expected only one
        ({'my_field1': 3, 'my_field2': [], 'my_field3': (1, 2)}, pytest.raises(ParseError)),
        # Type checks for all fields
        ({'my_field1': 'string',
          'my_field2': [{'date_field': None}],
          'my_field3': ('hello world',)}, does_not_raise()),

    ]
)
def test_load_with_future_annotation_v1(input, expectation):
    """
    Test case using the latest Python 3.10 features, such as PEP 604- style
    annotations.

    Ref: https://www.python.org/dev/peps/pep-0604/
    """

    @dataclass
    class A(JSONWizard):
        my_field1: bool | str | int
        my_field2: list[B]
        my_field3: int | tuple[str | int] | bool

    with expectation:
        result = A.from_dict(input)
        log.debug('Parsed object: %r', result)


@pytest.mark.parametrize(
    'input,expectation',
    [
        # Wrong type: `my_field2` is passed in a float (expected str, int, or None)
        ({'my_field1': datetime.date.min, 'my_field2': 1.23, 'my_field3': {'key': [None]}},
         pytest.raises(ParseError)),
        # Type checks
        ({'my_field1': datetime.date.max, 'my_field2': None, 'my_field3': {'key': []}}, does_not_raise()),
        # ParseError: expected list of B, C, D, or None; passed in a list of string instead.
        ({'my_field1': Decimal('3.1'), 'my_field2': 7, 'my_field3': {'key': ['hello']}},
         pytest.raises(ParseError)),
        # ParseError: expected list of B, C, D, or None; passed in a list of DummyClass instead.
        ({'my_field1': Decimal('3.1'), 'my_field2': 7, 'my_field3': {'key': [DummyClass()]}},
         pytest.raises(ParseError)),
        # Type checks
        ({'my_field1': Decimal('3.1'), 'my_field2': 7, 'my_field3': {'key': [None]}},
         does_not_raise()),
        # TODO enable once dataclasses are fully supported in Union types
        pytest.param({'my_field1': Decimal('3.1'), 'my_field2': 7, 'my_field3': {'key': [C()]}},
                     does_not_raise(),
                     marks=pytest.mark.skip('Dataclasses in Union types are '
                                            'not fully supported currently.')),
    ]
)
def test_load_with_future_annotation_v2(input, expectation):
    """
    Test case using the latest Python 3.10 features, such as PEP 604- style
    annotations.

    Ref: https://www.python.org/dev/peps/pep-0604/
    """

    @dataclass
    class A(JSONWizard):
        my_field1: Decimal | datetime.date | str
        my_field2: str | Optional[int]
        my_field3: dict[str | int, list[B | C | Optional[D]]]

    with expectation:
        result = A.from_dict(input)
        log.debug('Parsed object: %r', result)


def test_dataclasses_in_union_types():
    """Dataclasses in Union types when manually specifying `tag` value."""

    @dataclass
    class Container(JSONWizard):
        class _(JSONWizard.Meta):
            key_transform_with_dump = 'SNAKE'

        my_data: Data
        my_dict: dict[str, A | B]

    @dataclass
    class Data:
        my_str: str
        my_list: list[C | D]

    @dataclass
    class A(JSONWizard):
        class _(JSONWizard.Meta):
            tag = 'AA'

        val: str

    @dataclass
    class B(JSONWizard):
        class _(JSONWizard.Meta):
            tag = 'BB'

        val: int

    @dataclass
    class C(JSONWizard):
        class _(JSONWizard.Meta):
            tag = '_C_'

        my_field: int

    @dataclass
    class D(JSONWizard):
        class _(JSONWizard.Meta):
            tag = '_D_'

        my_field: float

    # Fix so the forward reference works
    globals().update(locals())

    c = Container.from_dict({
        'my_data': {
            'myStr': 'string',
            'MyList': [{'__tag__': '_D_', 'my_field': 1.23},
                       {'__tag__': '_C_', 'my_field': 3.21}]
        },
        'my_dict': {
            'key': {'__tag__': 'AA',
                    'val': '123'}
        }
    })

    expected_obj = Container(
        my_data=Data(my_str='string',
                     my_list=[D(my_field=1.23),
                              C(my_field=3)]),
        my_dict={'key': A(val='123')}
    )

    expected_dict = {
        "my_data": {"my_str": "string",
                    "my_list": [{"my_field": 1.23, "__tag__": "_D_"},
                                {"my_field": 3, "__tag__": "_C_"}]},
        "my_dict": {"key": {"val": "123", "__tag__": "AA"}}
    }

    assert c == expected_obj
    assert c.to_dict() == expected_dict


def test_dataclasses_in_union_types_with_auto_assign_tags():
    """
    Dataclasses in Union types with auto-assign tags, and a custom tag field.
    """
    @dataclass
    class Container(JSONWizard):
        class _(JSONWizard.Meta):
            key_transform_with_dump = 'SNAKE'
            tag_key = 'type'
            auto_assign_tags = True

        my_data: Data
        my_dict: dict[str, A | B]

    @dataclass
    class Data:
        my_str: str
        my_list: list[C | D | E]

    @dataclass
    class A:
        val: str

    @dataclass
    class B:
        val: int

    @dataclass
    class C:
        my_field: int

    @dataclass
    class D:
        my_field: float

    @dataclass
    class E:
        ...

    # This is to coverage a case where we have a Meta config for a class,
    # but we do not define a tag in the Meta config.
    DumpMeta(key_transform='SNAKE').bind_to(D)

    # Bind a custom tag to class E, so we can cover a case when
    # `auto_assign_tags` is true, but we are still able to specify a
    # custom tag for a class.
    DumpMeta(tag='!E').bind_to(E)

    # Fix so the forward reference works
    globals().update(locals())

    c = Container.from_dict({
        'my_data': {
            'myStr': 'string',
            'MyList': [{'type': 'D', 'my_field': 1.23},
                       {'type': 'C', 'my_field': 3.21},
                       {'type': '!E'}]
        },
        'my_dict': {
            'key': {'type': 'A',
                    'val': '123'}
        }
    })

    expected_obj = Container(
        my_data=Data(my_str='string',
                     my_list=[D(my_field=1.23),
                              C(my_field=3),
                              E()]),
        my_dict={'key': A(val='123')}
    )

    expected_dict = {
        "my_data": {"my_str": "string",
                    "my_list": [{"my_field": 1.23, "type": "D"},
                                {"my_field": 3, "type": "C"},
                                {'type': '!E'}]},
        "my_dict": {"key": {"val": "123", "type": "A"}}
    }

    assert c == expected_obj
    assert c.to_dict() == expected_dict
