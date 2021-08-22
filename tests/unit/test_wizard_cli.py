import logging
from textwrap import dedent
from unittest.mock import ANY

import pytest
from pytest_mock import MockerFixture

from dataclass_wizard.wizard_cli import main, PyCodeGenerator
from ..conftest import data_file_path


log = logging.getLogger(__name__)


def gen_schema(filename: str):
    """
    Helper function to call `wiz gen-schema` and pass the full path to a test
    file in the `testdata` directory.
    """

    main(['gs', data_file_path(filename), '-'])


def assert_py_code(expected, capfd=None, py_code=None):
    """
    Helper function to assert that generated Python code is as expected.
    """
    if py_code is None:
        py_code = _get_captured_py_code(capfd)

    # TODO update to `info` level to see the output in terminal.
    log.debug('Generated Python code:\n%s\n%s',
              '-' * 20, py_code)

    assert py_code == dedent(expected).lstrip()


def _get_captured_py_code(capfd) -> str:
    """Reads the Python code which is written to stdout."""
    out, err = capfd.readouterr()
    assert not err

    py_code_lines = out.split('\n')[4:]
    py_code = '\n'.join(py_code_lines)

    return py_code


@pytest.fixture
def mock_path(mocker: MockerFixture):
    return mocker.patch('dataclass_wizard.wizard_cli.schema.Path')


@pytest.fixture
def mock_stdin(mocker: MockerFixture):
    return mocker.patch('sys.stdin')


@pytest.fixture
def mock_open(mocker: MockerFixture):
    return mocker.patch('dataclass_wizard.wizard_cli.cli.open')


def test_call_py_code_generator_with_file_name(mock_path):
    """
    Test calling the constructor for :class:`PyCodeGenerator` with the
    `file_name` argument. Added for code coverage.
    """
    mock_path().read_bytes.return_value = b'{"key": "1.23", "secondKey": null}'

    expected = '''
    from dataclasses import dataclass
    from typing import Any, Optional


    @dataclass
    class Data:
        """
        Data dataclass

        """
        key: float
        second_key: Optional[Any]
    '''

    code_gen = PyCodeGenerator(file_name='my_file.txt',
                               force_strings=True)

    assert_py_code(expected, py_code=code_gen.py_code)


def test_call_wiz_cli_without_subcommand():
    """
    Calling wiz-cli without a sub-command. Added for code coverage.
    """
    with pytest.raises(SystemExit) as e:
        main([])

    assert e.value.code == 0


def test_call_wiz_cli_with_invalid_json_input(capsys, mock_stdin):
    """
    Calling wiz-cli with invalid JSON as input. Added for code coverage.
    """
    invalid_json = '{"key": "value"'

    mock_stdin.name = '<stdin>'
    mock_stdin.read.return_value = invalid_json

    with capsys.disabled():
        with pytest.raises(SystemExit) as e:
            main(['gs', '-', '-'])

        assert 'JSONDecodeError' in e.value.code


def test_call_wiz_cli_when_double_quotes_are_used_to_wrap_input(
        capsys, mock_stdin):
    """
    Calling wiz-cli when input is piped via stdin and the string is wrapped
    with double quotes instead of single quotes. Added for code coverage.
    """

    # Note: this can be the result of the following command:
    #   echo "{"key": "value"}" | wiz gs
    invalid_json = '\"{"key": "value"}\"'

    mock_stdin.name = '<stdin>'
    mock_stdin.read.return_value = invalid_json

    with capsys.disabled():
        with pytest.raises(SystemExit) as e:
            main(['gs', '-'])

        log.debug(e.value.code)
        assert 'double quotes' in e.value.code


def test_call_wiz_cli_with_mock_stdout(capsys, mock_stdin, mocker):
    """
    Calling wiz-cli with mock stdout. Added for code coverage.
    """
    valid_json = '{"key": "value"}'

    mock_stdin.name = '<stdin>'
    mock_stdin.read.return_value = valid_json

    with capsys.disabled():
        mock_stdout = mocker.patch('sys.stdout')
        mock_stdout.name = '<stdout>'
        mock_stdout.isatty.return_value = False

        main(['gs', '-', '-'])

    mock_stdout.write.assert_called()


def test_call_wiz_cli_with_output_filename_without_ext(
        mocker, mock_stdin, mock_open):
    """
    Calling wiz-cli with an output filename without an extension. The
    extension should automatically be added.
    """
    valid_json = '{"key": "value"}'

    mock_out = mocker.Mock()
    mock_out.name = 'testing'
    mock_out.fileno.return_value = 0

    mock_open.return_value = mock_out

    mock_stdin.name = '<stdin>'
    mock_stdin.read.return_value = valid_json

    main(['gs', '-', 'testing'])

    mock_open.assert_called_once_with(
        'testing.py', 'w', ANY, ANY, ANY)

    mock_out.write.assert_called_once()


def test_call_wiz_cli_when_open_raises_error(
        mocker, mock_stdin, mock_open):
    """
    Calling wiz-cli with an error is raised opening the JSON file.
    """
    valid_json = '{"key": "value"}'

    mock_open.side_effect = OSError

    mock_stdin.name = '<stdin>'
    mock_stdin.read.return_value = valid_json

    with pytest.raises(SystemExit) as e:
        main(['gs', '-', 'testing'])

    mock_open.assert_called_once()


def test_star_wars(capfd):

    expected = '''
    from dataclasses import dataclass
    from datetime import datetime
    from typing import Dict, List, Union


    @dataclass
    class Data:
        """
        Data dataclass

        """
        name: str
        rotation_period: Union[int, str]
        orbital_period: Union[int, str]
        diameter: Union[int, str]
        climate: str
        gravity: str
        terrain: str
        surface_water: Union[int, str]
        population: Union[int, str]
        residents: Dict
        films: List[str]
        created: datetime
        edited: datetime
        url: str
    '''

    gen_schema('star_wars.json')

    assert_py_code(expected, capfd)


def test_input_1(capfd):

    expected = '''
    from dataclasses import dataclass


    @dataclass
    class Data:
        """
        Data dataclass

        """
        key: str
        int_key: int
        float_key: float
        my_dict: 'MyDict'


    @dataclass
    class MyDict:
        """
        MyDict dataclass

        """
        key2: str
    '''

    gen_schema('test1.json')

    assert_py_code(expected, capfd)


def test_input_2(capfd):

    expected = '''
    from dataclasses import dataclass
    from datetime import datetime
    from typing import Optional, Union


    @dataclass
    class Container:
        """
        Container dataclass

        """
        data: 'Data'
        field_1: int
        field_2: str


    @dataclass
    class Data:
        """
        Data dataclass

        """
        key: Optional[str]
        another_key: Optional[Union[str, int]]
        truth: int
        my_list: 'MyList'
        my_date: datetime
        my_id: str


    @dataclass
    class MyList:
        """
        MyList dataclass

        """
        pass
    '''

    gen_schema('test2.json')

    assert_py_code(expected, capfd)


def test_input_3(capfd):

    expected = '''
    from dataclasses import dataclass
    from typing import List, Union


    @dataclass
    class Container:
        """
        Container dataclass

        """
        data: 'Data'
        field_1: int
        field_2: int
        field_3: str
        field_4: bool


    @dataclass
    class Data:
        """
        Data dataclass

        """
        true_story: Union[str, int]
        true_bool: bool
        my_list: List[Union[int, 'MyList']]


    @dataclass
    class MyList:
        """
        MyList dataclass

        """
        hey: str
    '''

    gen_schema('test3.json')

    assert_py_code(expected, capfd)


def test_input_4(capfd):

    expected = '''
    from dataclasses import dataclass
    from typing import Union


    @dataclass
    class Container:
        """
        Container dataclass

        """
        data: 'Data'


    @dataclass
    class Data:
        """
        Data dataclass

        """
        input_index: int
        candidate_index: int
        delivery_line_1: str
        last_line: str
        delivery_point_barcode: Union[int, str]
        components: 'Component'
        metadata: 'Metadatum'
        analysis: 'Analysis'


    @dataclass
    class Component:
        """
        Component dataclass

        """
        primary_number: Union[int, str]
        street_predirection: Union[bool, str]
        street_name: str
        street_suffix: str
        city_name: str
        state_abbreviation: str
        zipcode: Union[int, str]
        plus4_code: Union[int, str]
        delivery_point: Union[int, str]
        delivery_point_check_digit: Union[int, str]


    @dataclass
    class Metadatum:
        """
        Metadatum dataclass

        """
        record_type: str
        zip_type: str
        county_fips: Union[int, str]
        county_name: str
        carrier_route: str
        congressional_district: Union[int, str]
        rdi: str
        elot_sequence: Union[int, str]
        elot_sort: str
        latitude: float
        longitude: float
        precision: str
        time_zone: str
        utc_offset: int
        dst: bool


    @dataclass
    class Analysis:
        """
        Analysis dataclass

        """
        dpv_match_code: Union[bool, str]
        dpv_footnotes: str
        dpv_cmra: Union[bool, str]
        dpv_vacant: Union[bool, str]
        active: Union[bool, str]
    '''

    gen_schema('test4.json')

    assert_py_code(expected, capfd)


def test_input_5(capfd):

    expected = '''
    from dataclasses import dataclass
    from typing import List, Union


    @dataclass
    class Container:
        """
        Container dataclass

        """
        data: 'Data'
        field_1: List[Union[List[Union[str, 'Data2']], int, str]]


    @dataclass
    class Data:
        """
        Data dataclass

        """
        key: str


    @dataclass
    class Data2:
        """
        Data2 dataclass

        """
        key: int
        nested_classes: 'NestedClass'


    @dataclass
    class NestedClass:
        """
        NestedClass dataclass

        """
        blah: str
        another_one: List['AnotherOne']
        just_something_with_a_space: int


    @dataclass
    class AnotherOne:
        """
        AnotherOne dataclass

        """
        testing: str
    '''

    gen_schema('test5.json')

    assert_py_code(expected, capfd)


def test_input_6(capfd):

    expected = '''
    from dataclasses import dataclass
    from datetime import date, time
    from typing import List, Union


    @dataclass
    class Data:
        """
        Data dataclass

        """
        my_field: str
        another_field: date
        my_list: List[Union[int, 'MyList', List['Data2']]]


    @dataclass
    class MyList:
        """
        MyList dataclass

        """
        another_key: str


    @dataclass
    class Data2:
        """
        Data2 dataclass

        """
        key: str
        my_time: time
    '''

    gen_schema('test6.json')

    assert_py_code(expected, capfd)


def test_input_7(capfd):

    expected = '''
    from dataclasses import dataclass
    from typing import List, Union


    @dataclass
    class Container:
        """
        Container dataclass

        """
        data: 'Data'


    @dataclass
    class Data:
        """
        Data dataclass

        """
        my_test_apis: List['MyTestApi']
        people: List['Person']
        children: List['Child']
        activities: List['Activity']
        equipment: List['Equipment']
        key: int
        nested_classes: 'NestedClass'
        something_else: str


    @dataclass
    class MyTestApi:
        """
        MyTestApi dataclass

        """
        first_api: str


    @dataclass
    class Person:
        """
        Person dataclass

        """
        name: str
        age: Union[int, str]


    @dataclass
    class Child:
        """
        Child dataclass

        """
        name: str
        age: Union[int, float]


    @dataclass
    class Activity:
        """
        Activity dataclass

        """
        name: str


    @dataclass
    class Equipment:
        """
        Equipment dataclass

        """
        count: int


    @dataclass
    class NestedClass:
        """
        NestedClass dataclass

        """
        blah: str
        another_one: List['AnotherOne']
        just_something: int


    @dataclass
    class AnotherOne:
        """
        AnotherOne dataclass

        """
        testing: str
    '''

    gen_schema('test7.json')

    assert_py_code(expected, capfd)
