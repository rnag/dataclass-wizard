import pytest
from pytest_mock import MockerFixture

from dataclass_wizard import fromlist
from dataclass_wizard.models import Container, json_field
from .conftest import SampleClass


@pytest.fixture
def mock_open(mocker: MockerFixture):
    return mocker.patch('dataclass_wizard.models.open')


def test_json_field_does_not_allow_both_default_and_default_factory():
    """
    Confirm we can't specify both `default` and `default_factory` when
    calling the :func:`json_field` helper function.
    """
    with pytest.raises(ValueError):
        _ = json_field((), default=None, default_factory=None)


def test_container_with_incorrect_usage():
    """Confirm an error is raised when wrongly instantiating a Container."""
    c = Container()

    with pytest.raises(TypeError) as exc_info:
        _ = c.to_json()

    err_msg = exc_info.exconly()
    assert 'A Container object needs to be instantiated ' \
           'with a generic type T' in err_msg


def test_container_methods(mocker: MockerFixture, mock_open):
    list_of_dict = [{'f1': 'hello', 'f2': 1},
                    {'f1': 'world', 'f2': 2}]

    list_of_a = fromlist(SampleClass, list_of_dict)

    c = Container[SampleClass](list_of_a)

    # The repr() is very short, so it would be expected to fit in one line,
    # which thus aligns with the output of `pprint.pformat`.
    assert str(c) == repr(c)

    assert c.prettify() == """\
[
  {
    "f1": "hello",
    "f2": 1
  },
  {
    "f1": "world",
    "f2": 2
  }
]"""

    assert c.to_json() == '[{"f1": "hello", "f2": 1}, {"f1": "world", "f2": 2}]'

    mock_open.assert_not_called()
    mock_encoder = mocker.Mock()

    filename = 'my_file.json'
    c.to_json_file(filename, encoder=mock_encoder)

    mock_open.assert_called_once_with(filename, 'w')
    mock_encoder.assert_called_once_with(list_of_dict, mocker.ANY)
