import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List
from unittest.mock import ANY

import pytest
from pytest_mock import MockerFixture

from dataclass_wizard import JSONSerializable
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
def mock_meta_initialize(mocker: MockerFixture):
    return mocker.patch(
        'dataclass_wizard.bases_meta.BaseJSONWizardMeta._meta_initialize')


@pytest.fixture
def mock_get_dumper(mocker: MockerFixture):
    return mocker.patch('dataclass_wizard.bases_meta.get_dumper')


def test_meta_initializer_runs_as_expected(mock_log):
    """
    Optional flags passed in when subclassing :class:`JSONSerializable.Meta`
    are correctly applied as expected.
    """

    @dataclass
    class MyClass(JSONSerializable):

        class Meta(JSONSerializable.Meta):
            debug_enabled = True
            json_key_to_field = {
                '__all__': True,
                'my_json_str': 'myCustomStr',
                'anotherJSONField': 'myCustomStr'
            }
            marshal_date_time_as = DateTimeTo.TIMESTAMP
            key_transform_with_load = 'Camel'
            key_transform_with_dump = LetterCase.SNAKE

        myStr: Optional[str]
        myCustomStr: str
        myDate: date
        listOfInt: List[int] = field(default_factory=list)
        isActive: bool = False
        myDt: Optional[datetime] = None

    mock_log.info.assert_called_once_with('DEBUG Mode is enabled')

    string = """
    {
        "my_str": 20,
        "my_json_str": "test that this is mapped to 'myCustomStr'",
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
    assert c.myCustomStr == "test that this is mapped to 'myCustomStr'"
    assert c.listOfInt == [1, 2, 3]
    assert c.isActive
    assert c.myDate == expected_date
    assert c.myDt == expected_dt

    d = c.to_dict()

    # Assert all JSON keys are converted to snake case
    expected_json_keys = ['my_str', 'list_of_int', 'is_active',
                          'my_date', 'my_dt', 'my_json_str']
    assert all(k in d for k in expected_json_keys)

    # Assert that date and datetime objects are serialized to timestamps (int)
    assert isinstance(d['my_date'], int)
    assert d['my_date'] == date_to_timestamp(expected_date)
    assert isinstance(d['my_dt'], int)
    assert d['my_dt'] == round(expected_dt.timestamp())


def test_json_key_to_field_when_add_is_a_falsy_value(mock_log):
    """
    The `json_key_to_field` attribute is specified when subclassing
    :class:`JSONSerializable.Meta`, but the `__all__` field a falsy value.

    Added for code coverage.
    """

    @dataclass
    class MyClass(JSONSerializable):

        class Meta(JSONSerializable.Meta):
            debug_enabled = True
            json_key_to_field = {
                '__all__': False,
                'my_json_str': 'myCustomStr',
                'anotherJSONField': 'myCustomStr'
            }
            key_transform_with_dump = LetterCase.SNAKE

        myCustomStr: str

    mock_log.info.assert_called_once_with('DEBUG Mode is enabled')

    string = """
    {
        "my_json_str": "test that this is mapped to 'myCustomStr'"
    }
    """
    c = MyClass.from_json(string)

    log.debug(repr(c))
    log.debug('Prettified JSON: %s', c)

    assert c.myCustomStr == "test that this is mapped to 'myCustomStr'"

    d = c.to_dict()

    # Assert that the default key transform is used when converting the
    # dataclass to JSON.
    assert 'my_json_str' not in d
    assert 'my_custom_str' in d
    assert d['my_custom_str'] == "test that this is mapped to 'myCustomStr'"


def test_meta_config_is_not_implicitly_shared_between_dataclasses(mock_log):

    @dataclass
    class MyFirstClass(JSONSerializable):

        class _(JSONSerializable.Meta):
            debug_enabled = True
            marshal_date_time_as = DateTimeTo.TIMESTAMP
            key_transform_with_load = 'Camel'
            key_transform_with_dump = LetterCase.SNAKE

        myStr: str

    @dataclass
    class MySecondClass(JSONSerializable):

        my_str: Optional[str]
        my_date: date
        list_of_int: List[int] = field(default_factory=list)
        is_active: bool = False
        my_dt: Optional[datetime] = None

    mock_log.info.assert_called_once_with('DEBUG Mode is enabled')

    string = """
    {"My_Str": "hello world"}
    """

    c = MyFirstClass.from_json(string)

    log.debug(repr(c))
    log.debug('Prettified JSON: %s', c)

    assert c.myStr == 'hello world'

    d = c.to_dict()
    assert 'my_str' in d
    assert d['my_str'] == 'hello world'

    string = """
    {
        "my_str": 20,
        "ListOfInt": ["1", "2", 3],
        "isActive": "true",
        "my_dt": "2020-01-02T03:04:05",
        "my_date": "2010-11-30"
    }
    """
    c = MySecondClass.from_json(string)

    log.debug(repr(c))
    log.debug('Prettified JSON: %s', c)

    expected_dt = datetime(2020, 1, 2, 3, 4, 5)
    expected_date = date(2010, 11, 30)

    assert c.my_str == '20'
    assert c.list_of_int == [1, 2, 3]
    assert c.is_active
    assert c.my_date == expected_date
    assert c.my_dt == expected_dt

    d = c.to_dict()

    # Assert all JSON keys are converted to snake case
    expected_json_keys = ['myStr', 'listOfInt', 'isActive',
                          'myDate', 'myDt']
    assert all(k in d for k in expected_json_keys)

    # Assert that date and datetime objects are serialized to timestamps (int)
    assert isinstance(d['myDate'], str)
    assert d['myDate'] == expected_date.isoformat()
    assert isinstance(d['myDt'], str)
    assert d['myDt'] == expected_dt.isoformat()


def test_meta_initializer_is_called_when_meta_is_an_inner_class(
        mock_meta_initializers):
    """
    Meta Initializer `dict` should be updated when `Meta` is an inner class.
    """

    class _(JSONSerializable):
        class _(JSONSerializable.Meta):
            debug_enabled = True

    mock_meta_initializers.__setitem__.assert_called_once()


def test_meta_initializer_not_called_when_meta_is_not_an_inner_class(
        mock_meta_initializers, mock_meta_initialize):
    """
    Meta Initializer `dict` should *not* be updated when `Meta` has no outer
    class.
    """

    class _(JSONSerializable.Meta):
        debug_enabled = True

    mock_meta_initializers.__setitem__.assert_not_called()
    mock_meta_initialize.assert_called_once_with(ANY, create=False)


def test_meta_initializer_errors_when_key_transform_with_load_is_invalid(
        mock_log):
    """
    Test when an invalid value for the ``key_transform_with_load`` attribute
    is specified when sub-classing from :class:`JSONSerializable.Meta`.

    """
    with pytest.raises(ParseError):

        @dataclass
        class _(JSONSerializable):
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
        class _(JSONSerializable):
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
        class _(JSONSerializable):
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
    class _(JSONSerializable):
        class Meta(JSONSerializable.Meta):
            marshal_date_time_as = 'ISO Format'

        my_str: Optional[str]
        list_of_int: List[int] = field(default_factory=list)

    mock_get_dumper().register_dump_hook.assert_not_called()
