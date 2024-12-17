import json
import logging
from dataclasses import MISSING, dataclass, fields
from typing import Callable

from .dumpers import asdict
from .lookups import Env, lookup_exact, clean
from ..abstractions import AbstractEnvWizard
from ..bases import AbstractEnvMeta
from ..bases_meta import BaseEnvWizardMeta, EnvMeta
from ..class_helper import (call_meta_initializer_if_needed, get_meta,
                            field_to_env_var, dataclass_field_to_json_field)
from ..decorators import cached_class_property
from ..enums import LetterCase
from ..environ.loaders import EnvLoader
from ..errors import ExtraData, MissingVars, ParseError, type_name
from ..loader_selection import get_loader
from ..models import Extras, JSONField
from ..type_def import ExplicitNull, JSONObject, dataclass_transform
from ..utils.function_builder import FunctionBuilder


_to_dataclass = dataclass(init=False)


@dataclass_transform(kw_only_default=True)
class EnvWizard(AbstractEnvWizard):
    """
    *Environment Wizard*

    A mixin class for parsing and managing environment variables in Python.

    ``EnvWizard`` makes it easy to map environment variables to Python attributes,
    handle defaults, and optionally load values from `.env` files.

    Quick Example::

        import os
        from pathlib import Path

        class MyConfig(EnvWizard):
            my_var: str
            my_optional_var: int = 42

        # Set environment variables
        os.environ["MY_VAR"] = "hello"

        # Load configuration from the environment
        config = MyConfig()
        print(config.my_var)  # Output: "hello"
        print(config.my_optional_var)  # Output: 42

        # Specify configuration explicitly
        config = MyConfig(my_var='world')
        print(config.my_var)  # Output: "world"
        print(config.my_optional_var)  # Output: 42

    Example with ``.env`` file::

        class MyConfigWithEnvFile(EnvWizard):
            class _(EnvWizard.Meta):
                env_file = True  # Defaults to loading from `.env`

            my_var: str
            my_optional_var: int = 42

        # Create an `.env` file in the current directory:
        # MY_VAR=world
        config = MyConfigWithEnvFile()
        print(config.my_var)  # Output: "world"
        print(config.my_optional_var)  # Output: 42

    Key Features:
        - Automatically maps environment variables to dataclass fields.
        - Supports default values for fields if environment variables are not set.
        - Optionally loads environment variables from `.env` files.
        - Supports prefixes for environment variables using ``_env_prefix`` or ``Meta.env_prefix``.
        - Supports loading secrets from directories using ``_secrets_dir`` or ``Meta.secrets_dir``.
        - Dynamic reloading with ``_reload`` to handle updated environment values.

    Initialization Options:
        The ``__init__`` method accepts additional parameters for flexibility:

        - ``_env_file`` (optional):
            Overrides the ``Meta.env_file`` value dynamically. Can be a file path,
            a sequence of file paths, or ``True`` to use the default `.env` file.
        - ``_reload`` (optional):
            Forces a reload of environment variables to bypass caching. Defaults to ``False``.
        - ``_env_prefix`` (optional):
            Dynamically overrides ``Meta.env_prefix``, applying a prefix to all environment
            variables. Defaults to ``None``.
        - ``_secrets_dir`` (optional):
            Overrides the ``Meta.secrets_dir`` value dynamically. Can be a directory path
            or a sequence of paths pointing to directories containing secret files.

    Meta Settings:
        These class-level attributes can be configured in a nested ``Meta`` class:

        - ``env_file``:
            The path(s) to `.env` files to load. If set to ``True``, defaults to `.env`.
        - ``env_prefix``:
            A prefix applied to all environment variables. Defaults to ``None``.
        - ``secrets_dir``:
            A path or sequence of paths to directories containing secret files. Defaults to ``None``.

    Attributes:
        Defined dynamically based on the dataclass fields in the derived class.
    """
    __slots__ = ()

    class Meta(BaseEnvWizardMeta):
        """
        Inner meta class that can be extended by sub-classes for additional
        customization with the environment load process.
        """
        __slots__ = ()

        # Class attribute to enable detection of the class type.
        __is_inner_meta__ = True

        def __init_subclass__(cls):
            # Set the `__init_subclass__` method here, so we can ensure it
            # doesn't run for the `EnvWizard.Meta` class.
            return cls._init_subclass()

    # noinspection PyMethodParameters,PyUnresolvedReferences
    @cached_class_property
    def __fields__(cls: type['E']):
        cls_fields = {}
        field_to_var = field_to_env_var(cls)

        for field in fields(cls):
            name = field.name
            cls_fields[name] = field

            if isinstance(field, JSONField):
                if not field.json.dump:
                    field_to_json_key = dataclass_field_to_json_field(cls)
                    field_to_json_key[name] = ExplicitNull

                keys = field.json.keys
                if keys:
                    # minor optimization: convert a one-element tuple of `str` to `str`
                    field_to_var[name] = keys[0] if len(keys) == 1 else keys

        return cls_fields

    to_dict = asdict

    def to_json(self, *,
                encoder = json.dumps,
                **encoder_kwargs):
        """
        Converts the `EnvWizard` subclass to a JSON `string` representation.
        """
        return encoder(asdict(self), **encoder_kwargs)

    def __init_subclass__(cls, *, reload_env=False, debug=False,
                          key_transform=LetterCase.NONE):

        if reload_env:  # reload cached var names from `os.environ` as needed.
            Env.reload()

        # apply the `@dataclass(init=False)` decorator to `cls`.
        _to_dataclass(cls)

        # set `key_transform_with_dump` for the class's Meta
        meta = EnvMeta(key_transform_with_dump=key_transform)

        if debug:
            default_lvl = logging.DEBUG
            logging.basicConfig(level=default_lvl)
            # minimum logging level for logs by this library
            min_level = default_lvl if isinstance(debug, bool) else debug
            # set `debug_enabled` flag for the class's Meta
            meta.debug_enabled = min_level

        # Bind child class to DumpMeta with no key transformation.
        meta.bind_to(cls)

        # Calls the Meta initializer when inner :class:`Meta` is sub-classed.
        call_meta_initializer_if_needed(cls)

        # create and set methods such as `__init__()`.
        cls._create_methods()

    @classmethod
    def _create_methods(cls):
        """
        Generates methods such as the ``__init__()`` constructor method
        and ``dict()`` for the :class:`EnvWizard` subclass, vis-à-vis
        how the ``dataclasses`` module does it, with a few noticeable
        differences.
        """
        meta = get_meta(cls, base_cls=AbstractEnvMeta)
        cls_loader = get_loader(cls, base_cls=EnvLoader)

        # A cached mapping of each dataclass field name to its environment
        # variable name; useful so we don't need to do a case transformation
        # (via regex) each time.
        field_to_var = field_to_env_var(cls)

        # The function to case-transform and lookup variables defined in the
        # environment.
        get_env: 'Callable[[str], str | None]' = meta.key_lookup_with_load

        # noinspection PyArgumentList
        extras = Extras(config=None)

        cls_fields = cls.__fields__
        field_names = frozenset(cls_fields)

        _meta_env_file = meta.env_file

        _locals = {'Env': Env,
                   'ParseError': ParseError,
                   'field_names': field_names,
                   'get_env': get_env,
                   'lookup_exact': lookup_exact}

        _globals = {'MissingVars': MissingVars,
                    'add': _add_missing_var,
                    'cls': cls,
                    'fields_ordered': cls_fields.keys(),
                    'handle_err': _handle_parse_error,
                    'MISSING': MISSING,
                    }

        if meta.secrets_dir is None:
            _secrets_dir_value = 'None'
        else:
            _locals['_secrets_dir_value'] = meta.secrets_dir
            _secrets_dir_value = '_secrets_dir_value'

        # parameters to the `__init__()` method.
        init_params = ['self',
                       '_env_file=None',
                       '_reload=False',
                       f'_env_prefix={meta.env_prefix!r}',
                       f'_secrets_dir={_secrets_dir_value}',
        ]

        fn_gen = FunctionBuilder()

        with fn_gen.function('__init__', init_params, None, _locals):

            # reload cached var names from `os.environ` as needed.
            with fn_gen.if_('_reload'):
                fn_gen.add_line('Env.reload()')
            with fn_gen.else_():
                fn_gen.add_line('Env.load_environ()')

            with fn_gen.if_('_secrets_dir'):
                fn_gen.add_line('Env.update_with_secret_values(_secrets_dir)')

            # update environment with values in the "dot env" files as needed.
            if _meta_env_file:
                fn = fn_gen.elif_
                _globals['_dotenv_values'] = Env.dotenv_values(_meta_env_file)
                with fn_gen.if_('_env_file is None'):
                    fn_gen.add_line('Env.update_with_dotenv(dotenv_values=_dotenv_values)')
            else:
                fn = fn_gen.if_
            with fn('_env_file'):
                fn_gen.add_line('Env.update_with_dotenv(_env_file)')

            # iterate over the dataclass fields and (attempt to) resolve
            # each one.
            fn_gen.add_line('_vars = []')

            if field_names:

                with fn_gen.try_():

                    for name, f in cls_fields.items():
                        type_field = f'_tp_{name}'
                        tp = _globals[type_field] = f.type

                        init_params.append(f'{name}:{type_field}=MISSING')

                        # retrieve value (if it exists) for the environment variable

                        env_var = var_name = field_to_var.get(name)
                        if env_var:
                            part = f'({name} := lookup_exact(_var_name))'
                        else:
                            var_name = name
                            part = f'({name} := get_env(_var_name))'

                        fn_gen.add_line(f'_name={name!r}; _env_var={env_var!r}; _var_name=f"{{_env_prefix}}{var_name}" if _env_prefix else {var_name!r}')

                        with fn_gen.if_(f'{name} is not MISSING or {part} is not MISSING'):
                            parser_name = f'_parser_{name}'
                            _globals[parser_name] = getattr(p := cls_loader.get_parser_for_annotation(
                                tp, cls, extras), '__call__', p)
                            fn_gen.add_line(f'self.{name} = {parser_name}({name})')
                        # this `else` block means that a value was not received for the
                        # field, either via keyword arguments or Environment.
                        with fn_gen.else_():
                            # check if the field defines a `default` or `default_factory`
                            # value; note this is similar to how `dataclasses` does it.
                            default_name = f'_dflt_{name}'
                            if f.default is not MISSING:
                                _globals[default_name] = f.default
                                fn_gen.add_line(f'self.{name} = {default_name}')
                            elif f.default_factory is not MISSING:
                                _globals[default_name] = f.default_factory
                                fn_gen.add_line(f'self.{name} = {default_name}()')
                            else:
                                fn_gen.add_line(f'add(_vars, _name, _env_prefix, _env_var, {type_field})')

                with fn_gen.except_(ParseError, 'e'):
                    fn_gen.add_line('handle_err(e, cls, _name, _env_prefix, _env_var)')

            # check for any required fields with missing values
            with fn_gen.if_('_vars'):
                fn_gen.add_line('raise MissingVars(cls, _vars) from None')

            # if keyword arguments are passed in, confirm that all there
            # aren't any "extra" keyword arguments
            # if _extra is not Extra.IGNORE:
                # with fn_gen.if_('has_kwargs'):
                #     # get a list of keyword arguments that don't map to any fields
                #     fn_gen.add_line('extra_kwargs = set(init_kwargs) - field_names')
                #     with fn_gen.if_('extra_kwargs'):
                #         # the default behavior is "DENY", so an error will be raised here.
                #         if _extra is None or _extra is Extra.DENY:
                #             _globals['ExtraData'] = ExtraData
                #             fn_gen.add_line('raise ExtraData(cls, extra_kwargs, list(fields_ordered)) from None')
                #         else:  # Extra.ALLOW
                #             # else, if we want to "ALLOW" extra keyword arguments, we need to
                #             # store those attributes in the instance.
                #             with fn_gen.for_('attr in extra_kwargs'):
                #                 fn_gen.add_line('setattr(self, attr, init_kwargs[attr])')

        with fn_gen.function('dict', ['self'], JSONObject, _locals):
            parts = ','.join([f'{name!r}:self.{name}' for name, f in cls.__fields__.items()])
            fn_gen.add_line(f'return {{{parts}}}')

        functions = fn_gen.create_functions(_globals)

        # set the `__init__()` method.
        cls.__init__ = functions['__init__']
        # set the `dict()` method.
        cls.dict = functions['dict']


def _add_missing_var(missing_vars, name, env_prefix, var_name, tp):

    var_name = _get_var_name(name, env_prefix, var_name)
    tn = type_name(tp)
    # noinspection PyBroadException
    try:
        suggested = tp()
    except Exception:
        suggested = None

    missing_vars.append((name, var_name, tn, suggested))


def _handle_parse_error(e, cls, name, env_prefix, var_name):

    # We run into a parsing error while loading the field
    # value; Add additional info on the Exception object
    # before re-raising it.
    e.class_name = cls
    e.field_name = name
    e.kwargs['env_variable'] = _get_var_name(name, env_prefix, var_name)

    raise


def _get_var_name(name, env_prefix, var_name):

    if var_name is None:
        env_var = f'{env_prefix}{name}' if env_prefix else name
        var_name = Env.cleaned_to_env.get(clean(env_var), env_var)

    elif env_prefix:
        var_name = f'{env_prefix}{var_name}'

    return var_name
