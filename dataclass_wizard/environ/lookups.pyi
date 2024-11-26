from dataclasses import MISSING
from os import environ
from typing import ClassVar

from ..decorators import cached_class_property
from ..type_def import StrCollection, EnvFileType


type _MISSING_TYPE = type(MISSING)
type STR_OR_MISSING = str | _MISSING_TYPE
type STR_OR_NONE = str | None

# Type of `os.environ` or `DotEnv` dict
Environ = dict[str, STR_OR_NONE]

# Type of (unique) environment variable names
EnvVars = set[str]


# noinspection PyMethodParameters
class Env:

    __slots__ = ()

    _accessed_cleaned_to_env: ClassVar[bool] = False

    """
    Cached mapping of `os.environ` key names. This can be refreshed with
    :meth:`reload` as needed.
    """
    var_names: EnvVars

    @classmethod
    def reload(cls, env: dict = environ):
        """Refresh cached environment variable names."""

    @classmethod
    def dotenv_values(cls, files: EnvFileType) -> Environ:
        """
        Retrieve the values (environment variables) from a dotenv file,
        or a list/tuple of dotenv files.
        """

    @classmethod
    def update_with_dotenv(cls, files: EnvFileType = '.env', dotenv_values=None):
        ...

    # noinspection PyDunderSlots,PyUnresolvedReferences
    @cached_class_property
    def cleaned_to_env(cls) -> Environ:
        ...


def clean(s: str) -> str:
    """
    TODO:
        see https://stackoverflow.com/questions/1276764/stripping-everything-but-alphanumeric-chars-from-a-string-in-python
        also, see if we can refactor to use something like Rust and `pyo3` for a slight performance improvement.
    """


def try_cleaned(key: str) -> STR_OR_MISSING:
    """
    Return the value of the env variable as a *string* if present in
    the Environment, or `MISSING` otherwise.
    """


def lookup_exact(var: StrCollection) -> STR_OR_MISSING:
    """
    Lookup by variable name(s) with *exact* letter casing, and return
    `None` if not found in the environment.
    """


def with_screaming_snake_case(field_name: str) -> STR_OR_MISSING:
    """
    Lookup with `SCREAMING_SNAKE_CASE` letter casing first - this is the
    default lookup.

    This function assumes the dataclass field name is lower-cased.

    For a field named 'my_env_var', this tries the following lookups in order:
        - MY_ENV_VAR (screaming snake-case)
        - my_env_var (snake-case)
        - Any other variations - i.e. MyEnvVar, myEnvVar, myenvvar, my-env-var

    :param field_name: The dataclass field name to lookup in the environment.
    :return: The value of the matched environment variable, if one is found in
      the environment.
    """


def with_snake_case(field_name: str) -> STR_OR_MISSING:
    """Lookup with `snake_case` letter casing first.

    This function assumes the dataclass field name is lower-cased.

    For a field named 'my_env_var', this tries the following lookups in order:
        - my_env_var (snake-case)
        - MY_ENV_VAR (screaming snake-case)
        - Any other variations - i.e. MyEnvVar, myEnvVar, myenvvar, my-env-var

    :param field_name: The dataclass field name to lookup in the environment.
    :return: The value of the matched environment variable, if one is found in
      the environment.
    """


def with_pascal_or_camel_case(field_name: str) -> STR_OR_MISSING:
    """Lookup with `PascalCase` or `camelCase` letter casing first.

    This function assumes the dataclass field name is either pascal- or camel-
    cased.

    For a field named 'myEnvVar', this tries the following lookups in order:
        - myEnvVar, MyEnvVar (camel-case, or pascal-case)
        - MY_ENV_VAR (screaming snake-case)
        - my_env_var (snake-case)
        - Any other variations - i.e. my-env-var, myenvvar

    :param field_name: The dataclass field name to lookup in the environment.
    :return: The value of the matched environment variable, if one is found in
      the environment.
    """
