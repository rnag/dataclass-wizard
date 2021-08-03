import logging
from dataclasses import dataclass

import pytest

from dataclass_wizard import JSONSerializable
from dataclass_wizard.enums import LetterCase
from dataclass_wizard.errors import ParseError
from ..conftest import *


log = logging.getLogger(__name__)


@pytest.mark.parametrize(
    'input,expectation',
    [
        ('testing', pytest.raises(ParseError)),
        ('e1', does_not_raise()),
        (False, pytest.raises(ParseError)),
        (0, does_not_raise()),
    ]
)
@pytest.mark.xfail(reason='still need to add the dump hook for this type')
def test_literal(input, expectation):

    @dataclass
    class MyClass(JSONSerializable):
        KEY_TRANSFORM_TO_DICT = LetterCase.PASCAL

        my_lit: Literal['e1', 'e2', 0]

    c = MyClass(my_lit=input)
    expected = {'MyLit': input}

    with expectation:
        actual = c.to_dict()

        assert actual == expected
        log.debug('Parsed object: %r', actual)


@pytest.mark.parametrize(
    'input,expectation',
    [
        (
            {}, pytest.raises(ParseError)),
        (
            {'key': 'value'}, pytest.raises(ParseError)),
        (
            {'my_str': 'test', 'my_int': 2,
             'my_bool': True, 'other_key': 'testing'}, does_not_raise()),
        (
            {'my_str': 3}, pytest.raises(ParseError)),
        (
            {'my_str': 'test', 'my_int': 'test', 'my_bool': True},
            pytest.raises(ValueError)),
        (
            {'my_str': 'test', 'my_int': 2, 'my_bool': True},
            does_not_raise(),
        )
    ]
)
@pytest.mark.xfail(reason='still need to add the dump hook for this type')
def test_typed_dict(input, expectation):

    class MyDict(TypedDict):
        my_str: str
        my_bool: bool
        my_int: int

    @dataclass
    class MyClass(JSONSerializable):
        my_typed_dict: MyDict

    c = MyClass(my_typed_dict=input)

    with expectation:
        result = c.to_dict()
        log.debug('Parsed object: %r', result)
