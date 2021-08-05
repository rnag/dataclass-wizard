import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

import pytest
from pytest_mock import MockerFixture

from dataclass_wizard import JSONSerializable, DumpMixin, LoadMixin
from dataclass_wizard.enums import LetterCase, DateTimeTo


log = logging.getLogger(__name__)


@pytest.fixture
def mock_log(mocker: MockerFixture):
    return mocker.patch('dataclass_wizard.bases_meta.LOG')


def test_meta_initializer_runs_as_expected(mock_log):
    """
    Optional flags passed in when subclassing :class:`JSONSerializable.Meta`
    are correctly applied as expected.

    Note that I'm sub-classing from :class:`DumpMixin` here, even though it's
    technically not required, because I don't want to update the default key
    transform for classes in other test cases; if I didn't do that, it'll
    update the transform method in the base :class:`DumpMixin` class, which is
    the default for classes that don't sub-class from it.

    Also, because the other test cases assert for a more specific exception
    (not a :class:`ParseError` which will be raised when DEBUG mode is
    enabled), I'm also sub-classing from :class:`LoadMixin` for now.

    """

    @dataclass
    class MyClass(JSONSerializable, LoadMixin, DumpMixin):

        class Meta(JSONSerializable.Meta):
            debug_enabled = True
            marshal_date_time_as = DateTimeTo.TIMESTAMP
            key_transform_with_dump = LetterCase.SNAKE

        my_str: Optional[str]
        list_of_int: List[int] = field(default_factory=list)
        is_active: bool = False
        my_dt: Optional[datetime] = None

    mock_log.info.assert_called_once_with('DEBUG Mode is enabled')

    string = """
    {
        "my_str": 20,
        "ListOfInt": ["1", "2", 3],
        "isActive": "true",
        "my_dt": "2020-01-02T03:04:05"
    }
    """
    c = MyClass.from_json(string)

    log.debug(repr(c))
    log.debug('Prettified JSON: %s', c)

    expected_dt = datetime(2020, 1, 2, 3, 4, 5)

    assert c.my_str == '20'
    assert c.list_of_int == [1, 2, 3]
    assert c.is_active
    assert c.my_dt == expected_dt

    d = c.to_dict()

    # Assert all JSON keys are converted to snake case
    expected_json_keys = ['my_str', 'list_of_int', 'is_active', 'my_dt']
    assert all(k in d for k in expected_json_keys)

    # Assert that datetime objects are serialized to timestamps (int)
    assert isinstance(d['my_dt'], int)
    assert d['my_dt'] == round(expected_dt.timestamp())
