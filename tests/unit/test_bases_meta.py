import logging
from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import Optional, List
from unittest.mock import ANY

import pytest
from pytest_mock import MockerFixture

from dataclass_wizard.bases import META
from dataclass_wizard import JSONWizard, EnvWizard
from dataclass_wizard.bases_meta import BaseJSONWizardMeta
from dataclass_wizard.enums import KeyCase, DateTimeTo
from dataclass_wizard.errors import ParseError
from dataclass_wizard.models import UTC

log = logging.getLogger(__name__)


def date_to_timestamp(d: date) -> int:
    """
    Retrieves the epoch timestamp of a :class:`date` object, as an `int`

    https://stackoverflow.com/a/15661036/10237506
    """
    dt = datetime.combine(d, time.min, tzinfo=UTC)
    return round(dt.timestamp())


@pytest.fixture
def mock_meta_initializers(mocker: MockerFixture):
    return mocker.patch('dataclass_wizard.bases_meta.META_INITIALIZER')


@pytest.fixture
def mock_bind_to(mocker: MockerFixture):
    return mocker.patch(
        'dataclass_wizard.bases_meta.BaseJSONWizardMeta.bind_to')


@pytest.fixture
def mock_env_bind_to(mocker: MockerFixture):
    return mocker.patch(
        'dataclass_wizard.bases_meta.BaseEnvWizardMeta.bind_to')


@pytest.fixture
def mock_get_dumper(mocker: MockerFixture):
    return mocker.patch('dataclass_wizard.bases_meta.get_dumper')


def test_merge_meta_with_or():
    """We are able to merge two Meta classes using the __or__ method."""
    class A(BaseJSONWizardMeta):
        v1_debug = True
        v1_dump_case = 'CAMEL'
        v1_dump_date_time_as = None
        tag = None
        v1_field_to_alias = {'k1': 'v1'}

    class B(BaseJSONWizardMeta):
        v1_debug = False
        v1_load_case = 'SNAKE'
        v1_dump_date_time_as = DateTimeTo.TIMESTAMP
        tag = 'My Test Tag'
        v1_field_to_alias = {'k2': 'v2'}

    # Merge the two Meta config together
    merged_meta: META = A | B

    # Assert we are a subclass of A, which subclasses from `BaseJSONWizardMeta`
    assert issubclass(merged_meta, BaseJSONWizardMeta)
    assert issubclass(merged_meta, A)
    assert merged_meta is not A

    # Assert Meta fields are merged from A and B as expected (with priority
    # given to A)
    assert 'CAMEL' == merged_meta.v1_dump_case == A.v1_dump_case
    assert 'SNAKE' == merged_meta.v1_load_case == B.v1_load_case
    assert None is merged_meta.v1_dump_date_time_as is A.v1_dump_date_time_as
    assert True is merged_meta.v1_debug is A.v1_debug
    # Assert that special attributes are only copied from A
    assert None is merged_meta.tag is A.tag
    assert {'k1': 'v1'} == merged_meta.v1_field_to_alias == A.v1_field_to_alias

    # Assert A and B have not been mutated
    assert A.v1_load_case is None
    assert B.v1_load_case == 'SNAKE'
    assert B.v1_field_to_alias == {'k2': 'v2'}
    # Assert that Base class attributes have not been mutated
    assert BaseJSONWizardMeta.v1_load_case is None
    assert BaseJSONWizardMeta.v1_field_to_alias is None


def test_merge_meta_with_and():
    """We are able to merge two Meta classes using the __or__ method."""
    class A(BaseJSONWizardMeta):
        v1_debug = True
        v1_dump_case = 'CAMEL'
        v1_dump_date_time_as = None
        tag = None
        v1_field_to_alias = {'v1': 'k1'}

    class B(BaseJSONWizardMeta):
        v1_debug = False
        v1_load_case = 'SNAKE'
        v1_dump_date_time_as = DateTimeTo.TIMESTAMP
        tag = 'My Test Tag'
        v1_field_to_alias = {'v2': 'k2'}

    # Merge the two Meta config together
    merged_meta: META = A & B

    # Assert we are a subclass of A, which subclasses from `BaseJSONWizardMeta`
    assert issubclass(merged_meta, BaseJSONWizardMeta)
    assert merged_meta is A

    # Assert Meta fields are merged from A and B as expected (with priority
    # given to A)
    assert 'CAMEL' == merged_meta.v1_dump_case == A.v1_dump_case
    assert 'SNAKE' == merged_meta.v1_load_case == B.v1_load_case
    assert DateTimeTo.TIMESTAMP is merged_meta.v1_dump_date_time_as is A.v1_dump_date_time_as
    assert False is merged_meta.v1_debug is A.v1_debug
    # Assert that special attributes are copied from B
    assert 'My Test Tag' == merged_meta.tag == A.tag
    assert {'v2': 'k2'} == merged_meta.v1_field_to_alias == A.v1_field_to_alias

    # Assert A has been mutated
    assert A.v1_load_case == B.v1_load_case == 'SNAKE'
    assert B.v1_field_to_alias == {'v2': 'k2'}
    # Assert that Base class attributes have not been mutated
    assert BaseJSONWizardMeta.v1_load_case is None
    assert BaseJSONWizardMeta.v1_field_to_alias is None


def test_meta_initializer_runs_as_expected(mock_log):
    """
    Optional flags passed in when subclassing :class:`JSONWizard.Meta`
    are correctly applied as expected.
    """

    @dataclass
    class MyClass(JSONWizard):

        class Meta(JSONWizard.Meta):
            v1_debug = True
            v1_field_to_alias = {
                'myCustomStr': ('my_json_str', 'anotherJSONField')
            }
            v1_dump_date_time_as = DateTimeTo.TIMESTAMP
            v1_load_case = 'AUTO'
            v1_dump_case = KeyCase.SNAKE
            v1_assume_naive_datetime_tz = UTC

        myStr: Optional[str]
        myCustomStr: str
        myDate: date
        listOfInt: List[int] = field(default_factory=list)
        isActive: bool = False
        myDt: Optional[datetime] = None

    # assert 'DEBUG Mode is enabled' in mock_log.text

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
    assert d['my_dt'] == round(expected_dt.replace(tzinfo=UTC).timestamp())


def test_field_to_alias_load_when_add_is_a_falsy_value():
    """
    The `field_to_alias_load` attribute is specified when subclassing
    :class:`JSONWizard.Meta`.

    Added for code coverage.
    """

    @dataclass
    class MyClass(JSONWizard):

        class Meta(JSONWizard.Meta):
            v1_field_to_alias_load = {'myCustomStr': ('my_json_str',
                                                      'anotherJSONField')}
            v1_dump_case = 'SNAKE'

        myCustomStr: str

    # note: this is only expected to run at most once
    # assert 'DEBUG Mode is enabled' in mock_log.text

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


def test_meta_config_is_not_implicitly_shared_between_dataclasses():

    @dataclass
    class MyFirstClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1_debug = True
            v1_dump_date_time_as = DateTimeTo.TIMESTAMP
            v1_load_case = 'SNAKE'
            v1_dump_case = KeyCase.SNAKE

        myStr: str

    @dataclass
    class MySecondClass(JSONWizard):
        class _(JSONWizard.Meta):
            v1_dump_case = KeyCase.CAMEL

        my_str: Optional[str]
        my_date: date
        list_of_int: List[int] = field(default_factory=list)
        is_active: bool = False
        my_dt: Optional[datetime] = None

    string = """
    {"my_str": "hello world"}
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
        "list_of_int": ["1", "2", 3],
        "is_active": "true",
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

    class _(JSONWizard):
        class _(JSONWizard.Meta):
            debug_enabled = True

    mock_meta_initializers.__setitem__.assert_called_once()


def test_env_meta_initializer_not_called_when_meta_is_not_an_inner_class(
        mock_meta_initializers, mock_env_bind_to):
    """
    Meta Initializer `dict` should *not* be updated when `Meta` has no outer
    class.
    """

    class _(EnvWizard.Meta):
        v1_debug = True

    mock_meta_initializers.__setitem__.assert_not_called()
    mock_env_bind_to.assert_called_once_with(ANY, create=False)


def test_meta_initializer_not_called_when_meta_is_not_an_inner_class(
        mock_meta_initializers, mock_bind_to):
    """
    Meta Initializer `dict` should *not* be updated when `Meta` has no outer
    class.
    """

    class _(JSONWizard.Meta):
        debug_enabled = True

    mock_meta_initializers.__setitem__.assert_not_called()
    mock_bind_to.assert_called_once_with(ANY, create=False)


def test_meta_initializer_errors_when_load_case_is_invalid():
    """
    Test when an invalid value for the ``load_case`` attribute
    is specified when sub-classing from :class:`JSONWizard.Meta`.

    """
    with pytest.raises(ParseError):

        @dataclass
        class _(JSONWizard):
            class Meta(JSONWizard.Meta):
                v1_load_case = 'Hello'

            my_str: Optional[str]
            list_of_int: List[int] = field(default_factory=list)


def test_meta_initializer_errors_when_dump_case_is_invalid():
    """
    Test when an invalid value for the ``dump_case`` attribute
    is specified when sub-classing from :class:`JSONWizard.Meta`.

    """
    with pytest.raises(ParseError):

        @dataclass
        class _(JSONWizard):
            class Meta(JSONWizard.Meta):
                v1_dump_case = 'World'

            my_str: Optional[str]
            list_of_int: List[int] = field(default_factory=list)


def test_meta_initializer_errors_when_marshal_date_time_as_is_invalid():
    """
    Test when an invalid value for the ``marshal_date_time_as`` attribute
    is specified when sub-classing from :class:`JSONWizard.Meta`.

    """
    with pytest.raises(ParseError):

        @dataclass
        class _(JSONWizard):
            class Meta(JSONWizard.Meta):
                v1_dump_date_time_as = 'TEST'

            my_str: Optional[str]
            list_of_int: List[int] = field(default_factory=list)


def test_meta_initializer_is_noop_when_marshal_date_time_as_is_iso_format(mock_get_dumper):
    """
    Test that it's a noop when the value for ``marshal_date_time_as``
    is `ISO_FORMAT`, which is the default conversion method for the dumper
    otherwise.

    """
    @dataclass
    class _(JSONWizard):
        class Meta(JSONWizard.Meta):
            marshal_date_time_as = 'ISO Format'

        my_str: Optional[str]
        list_of_int: List[int] = field(default_factory=list)

    mock_get_dumper().register_dump_hook.assert_not_called()
