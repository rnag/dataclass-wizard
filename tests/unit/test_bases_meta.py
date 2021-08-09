import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List

import pytest
from pytest_mock import MockerFixture

from dataclass_wizard import JSONSerializable, DumpMixin, LoadMixin
from dataclass_wizard.enums import LetterCase, DateTimeTo
from dataclass_wizard.errors import ParseError
from dataclass_wizard.utils.type_conv import date_to_timestamp

log = logging.getLogger(__name__)


@pytest.fixture
def mock_log(mocker: MockerFixture):
    return mocker.patch('dataclass_wizard.bases_meta.LOG')


@pytest.fixture
def mock_meta_initializers(mocker: MockerFixture):
    return mocker.patch('dataclass_wizard.bases_meta._META_INITIALIZER')


@pytest.fixture
def mock_get_dumper(mocker: MockerFixture):
    return mocker.patch('dataclass_wizard.bases_meta.get_dumper')


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
            key_transform_with_load = 'Camel'
            key_transform_with_dump = LetterCase.SNAKE

        myStr: Optional[str]
        myDate: date
        listOfInt: List[int] = field(default_factory=list)
        isActive: bool = False
        myDt: Optional[datetime] = None

    mock_log.info.assert_called_once_with('DEBUG Mode is enabled')

    string = """
    {
        "my_str": 20,
        "ListOfInt": ["1", "2", 3],
        "isActive": "true",
        "my_dt": "2020-01-02T03:04:05",
        "my_date": "2010-11-30"
    }
    """
    c = MyClass.from_json(string)

    log.debug(repr(c))
    log.debug('Prettified JSON: %s', c)

    expected_dt = datetime(2020, 1, 2, 3, 4, 5)
    expected_date = date(2010, 11, 30)

    assert c.myStr == '20'
    assert c.listOfInt == [1, 2, 3]
    assert c.isActive
    assert c.myDate == expected_date
    assert c.myDt == expected_dt

    d = c.to_dict()

    # Assert all JSON keys are converted to snake case
    expected_json_keys = ['my_str', 'list_of_int', 'is_active',
                          'my_date', 'my_dt']
    assert all(k in d for k in expected_json_keys)

    # Assert that date and datetime objects are serialized to timestamps (int)
    assert isinstance(d['my_date'], int)
    assert d['my_date'] == date_to_timestamp(expected_date)
    assert isinstance(d['my_dt'], int)
    assert d['my_dt'] == round(expected_dt.timestamp())


def test_meta_initializer_is_called_when_meta_is_an_inner_class(
        mock_meta_initializers):
    """
    Meta Initializer `dict` should be updated when `Meta` is an inner class.

    Note: we're mocking the `__setitem__` for the meta initializers here, so
    we don't need to inherit from :class:`LoadMixin` or :class:`DumpMixin`.
    """
    class _(JSONSerializable):
        class _(JSONSerializable.Meta):
            debug_enabled = True

    mock_meta_initializers.__setitem__.assert_called_once()


def test_meta_initializer_not_called_when_meta_is_not_an_inner_class(
        mock_meta_initializers):
    """
    Meta Initializer `dict` should *not* be updated when `Meta` has no outer
    class.

    Note: we're mocking the `__setitem__` for the meta initializers here, so
    we don't need to inherit from :class:`LoadMixin` or :class:`DumpMixin`.
    """
    class _(JSONSerializable.Meta):
        debug_enabled = True

    mock_meta_initializers.__setitem__.assert_not_called()


def test_meta_initializer_errors_when_key_transform_with_load_is_invalid(
        mock_log):
    """
    Test when an invalid value for the ``key_transform_with_load`` attribute
    is specified when sub-classing from :class:`JSONSerializable.Meta`.

    """
    with pytest.raises(ParseError):

        @dataclass
        class _(JSONSerializable, LoadMixin, DumpMixin):
            class Meta(JSONSerializable.Meta):
                key_transform_with_load = 'Hello'

            my_str: Optional[str]
            list_of_int: List[int] = field(default_factory=list)


def test_meta_initializer_errors_when_key_transform_with_dump_is_invalid(
        mock_log):
    """
    Test when an invalid value for the ``key_transform_with_dump`` attribute
    is specified when sub-classing from :class:`JSONSerializable.Meta`.

    """
    with pytest.raises(ParseError):

        @dataclass
        class _(JSONSerializable, LoadMixin, DumpMixin):
            class Meta(JSONSerializable.Meta):
                key_transform_with_dump = 'World'

            my_str: Optional[str]
            list_of_int: List[int] = field(default_factory=list)


def test_meta_initializer_errors_when_marshal_date_time_as_is_invalid(
        mock_log):
    """
    Test when an invalid value for the ``marshal_date_time_as`` attribute
    is specified when sub-classing from :class:`JSONSerializable.Meta`.

    """
    with pytest.raises(ParseError):

        @dataclass
        class _(JSONSerializable, LoadMixin, DumpMixin):
            class Meta(JSONSerializable.Meta):
                marshal_date_time_as = 'iso'

            my_str: Optional[str]
            list_of_int: List[int] = field(default_factory=list)


def test_meta_initializer_is_noop_when_marshal_date_time_as_is_iso_format(
        mock_log, mock_get_dumper):
    """
    Test that it's a noop when the value for ``marshal_date_time_as``
    is `ISO_FORMAT`, which is the default conversion method for the dumper
    otherwise.

    """
    @dataclass
    class _(JSONSerializable, LoadMixin, DumpMixin):
        class Meta(JSONSerializable.Meta):
            marshal_date_time_as = 'ISO Format'

        my_str: Optional[str]
        list_of_int: List[int] = field(default_factory=list)

    mock_get_dumper().register_dump_hook.assert_not_called()
