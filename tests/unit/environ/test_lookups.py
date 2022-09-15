import pytest

from dataclass_wizard.environ.lookups import *


@pytest.mark.parametrize(
    'string,expected',
    [
        ('device_type', 'devicetype'),
        ('isACamelCasedWORD', 'isacamelcasedword'),
        ('ATitledWordToTESTWith', 'atitledwordtotestwith'),
        ('not-a-tester', 'notatester'),
        ('helloworld', 'helloworld'),
        ('A', 'a'),
        ('TESTing_if_thisWorks', 'testingifthisworks'),
        ('a_B_Cde_fG_hi', 'abcdefghi'),
        ('How_-Are-_YoUDoing__TeST', 'howareyoudoingtest'),
    ]
)
def test_clean(string, expected):
    assert clean(string) == expected


def test_lookup_exact():
    assert lookup_exact('abc-this-key-shouldnt-exist') is MISSING
    assert lookup_exact(('abc-this-key-shouldnt-exist', )) is MISSING


def test_reload_when_not_accessed_cleaned_to_env():
    # save current value
    current_val = Env._accessed_cleaned_to_env

    Env._accessed_cleaned_to_env = False
    Env.reload()

    # don't forget to reset it
    Env._accessed_cleaned_to_env = current_val


def test_with_snake_case():
    var = 'my_test_string_1'
    assert with_snake_case(var) is MISSING

    os.environ['MY_TEST_STRING_1'] = 'hello world'
    Env.reload()
    assert with_snake_case(var) == 'hello world'

    os.environ[var] = 'testing 123'
    Env.reload()
    assert with_snake_case(var) == 'testing 123'


def test_with_pascal_or_camel_case():
    var = 'MyTestString2'
    assert with_pascal_or_camel_case(var) is MISSING

    os.environ['my_test_string2'] = 'testing 123'
    Env.reload()
    assert with_pascal_or_camel_case(var) == 'testing 123'

    os.environ['MY_TEST_STRING2'] = 'hello world'
    Env.reload()
    assert with_pascal_or_camel_case(var) == 'hello world'

    if os.name == 'nt':
        # Windows: var names are automatically converted
        # to upper case when saved to `os.environ`
        return

    os.environ[var] = 'hello world !!'
    Env.reload()
    assert with_pascal_or_camel_case(var) == 'hello world !!'
