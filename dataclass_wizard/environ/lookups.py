import os
from dataclasses import MISSING
from pathlib import Path

from ..decorators import cached_class_property
from ..lazy_imports import dotenv
from ..utils.string_conv import to_snake_case


# Type of `os.environ` or `DotEnv` dict
Environ = dict[str, 'str | None']

# noinspection PyTypeChecker
environ = None


# noinspection PyMethodParameters
class Env:

    __slots__ = ()

    _accessed_cleaned_to_env = False

    @classmethod
    def load_environ(cls, force_reload=False):
        """
        Load :attr:`environ` from ``os.environ``.

        If `force_reload` is true, start fresh
        and re-copy `os.environ`.
        """
        global environ

        if (_env_not_setup := environ is None) or force_reload:
            # Copy `os.environ`, so as not to mutate it
            environ = os.environ.copy()

            if not _env_not_setup:
                # Refresh `var_names`, in case env variables
                # were removed (deleted) from `os.environ`
                cls.var_names = set(environ)

                if cls._accessed_cleaned_to_env:
                    cls.cleaned_to_env = {
                        k: v for k, v in cls.cleaned_to_env.items()
                        if v in cls.var_names
                    }

    @cached_class_property
    def var_names(cls):
        """
        Cached mapping of `os.environ` key names. This can be refreshed with
        :meth:`reload` as needed.
        """
        return set(environ) if environ is not None else set()

    @classmethod
    def reload(cls, env=None):
        """Refresh cached environment variable names."""
        env_vars = cls.var_names

        if env is None:
            cls.load_environ(force_reload=True)
            env = environ

        new_vars = set(env) - env_vars

        # update names of environment variables
        env_vars.update(new_vars)

        # update mapping of cleaned environment variables (if needed)
        if cls._accessed_cleaned_to_env:
            cls.cleaned_to_env.update(
                (clean(var), var) for var in new_vars
            )

    @classmethod
    def secret_values(cls, dirs):
        """
        Retrieve the values (environment variables) from secret file(s)
        in a secret directory, or a list/tuple of secret directories.
        """
        if isinstance(dirs, (str, os.PathLike)):
            dirs = [dirs]

        env: Environ = {}

        for d in dirs:
            d: Path = d if isinstance(dirs, os.PathLike) else Path(d)

            if d.exists():
                if d.is_dir():
                    # Iterate over all files in the directory
                    for f in d.iterdir():
                        if f.is_file():  # Ensure it's a file, not a subdirectory
                            env[f.name] = f.read_text()
                elif d.is_file():
                    raise ValueError(f'Secrets directory `{d!r}` is a file, not a directory.')

        return env

    @classmethod
    def update_with_secret_values(cls, dirs):

        secret_values = cls.secret_values(dirs)

        # reload cached mapping of environment variables
        cls.reload(secret_values)
        # update `environ` with new environment variables
        environ.update(secret_values)

    @classmethod
    def dotenv_values(cls, files):
        """
        Retrieve the values (environment variables) from a dotenv file,
        or a list/tuple of dotenv files.
        """
        if isinstance(files, (str, os.PathLike)):
            files = [files]
        elif files is True:
            files = ['.env']

        env: Environ = {}

        for f in files:
            # iterate backwards (from current directory) to find the
            # dotenv file
            dotenv_path = dotenv.find_dotenv(f)
            # take environment variables from `.env` file
            dotenv_values = dotenv.dotenv_values(dotenv_path)
            env.update(dotenv_values)

        return env

    @classmethod
    def update_with_dotenv(cls, files='.env', dotenv_values=None):

        if dotenv_values is None:
            dotenv_values = cls.dotenv_values(files)

        # reload cached mapping of environment variables
        cls.reload(dotenv_values)
        # update `environ` with new environment variables
        environ.update(dotenv_values)

    # noinspection PyDunderSlots,PyUnresolvedReferences,PyClassVar
    @cached_class_property
    def cleaned_to_env(cls):
        cls._accessed_cleaned_to_env = True
        return {clean(var): var for var in cls.var_names}


def clean(s):
    """
    TODO:
        see https://stackoverflow.com/questions/1276764/stripping-everything-but-alphanumeric-chars-from-a-string-in-python
        also, see if we can refactor to use something like Rust and `pyo3` for a slight performance improvement.
    """
    return s.replace('-', '').replace('_', '').lower()


def try_cleaned(key):
    """
    Return the value of the env variable as a *string* if present in
    the Environment, or `MISSING` otherwise.
    """
    key = Env.cleaned_to_env.get(clean(key))

    if key is not None:
        return environ[key]

    return MISSING


if os.name == 'nt':
    # Where Env Var Names Must Be UPPERCASE
    def lookup_exact(var):
        """
        Lookup by variable name(s) with *exact* letter casing, and return
        `None` if not found in the environment.
        """
        if isinstance(var, str):
            var = var.upper()

            if var in Env.var_names:
                return environ[var]

        else:  # a collection of env variable names.
            for v in var:
                v = v.upper()

                if v in Env.var_names:
                    return environ[v]

        return MISSING

else:
    # Where Env Var Names Can Be Mixed Case
    def lookup_exact(var):
        """
        Lookup by variable name(s) with *exact* letter casing, and return
        `None` if not found in the environment.
        """
        if isinstance(var, str):
            if var in Env.var_names:
                return environ[var]

        else:  # a collection of env variable names.
            for v in var:
                if v in Env.var_names:
                    return environ[v]

        return MISSING


def with_screaming_snake_case(field_name):
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
    upper_key = field_name.upper()

    if upper_key in Env.var_names:
        return environ[upper_key]

    if field_name in Env.var_names:
        return environ[field_name]

    return try_cleaned(field_name)


def with_snake_case(field_name):
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
    if field_name in Env.var_names:
        return environ[field_name]

    upper_key = field_name.upper()

    if upper_key in Env.var_names:
        return environ[upper_key]

    return try_cleaned(field_name)


def with_pascal_or_camel_case(field_name):
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
    if field_name in Env.var_names:
        return environ[field_name]

    snake_key = to_snake_case(field_name)
    upper_key = snake_key.upper()

    if upper_key in Env.var_names:
        return environ[upper_key]

    if snake_key in Env.var_names:
        return environ[snake_key]

    return try_cleaned(field_name)
