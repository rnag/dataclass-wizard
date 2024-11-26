import os
from dataclasses import MISSING
from os import environ, name

from ..decorators import cached_class_property
from ..lazy_imports import dotenv
from ..utils.string_conv import to_snake_case


# Type of `os.environ` or `DotEnv` dict
Environ = dict[str, 'str | None']


# noinspection PyMethodParameters
class Env:

    __slots__ = ()

    _accessed_cleaned_to_env = False

    @cached_class_property
    def var_names(cls):
        """
        Cached mapping of `os.environ` key names. This can be refreshed with
        :meth:`reload` as needed.
        """
        return set(environ)

    @classmethod
    def reload(cls, env=environ):

        env_vars = cls.var_names
        new_vars = set(env) - env_vars

        # update names of environment variables
        env_vars.update(new_vars)

        # update mapping of cleaned environment variables (if needed)
        if cls._accessed_cleaned_to_env:
            cls.cleaned_to_env.update(
                (clean(var), var) for var in new_vars
            )

    @classmethod
    def dotenv_values(cls, files):

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
        # update `os.environ` with new environment variables
        environ.update(dotenv_values)

    # noinspection PyDunderSlots,PyUnresolvedReferences,PyClassVar
    @cached_class_property
    def cleaned_to_env(cls):
        cls._accessed_cleaned_to_env = True
        return {clean(var): var for var in cls.var_names}


def clean(s):

    return s.replace('-', '').replace('_', '').lower()


def try_cleaned(key):

    key = Env.cleaned_to_env.get(clean(key))

    if key is not None:
        return environ[key]

    return MISSING


if name == 'nt':
    # Where Env Var Names Must Be UPPERCASE
    def lookup_exact(var):

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

        if isinstance(var, str):
            if var in Env.var_names:
                return environ[var]

        else:  # a collection of env variable names.
            for v in var:
                if v in Env.var_names:
                    return environ[v]

        return MISSING


def with_screaming_snake_case(field_name):

    upper_key = field_name.upper()

    if upper_key in Env.var_names:
        return environ[upper_key]

    if field_name in Env.var_names:
        return environ[field_name]

    return try_cleaned(field_name)


def with_snake_case(field_name):

    if field_name in Env.var_names:
        return environ[field_name]

    upper_key = field_name.upper()

    if upper_key in Env.var_names:
        return environ[upper_key]

    return try_cleaned(field_name)


def with_pascal_or_camel_case(field_name):

    if field_name in Env.var_names:
        return environ[field_name]

    snake_key = to_snake_case(field_name)
    upper_key = snake_key.upper()

    if upper_key in Env.var_names:
        return environ[upper_key]

    if snake_key in Env.var_names:
        return environ[snake_key]

    return try_cleaned(field_name)
