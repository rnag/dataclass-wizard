import os

from dataclass_wizard import EnvWizard, json_field


def test_dump_with_excluded_fields_and_skip_defaults():

    os.environ['MY_FIRST_STR'] = 'hello'
    os.environ['my-second-str'] = 'world'

    class TestClass(EnvWizard, reload_env=True):
        my_first_str: str
        my_second_str: str = json_field(..., dump=False)
        my_int: int = 123

    assert TestClass(_reload=True).to_dict(
        exclude=['my_first_str'],
        skip_defaults=True,
    ) == {}
