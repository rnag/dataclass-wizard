import pytest

from dataclass_wizard.utils.string_conv import *


@pytest.mark.parametrize(
    'string,expected',
    [
        ('device_type', 'deviceType'),
        ('io_error', 'ioError'),
        ('isACamelCasedWORD', 'isACamelCasedWORD'),
        ('ATitledWordToTESTWith', 'aTitledWordToTESTWith'),
        ('not-a-tester', 'notATester'),
        ('device_type', 'deviceType'),
        ('helloworld', 'helloworld'),
        ('A', 'a'),
        ('TESTing_if_thisWorks', 'tESTingIfThisWorks'),
        ('a_B_Cde_fG_hi', 'aBCdeFGHi'),
        ('ALL_CAPS', 'aLLCAPS'),
        ('WoRd', 'woRd'),
        ('HIThereHOWIsItGoinG', 'hIThereHOWIsItGoinG'),
        ('How_-Are-_YoUDoing__TeST', 'howAreYoUDoingTeST'),
        ('thisIsWithANumber42ToTEST', 'thisIsWithANumber42ToTEST'),
        ('Number 42 With spaces', 'number42WithSpaces')
    ]
)
def test_to_camel_case(string, expected):
    actual = to_camel_case(string)
    assert actual == expected


@pytest.mark.parametrize(
    'string,expected',
    [
        ('device_type', 'DeviceType'),
        ('io_error', 'IoError'),
        ('isACamelCasedWORD', 'IsACamelCasedWORD'),
        ('ATitledWordToTESTWith', 'ATitledWordToTESTWith'),
        ('not-a-tester', 'NotATester'),
        ('device_type', 'DeviceType'),
        ('helloworld', 'Helloworld'),
        ('A', 'A'),
        ('TESTing_if_thisWorks', 'TESTingIfThisWorks'),
        ('a_B_Cde_fG_hi', 'ABCdeFGHi'),
        ('ALL_CAPS', 'ALLCAPS'),
        ('WoRd', 'WoRd'),
        ('HIThereHOWIsItGoinG', 'HIThereHOWIsItGoinG'),
        ('How_-Are-_YoUDoing__TeST', 'HowAreYoUDoingTeST'),
        ('thisIsWithANumber42ToTEST', 'ThisIsWithANumber42ToTEST'),
        ('Number 42 With spaces', 'Number42WithSpaces')
    ]
)
def test_to_pascal_case(string, expected):
    actual = to_pascal_case(string)
    assert actual == expected


@pytest.mark.parametrize(
    'string,expected',
    [
        ('device_type', 'device-type'),
        ('IO_Error', 'io-error'),
        ('isACamelCasedWORD', 'is-a-camel-cased-word'),
        ('ATitledWordToTESTWith', 'a-titled-word-to-test-with'),
        ('not-a-tester', 'not-a-tester'),
        ('helloworld', 'helloworld'),
        ('A', 'a'),
        ('TESTing_if_thisWorks', 'tes-ting-if-this-works'),
        ('a_B_Cde_fG_hi', 'a-b-cde-f-g-hi'),
        ('ALL_CAPS', 'all-caps'),
        ('WoRd', 'wo-rd'),
        ('HIThereHOWIsItGoinG', 'hi-there-how-is-it-goin-g'),
        ('How_-Are-_YoUDoing__TeST', 'how-are-yo-u-doing-te-st'),
        ('thisIsWithANumber42ToTEST', 'this-is-with-a-number42-to-test'),
        ('Number 42 With spaces', 'number-42-with-spaces')
    ]
)
def test_to_lisp_case(string, expected):
    actual = to_lisp_case(string)
    assert actual == expected


@pytest.mark.parametrize(
    'string,expected',
    [
        ('device_type', 'device_type'),
        ('IO_Error', 'io_error'),
        ('isACamelCasedWORD', 'is_a_camel_cased_word'),
        ('ATitledWordToTESTWith', 'a_titled_word_to_test_with'),
        ('not-a-tester', 'not_a_tester'),
        ('helloworld', 'helloworld'),
        ('A', 'a'),
        ('TESTing_if_thisWorks', 'tes_ting_if_this_works'),
        ('a_B_Cde_fG_hi', 'a_b_cde_f_g_hi'),
        ('ALL_CAPS', 'all_caps'),
        ('WoRd', 'wo_rd'),
        ('HIThereHOWIsItGoinG', 'hi_there_how_is_it_goin_g'),
        ('How_-Are-_YoUDoing__TeST', 'how_are_yo_u_doing_te_st'),
        ('thisIsWithANumber42ToTEST', 'this_is_with_a_number42_to_test'),
        ('Number 42 With spaces', 'number_42_with_spaces')
    ]
)
def test_to_snake_case(string, expected):
    actual = to_snake_case(string)
    assert actual == expected
