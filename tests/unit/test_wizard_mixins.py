import pytest
from pytest_mock import MockerFixture

from dataclass_wizard import Container
from dataclass_wizard.wizard_mixins import (
    JSONListWizard, JSONFileWizard, YAMLWizard
)
from .conftest import SampleClass


class MyListWizard(SampleClass, JSONListWizard):
    ...


class MyFileWizard(SampleClass, JSONFileWizard):
    ...


@pytest.fixture
def mock_open(mocker: MockerFixture):
    return mocker.patch('dataclass_wizard.wizard_mixins.open')


def test_json_list_wizard_methods():

    c1 = MyListWizard.from_json('{"f1": "hello", "f2": 111}')
    assert c1.__class__ is MyListWizard

    c2 = MyListWizard.from_json('[{"f1": "hello", "f2": 111}]')
    assert c2.__class__ is Container

    c3 = MyListWizard.from_list([{"f1": "hello", "f2": 111}])
    assert c3.__class__ is Container

    assert c2 == c3


def test_json_file_wizard_methods(mocker: MockerFixture, mock_open):

    filename = 'my_file.json'
    my_dict = {'f1': 'Hello world!','f2': 123}

    mock_decoder = mocker.Mock()
    mock_decoder.return_value = my_dict

    c = MyFileWizard.from_json_file(filename,
                                    decoder=mock_decoder)

    mock_open.assert_called_once_with(filename)
    mock_decoder.assert_called_once()

    mock_encoder = mocker.Mock()
    mock_open.reset_mock()

    c.to_json_file(filename,
                   encoder=mock_encoder)

    mock_open.assert_called_once_with(filename, 'w')
    mock_encoder.assert_called_once_with(my_dict, mocker.ANY)
