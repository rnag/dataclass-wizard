"""Environment-name fallback preserves digit boundaries and lookup priority."""
import os

import pytest

from dataclass_wizard import Env, EnvWizard
from dataclass_wizard.errors import MissingVars
from dataclass_wizard.enums import EnvKeyStrategy
from dataclass_wizard.utils._string_conv import possible_env_vars

from ..utils_env import from_env


@pytest.mark.parametrize('name', ['CC_2TEST', 'A2B', '_2TEST', 'A12B3C'])
def test_uppercase_numeric_name_fallback(name):
    """Names with one or more digit boundaries load without an alias."""
    cls = type('Settings', (EnvWizard,), {'__annotations__': {name: str}})
    assert getattr(from_env(cls, {name: 'loaded'}), name) == 'loaded'


@pytest.mark.parametrize('values, expected', [
    ({'CC_2TEST': 'original'}, 'original'),
    ({'CC_2TEST': 'original', 'cc_2_test': 'snake'}, 'snake'),
    ({'CC_2TEST': 'original', 'cc_2_test': 'snake', 'CC_2_TEST': 'upper'},
     'upper'),
    ({'CC_2TEST': 'original', 'cc_2_test': ''}, ''),
    ({'CC_2TEST': 'original', 'cc_2_test': 'snake', 'CC_2_TEST': ''}, ''),
    ({'CC_2TEST': 'original', 'cc_2_test': '', 'CC_2_TEST': ''}, ''),
])
def test_uppercase_numeric_name_precedence(values, expected):
    """Both existing normalized candidates take priority over the fallback."""
    class Settings(EnvWizard):
        """A field whose original spelling differs from its normalized name."""
        CC_2TEST: str

    assert from_env(Settings, values).CC_2TEST == expected


@pytest.mark.parametrize('source', ['environment', 'dotenv'])
def test_uppercase_numeric_name_inherited(source, monkeypatch, tmp_path):
    """The reported inherited configuration works with env and dotenv input."""
    values = {'ABC': 'base', 'CC_TEST': 'plain', 'CC_2TEST': 'numeric'}
    environment = values.copy() if source == 'environment' else {}
    monkeypatch.setattr(os, 'environ', environment)
    dotenv = tmp_path / '.env'
    contents = '\n'.join(f'{key}={value}' for key, value in values.items())
    dotenv.write_text(contents, encoding='utf-8')

    class Base(EnvWizard):
        """Required inherited field from the issue's example."""
        ABC: str

    class Settings(Base):
        """Compare a plain name and a numeric name using the same source."""
        class _(EnvWizard.Meta):
            env_file = str(dotenv) if source == 'dotenv' else False

        CC_TEST: str = 'default'
        CC_2TEST: str = 'default'

    settings = Settings()
    assert settings.ABC == 'base'
    assert settings.CC_TEST == 'plain'
    assert settings.CC_2TEST == 'numeric'


def test_uppercase_numeric_name_prefix_and_alias():
    """Prefixes apply to the fallback, while an explicit alias still wins."""
    class Settings(EnvWizard):
        """A prefixed configuration with an unprefixed explicit alias."""
        class _(EnvWizard.Meta):
            env_prefix = 'APP_'

        CC_2TEST: str = Env('EXPLICIT')

    values = {'APP_CC_2TEST': 'original'}
    assert from_env(Settings, values).CC_2TEST == 'original'
    values['EXPLICIT'] = 'alias'
    assert from_env(Settings, values).CC_2TEST == 'alias'


def test_uppercase_numeric_name_missing():
    """Missing input retains required-field errors and optional defaults."""
    class Required(EnvWizard):
        """A required field with a numeric name."""
        CC_2TEST: str

    class Optional(EnvWizard):
        """A defaulted field with a numeric name."""
        CC_2TEST: str = 'default'

    with pytest.raises(MissingVars):
        from_env(Required, {})
    assert from_env(Optional, {}).CC_2TEST == 'default'


@pytest.mark.parametrize('strategy, expected', [
    ('FIELD_FIRST', 'original'), ('STRICT', 'default'),
])
def test_uppercase_numeric_name_other_strategies(strategy, expected):
    """FIELD_FIRST and STRICT retain their different lookup contracts."""
    class Settings(EnvWizard):
        """A numeric name using a non-default strategy."""
        class _(EnvWizard.Meta):
            load_case = strategy

        CC_2TEST: str = 'default'

    values = {'CC_2TEST': 'original', 'CC_2_TEST': 'upper'}
    assert from_env(Settings, values).CC_2TEST == expected


@pytest.mark.parametrize('name, expected', [
    ('CC_2TEST', ['CC_2_TEST', 'cc_2_test', 'CC_2TEST']),
    ('CC_TEST2', ['CC_TEST2', 'cc_test2']),
    ('CC_TEST', ['CC_TEST', 'cc_test']),
    ('cc_2test', ['CC_2TEST', 'cc_2test']),
    ('cc2Test', ['CC2_TEST', 'cc2_test']),
    ('CC__2TEST', ['CC_2_TEST', 'cc_2_test']),
    ('CC-2TEST', ['CC_2_TEST', 'cc_2_test']),
])
def test_uppercase_numeric_name_candidates(name, expected):
    """Only digit-induced normalization adds a new, nonduplicate candidate."""
    assert possible_env_vars(name, EnvKeyStrategy.ENV) == expected
