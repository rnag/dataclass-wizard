from dataclass_wizard.v1 import Alias, EnvWizard

from ..utils_env import from_env


def test_dump_with_excluded_fields_and_skip_defaults():

    class TestClass(EnvWizard):
        class _(EnvWizard.Meta):
            v1 = True

        my_first_str: str
        my_second_str: str = Alias(skip=True)
        my_int: int = 123

    env = {'MY_FIRST_STR': 'hello',
           'my_second_str': 'world'}

    # alternatively -- although not ideal for unit test:
    # os.environ['MY_FIRST_STR'] = 'hello'
    # os.environ['my_second_str'] = 'world'

    assert from_env(TestClass, env).to_dict(
        exclude=['my_first_str'],
        skip_defaults=True,
    ) == {}
