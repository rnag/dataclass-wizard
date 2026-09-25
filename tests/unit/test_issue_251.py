"""Regression coverage for CatchAll constructor argument ordering."""

from dataclasses import dataclass, field, make_dataclass
import sys
from typing import Optional

import pytest

from dataclass_wizard import JSONWizard
from dataclass_wizard.models import CatchAll


@pytest.mark.parametrize('payload', [
    {},
    {'remember_me_cookie': 'abc'},
    {'extra': 42},
    {'remember_me_cookie': 'abc', 'extra': 42},
])
@pytest.mark.parametrize('kw_only', [False, True])
def test_catch_all_after_defaulted_field(payload, kw_only):
    """Defaulted fields must not receive the CatchAll positional value."""
    if kw_only and sys.version_info < (3, 10):
        pytest.skip('Keyword-only dataclass fields require Python 3.10')

    @dataclass
    class Foo(JSONWizard):
        """Model with a defaulted field before its CatchAll field."""

        remember_me_cookie: Optional[str] = None
        extra_data: CatchAll = field(
            default_factory=dict, **({'kw_only': True} if kw_only else {}))

    result = Foo.from_dict(payload)

    assert result.remember_me_cookie == payload.get('remember_me_cookie')
    assert result.extra_data == {
        key: value for key, value in payload.items()
        if key != 'remember_me_cookie'
    }


@pytest.mark.parametrize('position', [0, 1, 2])
def test_required_catch_all_field_position(position):
    """Required CatchAll fields retain their positional argument order."""
    fields = [('first', str), ('second', int)]
    fields.insert(position, ('extras', CatchAll))
    model = make_dataclass('Model', fields, bases=(JSONWizard,))
    result = model.from_dict({'first': 'value', 'second': 7, 'extra': 42})
    assert result.first == 'value'
    assert result.second == 7
    assert result.extras == {'extra': 42}


def test_default_factory_catch_all_between_defaulted_fields():
    """A default factory must work between other defaulted fields."""
    @dataclass
    class Model(JSONWizard):
        """Model with a CatchAll field between two optional fields."""

        first: str = 'default'
        extras: CatchAll = field(default_factory=dict)
        second: int = 0

    result = Model.from_dict({'first': 'value', 'second': 7, 'extra': 42})
    assert result == Model('value', {'extra': 42}, 7)
