from __future__ import annotations

import dataclasses
import json
import logging
import os
from base64 import b64decode
from collections import ChainMap
from dataclasses import dataclass, is_dataclass, Field, MISSING
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import (Any, Callable, NamedTuple, cast, Mapping,
                    dataclass_transform, TYPE_CHECKING)
from uuid import UUID

from .decorators import (process_patterned_date_time,
                         setup_recursive_safe_function,
                         setup_recursive_safe_function_for_generic)
from .enums import EnvKeyStrategy, EnvPrecedence
from .loaders import LoadMixin as V1LoaderMixIn
from .models import Extras, TypeInfo, SIMPLE_TYPES
from .path_util import get_secrets_map, get_dotenv_map
from .type_conv import (
    as_datetime_v1, as_date_v1, as_int_v1,
    as_time_v1, as_timedelta, TRUTHY_VALUES,
)
from ..bases import AbstractMeta, META, AbstractEnvMeta, ENV_META
from ..bases_meta import BaseEnvWizardMeta, EnvMeta, register_type
from ..class_helper import (create_meta,
                            dataclass_fields,
                            dataclass_field_to_default,
                            dataclass_init_fields,
                            dataclass_init_field_names,
                            get_meta,
                            is_subclass_safe,
                            v1_dataclass_field_to_env_for_load,
                            CLASS_TO_LOAD_FUNC,
                            DATACLASS_FIELD_TO_ALIAS_PATH_FOR_LOAD,
                            call_meta_initializer_if_needed,
                            dataclass_field_names)
from ..constants import CATCH_ALL, TAG, PY311_OR_ABOVE, PACKAGE_NAME
from ..decorators import cached_class_property
from ..errors import (JSONWizardError,
                      MissingData,
                      MissingFields,
                      ParseError,
                      UnknownKeysError, type_name, MissingVars)
from ..loader_selection import get_loader, asdict
from ..log import LOG
from ..type_def import DefFactory, NoneType, T, JSONObject
# noinspection PyProtectedMember
from ..utils.dataclass_compat import _set_new_attribute
from ..utils.function_builder import FunctionBuilder
from ..utils.object_path import v1_safe_get
from ..utils.string_conv import possible_env_vars
from ..utils.typing_compat import (eval_forward_ref_if_needed,
                                   get_keys_for_typed_dict,
                                   get_origin_v2)

if TYPE_CHECKING:
    from .env import EnvInit, E_


def env_config(**kw):
    return kw


_PRECEDENCE_ORDER: dict[EnvPrecedence, tuple[str, ...]] = {
    EnvPrecedence.SECRETS_ENV_DOTENV: ('secrets', 'env', 'dotenv'),
    EnvPrecedence.SECRETS_DOTENV_ENV: ('secrets', 'dotenv', 'env'),
    EnvPrecedence.ENV_ONLY: ('env', ),
}


@dataclass_transform(kw_only_default=True)
class EnvWizard:
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

    def __init__(self, **kwargs):
        __init_fn__ = load_func_for_dataclass(
            self.__class__,
            loader_cls=LoadMixin,
            base_meta_cls=AbstractEnvMeta,
        )
        __init_fn__(self, **kwargs)

    def __init_subclass__(cls,
                          debug: bool = False,
                          _apply_dataclass=True,
                          **dc_kwargs):
        super().__init_subclass__()

        # skip classes provided by this library.
        if cls.__module__.startswith(f'{PACKAGE_NAME}.'):
            return

        # Apply the @dataclass decorator.
        if _apply_dataclass and not is_dataclass(cls):
            # noinspection PyArgumentList
            dataclass(cls, init=False, **dc_kwargs)

        load_meta_kwargs = {'v1': True}

        if debug:
            default_lvl = logging.DEBUG
            logging.basicConfig(level=default_lvl)
            # minimum logging level for logs by this library
            min_level = default_lvl if isinstance(debug, bool) else debug
            # set `v1_debug` flag for the class's Meta
            load_meta_kwargs['v1_debug'] = min_level

        if load_meta_kwargs:
            EnvMeta(**load_meta_kwargs).bind_to(cls)

        # Calls the Meta initializer when inner :class:`Meta` is sub-classed.
        call_meta_initializer_if_needed(cls)

    _dcw_env_cache_secrets = classmethod(get_secrets_map)
    _dcw_env_cache_dotenv = classmethod(get_dotenv_map)

    __field_names__ = cached_class_property(dataclass_field_names)

    register_type = classmethod(register_type)

    def raw_dict(self: E_) -> JSONObject:
        """
        Same as ``__dict__``, but only returns values for fields defined
        on the `EnvWizard` instance. See :attr:`__field_names__` for more info.

        .. NOTE::
           The values in the returned dictionary object are not needed to be
           JSON serializable. Use :meth:`to_dict` if this is required.
        """

    to_dict = asdict

    def to_json(self, *,
                encoder=json.dumps,
                **encoder_kwargs):

        return encoder(asdict(self), **encoder_kwargs)


def load_func_for_dataclass(
        cls,
        extras: Extras | None = None,
        loader_cls=None,
        base_meta_cls: ENV_META = AbstractEnvMeta,
) -> Callable[[T, dict[str, Any]], None] | None:

    # Tuple describing the fields of this dataclass.
    fields = dataclass_fields(cls)

    cls_init_fields = dataclass_init_fields(cls, True)
    cls_init_field_names = dataclass_init_field_names(cls)

    field_to_default = dataclass_field_to_default(cls)

    has_defaults = True if field_to_default else False

    # Get the loader for the class, or create a new one as needed.
    cls_loader = get_loader(cls, base_cls=loader_cls or LoadMixin, v1=True)

    cls_name = cls.__name__

    fn_name = f'__{PACKAGE_NAME}_init_{cls_name}__'
    raw_dict_name = 'raw_dict'

    # Get the meta config for the class, or the default config otherwise.
    meta = get_meta(cls, base_meta_cls)

    if extras is None:  # we are being run for the main dataclass
        is_main_class = True

        # If the `recursive` flag is enabled and a Meta config is provided,
        # apply the Meta recursively to any nested classes.
        #
        # Else, just use the base `AbstractMeta`.
        config: META = meta if meta.recursive else base_meta_cls

        # Initialize the FuncBuilder
        fn_gen = FunctionBuilder()

        new_locals = {
            'cls': cls,
            'fields': fields,
        }

        # noinspection PyTypeChecker
        extras: Extras = {
            'config': config,
            'cls': cls,
            'cls_name': cls_name,
            'locals': new_locals,
            'recursion_guard': {cls: fn_name},
            'fn_gen': fn_gen,
        }

        _globals = {
            'os': os,
            'ChainMap': ChainMap,
            'MISSING': MISSING,
            'ParseError': ParseError,
            'MissingVars': MissingVars,
            'add': _add_missing_var,
            'raise_missing_fields': check_and_raise_missing_fields,
            're_raise': re_raise,
        }

    # we are being run for a nested dataclass
    else:
        is_main_class = False

        # config for nested dataclasses
        config = extras['config']

        # Initialize the FuncBuilder
        fn_gen = extras['fn_gen']

        if config is not base_meta_cls:
            # we want to apply the meta config from the main dataclass
            # recursively.
            meta = meta | config
            meta.bind_to(cls, is_default=False)

        new_locals = extras['locals']
        new_locals['fields'] = fields

        # TODO need a way to auto-magically do this
        extras['cls'] = cls
        extras['cls_name'] = cls_name

    # default `v1_load_case` to `EnvKeyStrategy.ENV` if not set
    env_key_strat: EnvKeyStrategy | None = meta.v1_load_case or EnvKeyStrategy.ENV
    default_strat = env_key_strat is not EnvKeyStrategy.STRICT
    # default `v1_env_precedence` to SECRETS_ENV_DOTENV if not set
    env_precedence: EnvPrecedence = meta.v1_env_precedence or EnvPrecedence.SECRETS_ENV_DOTENV

    field_to_env_vars = v1_dataclass_field_to_env_for_load(cls)
    check_env_vars = True if field_to_env_vars else False

    field_to_paths = DATACLASS_FIELD_TO_ALIAS_PATH_FOR_LOAD[cls]
    has_alias_paths = True if field_to_paths else False

    # Fix for using `auto_assign_tags` and `raise_on_unknown_json_key` together
    # See https://github.com/rnag/dataclass-wizard/issues/137
    has_tag_assigned = getattr(meta, 'tag', None) is not None
    if (has_tag_assigned and
            # Ensure `tag_key` isn't a dataclass field,
            # to avoid issues with our logic.
            # See https://github.com/rnag/dataclass-wizard/issues/148
            meta.tag_key not in cls_init_field_names):
        expect_tag_as_unknown_key = True
    else:
        expect_tag_as_unknown_key = False

    # on_unknown_key = meta.v1_on_unknown_key

    catch_all_field: str | None = field_to_env_vars.pop(CATCH_ALL, None)
    has_catch_all = catch_all_field is not None

    if has_catch_all:
        pre_assign = 'i+=1; '
        catch_all_field_stripped = catch_all_field.rstrip('?')
        catch_all_idx = cls_init_field_names.index(catch_all_field_stripped)
        # remove catch all field from list, so we don't iterate over it
        del cls_init_fields[catch_all_idx]
    else:
        pre_assign = ''
        catch_all_field_stripped = catch_all_idx = None

    # if on_unknown_key is not None:
    #     should_raise = on_unknown_key is KeyAction.RAISE
    #     should_warn = on_unknown_key is KeyAction.WARN
    #     if should_warn or should_raise:
    #         pre_assign = 'i+=1; '
    #         set_aliases = True
    #     else:
    #         set_aliases = has_catch_all
    # else:
    #     should_raise = should_warn = None
    set_aliases = has_catch_all

    if set_aliases:
        if expect_tag_as_unknown_key:
            # add an alias for the tag key, so we don't
            # capture or raise an error when we see it
            aliases = {meta.tag_key}
        else:
            aliases = set()

        new_locals['aliases'] = aliases
    else:
        aliases = None

    if has_alias_paths:
        new_locals['safe_get'] = v1_safe_get

    _env_defaults: EnvInit = {}
    if _env_file := meta.env_file:
        _env_defaults['file'] = _env_file
    if (_env_prefix := meta.env_prefix) is not None:
        _env_defaults['prefix'] = _env_prefix
    if (_secrets_dir := meta.secrets_dir) is not None:
        _env_defaults['secrets_dir'] = '<configured>'
        LOG.debug(f'Default __env__ = {_env_defaults!r}')
        _env_defaults['secrets_dir'] = _secrets_dir

    new_locals['cfg'] = _env_defaults
    init_params = ['self',
                   '__env__:EnvInit=None',
                   '*']

    with fn_gen.function(fn_name, init_params, MISSING, new_locals):

        with fn_gen.if_('__env__ is not None'):
            fn_gen.add_line('cfg.update(__env__)')

        fn_gen.add_line("reload = cfg.get('reload', False)")
        fn_gen.add_line("env_file = cfg.get('file')")
        fn_gen.add_line("secrets_dir = cfg.get('secrets_dir')")
        fn_gen.add_line("pfx = cfg.get('prefix', '')")
        # Need to create a separate dictionary to copy over the constructor
        # args, as we don't want to mutate the original dictionary object.
        if pre_assign:
            fn_gen.add_line('i = 0')

        env_map_assign = "cfg.get('mapping') or os.environ"
        if env_precedence is EnvPrecedence.ENV_ONLY:
            fn_gen.add_line(f'env = {env_map_assign}')
        else:
            fn_gen.add_line(f'env_map = {env_map_assign}')

            order = _PRECEDENCE_ORDER[env_precedence]

            fn_gen.add_line('maps = []')
            fn_gen.add_line(f'# precedence: {env_precedence.value}')
            for src in order:
                if src == 'secrets':
                    with fn_gen.if_('secrets_dir is not None'):
                        fn_gen.add_line('maps.append(cls._dcw_env_cache_secrets(secrets_dir, reload=reload))')
                elif src == 'dotenv':
                    with fn_gen.if_('env_file'):
                        fn_gen.add_line('maps.append(cls._dcw_env_cache_dotenv(env_file, reload=reload))')
                elif src == 'env':
                    fn_gen.add_line('maps.append(env_map)')

            fn_gen.add_line('env = env_map if len(maps) == 1 else ChainMap(*maps)')

        if (_pre_from_dict := getattr(cls, '_pre_from_dict', None)) is not None:
            new_locals['__pre_from_dict__'] = _pre_from_dict
            fn_gen.add_line('env = __pre_from_dict__(env)')

        fn_gen.add_line('_vars = None')
        # with fn_gen.if_('_secrets_dir'):
        #     fn_gen.add_line('Env.update_with_secret_values(_secrets_dir)')
        #
        # # update environment with values in the "dot env" files as needed.
        # if _meta_env_file:
        #     fn = fn_gen.elif_
        #     _globals['_dotenv_values'] = Env.dotenv_values(_meta_env_file)
        #     with fn_gen.if_('_env_file is None'):
        #         fn_gen.add_line('Env.update_with_dotenv(dotenv_values=_dotenv_values)')
        # else:
        #     fn = fn_gen.if_
        # with fn('_env_file'):
        #     fn_gen.add_line('Env.update_with_dotenv(_env_file)')

        if cls_init_fields:

            with fn_gen.try_():

                if expect_tag_as_unknown_key and pre_assign:
                    with fn_gen.if_(f'{meta.tag_key!r} in env'):
                        fn_gen.add_line('i+=1')

                val = 'v1'
                _val_is_found = f'{val} is not MISSING'
                for i, f in enumerate(cls_init_fields):
                    name = f.name
                    preferred_env_var = f"f'{{pfx}}{name}'"
                    has_default = name in field_to_default
                    val_is_found = _val_is_found

                    tp_var = f'tp_{i}'
                    new_locals[tp_var] = f.type

                    init_params.append(f'{name}:{tp_var}=MISSING')

                    f_assign = f'field={name!r}; {val}={name}'

                    if (has_alias_paths
                            and (paths := field_to_paths.get(name)) is not None):

                        if len(paths) == 1:
                            path = paths[0]

                            # add the first part (top-level key) of the path
                            if set_aliases:
                                aliases.add(path[0])

                            f_assign = f'field={name!r}; {val}=safe_get(env, {path!r}, {not has_default})'
                        else:
                            fn_gen.add_line(f_assign)
                            f_assign = None

                            condition = [val_is_found]
                            last_idx = len(paths) - 1

                            for k, path in enumerate(paths):

                                # add the first part (top-level key) of each path
                                if set_aliases:
                                    aliases.add(path[0])

                                if k == last_idx:
                                    condition.append(
                                        f'({val} := safe_get(env, {path!r}, {not has_default})) is not MISSING')
                                else:
                                    condition.append(
                                        f'({val} := safe_get(env, {path!r}, False)) is not MISSING')

                            if len(condition) > 1:
                                val_is_found = '(' + '\n     or '.join(condition) + ')'
                            else:
                                val_is_found = condition

                        # TODO raise some useful message like (ex. on IndexError):
                        #       Field "my_str" of type tuple[float, str] in A2 has invalid value ['123']

                    else:
                        condition = [val_is_found]

                        if (check_env_vars
                            and (_initial_env_vars := field_to_env_vars.get(name)) is not None):
                            if len(_initial_env_vars) == 1:
                                _aliases = [_initial_env_vars[0]]
                            else:
                                _aliases = list(_initial_env_vars)
                            _has_alias = True
                            # No prefix for explicit aliases!
                            condition.extend([
                                f'({val} := env.get({alias!r}, MISSING)) is not MISSING'
                                for alias in _initial_env_vars
                            ])
                            preferred_env_var = repr(_initial_env_vars[0])
                        else:
                            _aliases = []
                            _has_alias = False

                        if default_strat:
                            _env_vars = possible_env_vars(name, env_key_strat)
                            condition.extend([
                                f"({val} := env.get(f'{{pfx}}{alias}', MISSING)) is not MISSING"
                                for alias in _env_vars
                            ])
                            _aliases.extend(_env_vars)
                            if not _has_alias:
                                preferred_env_var = f"f'{{pfx}}{_env_vars[0]}'"
                        else:  # EnvKeyStrategy.STRICT
                            pass

                        if set_aliases:
                            # add field name itself
                            aliases.add(name)
                            # add possible JSON keys
                            aliases.update(_aliases)

                        if len(condition) > 1:
                            val_is_found = '(' + '\n     or '.join(condition) + ')'
                        else:
                            val_is_found = condition[0]

                    string = generate_field_code(cls_loader, extras, f, i)

                    if f_assign is not None:
                        fn_gen.add_line(f_assign)

                    if has_default:
                        with fn_gen.if_(val_is_found):
                            fn_gen.add_line(f'{pre_assign}self.{name} = {string}')
                        if (default_factory := f.default_factory) is not MISSING:
                            with fn_gen.else_():
                                default_factory_name = f'_dflt{i}'
                                new_locals[default_factory_name] = default_factory
                                fn_gen.add_line(f'self.{name} = {default_factory_name}()')

                    else:
                        # TODO confirm this is ok
                        # vars_for_fields.append(f'{name}={var}')

                        with fn_gen.if_(val_is_found):
                            fn_gen.add_line(f'{pre_assign}self.{name} = {string}')
                        with fn_gen.else_():
                            fn_gen.add_line(f'_vars = add(_vars, field, {preferred_env_var}, {tp_var})')


                # raise `MissingFields`, as required dataclass fields
                # are not present in the input object `env`.
                # fn_gen.add_line("raise_missing_fields(locals(), env, cls, fields)")

                # check for any required fields with missing values
                with fn_gen.if_('_vars is not None'):
                    fn_gen.add_line('raise MissingVars(cls, _vars) from None')

            # create a broad `except Exception` block, as we will be
            # re-raising all exception(s) as a custom `ParseError`.
            with fn_gen.except_(Exception, 'e', ParseError):
                fn_gen.add_line("re_raise(e, cls, env, fields, field, locals().get('v1'))")

        # TODO
        if has_catch_all:
            catch_all_def = f'{{k: env[k] for k in env if k not in aliases}}'

            if catch_all_field.endswith('?'):  # Default value
                with fn_gen.if_('len(env) != i'):
                    fn_gen.add_line(f'self.{catch_all_field_stripped} = {catch_all_def}')
            else:
                var = f'__{catch_all_field_stripped}'
                fn_gen.add_line(f'{var} = {{}} if len(env) == i else {catch_all_def}')
                # vars_for_fields.insert(catch_all_idx, var)

        elif set_aliases:  # warn / raise on unknown key
            line = 'extra_keys = set(env) - aliases'

            with fn_gen.if_('len(env) != i'):
                fn_gen.add_line(line)
                if should_raise:
                    # Raise an error here (if needed)
                    new_locals['UnknownKeysError'] = UnknownKeysError
                    fn_gen.add_line('raise UnknownKeysError(extra_keys, env, cls, fields) from None')
                elif should_warn:
                    # Show a warning here
                    new_locals['LOG'] = LOG
                    fn_gen.add_line(r"LOG.warning('Found %d unknown keys %r not mapped to the dataclass schema.\n"
                                    r"  Class: %r\n  Dataclass fields: %r', "
                                    "len(extra_keys), extra_keys, "
                                    "cls.__qualname__, [f.name for f in fields])")

    # Save the load function for the main dataclass, so we don't need to run
    # this logic each time.
    if is_main_class:
        _locals = {}
        with fn_gen.function(raw_dict_name, ['self'], JSONObject, _locals):
            parts = ','.join([f'{name!r}:self.{name}' for name in cls.__field_names__])
            fn_gen.add_line(f'return {{{parts}}}')

        # noinspection PyUnboundLocalVariable
        functions = fn_gen.create_functions(_globals)

        cls_init = functions[fn_name]
        cls_raw_dict = functions[raw_dict_name]

        _set_new_attribute(
            cls, '__init__', cls_init)
        LOG.debug("setattr(%s, '__init__', %s)",
                  cls_name, fn_name)

        _set_new_attribute(
            cls, raw_dict_name, cls_raw_dict)
        LOG.debug("setattr(%s, %r, %s)",
                  cls_name, raw_dict_name, raw_dict_name)

        # TODO in `v1`, we will use class attribute (set above) instead.
        CLASS_TO_LOAD_FUNC[cls] = cls_init

        return cls_init


def _add_missing_var(missing_vars: dict | None, name, var_name, tp):
    tn = type_name(tp)

    # noinspection PyBroadException
    try:
        suggested = tp()
    except Exception:
        suggested = None

    if missing_vars is None:
        missing_vars = []

    missing_vars.append((name, var_name, tn, suggested))

    return missing_vars


# def _handle_parse_error(e, cls, name, env_prefix, var_name):
#
#     # We run into a parsing error while loading the field
#     # value; Add additional info on the Exception object
#     # before re-raising it.
#     e.class_name = cls
#     e.field_name = name
#     e.kwargs['env_variable'] = _get_var_name(name, env_prefix, var_name)
#
#     raise


def generate_field_code(cls_loader: LoadMixin,
                        extras: Extras,
                        field: Field,
                        field_i: int) -> 'str | TypeInfo':

    cls = extras['cls']
    field_type = field.type = eval_forward_ref_if_needed(field.type, cls)

    try:
        return cls_loader.load_dispatcher_for_annotation(
            TypeInfo(field_type, field_i=field_i), extras
        )

    # except Exception as e:
    #     re_raise(e, cls, None, dataclass_init_fields(cls), field, None)
    except ParseError as pe:
        pe.class_name = cls
        # noinspection PyPropertyAccess
        pe.field_name = field.name
        raise pe from None


def re_raise(e, cls, o, fields, field, value):
    # If the object `o` is None, then raise an error with
    # the relevant info included.
    if o is None:
        raise MissingData(cls) from None

    # Check if the object `o` is some other type than what we expect -
    # for example, we could be passed in a `list` type instead.
    if not isinstance(o, Mapping):
        base_err = TypeError('Incorrect type for `from_dict()`')
        e = ParseError(base_err, o, dict, cls, desired_type=dict)

    add_fields = True
    if type(e) is not ParseError:
        if isinstance(e, JSONWizardError):
            add_fields = False
        else:
            tp = getattr(next((f for f in fields if f.name == field), None), 'type', Any)
            e = ParseError(e, value, tp, 'load')

    # We run into a parsing error while loading the field value;
    # Add additional info on the Exception object before re-raising it.
    #
    # First confirm these values are not already set by an
    # inner dataclass. If so, it likely makes it easier to
    # debug the cause. Note that this should already be
    # handled by the `setter` methods.
    if add_fields:
        e.class_name, e.fields, e.field_name, e.json_object = cls, fields, field, o
    else:
        e.class_name, e.field_name, e.json_object = cls, field, o

    raise e from None


class LoadMixin(V1LoaderMixIn):
    """
    This Mixin class derives its name from the eponymous `json.loads`
    function. Essentially it contains helper methods to convert JSON strings
    (or a Python dictionary object) to a `dataclass` which can often contain
    complex types such as lists, dicts, or even other dataclasses nested
    within it.

    Refer to the :class:`AbstractLoader` class for documentation on any of the
    implemented methods.

    """
    __slots__ = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()

    @staticmethod
    def default_load_to(tp: TypeInfo, extras: Extras):
        # identity: o
        return tp.v()

    @staticmethod
    def load_to_str(tp: TypeInfo, extras: Extras):
        tn = tp.type_name(extras)
        o = tp.v()

        if tp.in_optional:  # str(v)
            return f'{tn}({o})'

        # '' if v is None else str(v)
        default = "''" if tp.origin is str else f'{tn}()'
        return f'{default} if {o} is None else {tn}({o})'

    @staticmethod
    def load_to_int(tp: TypeInfo, extras: Extras):
        """
        Generate code to load a value into an integer field.

        Current logic to parse (an annotated) ``int`` returns:
          - ``v``          -->  ``v`` is an ``int`` or similarly annotated type.
          - ``int(v)``     -->  ``v`` is a ``str`` value of either a decimal
                                integer (e.g. ``'123'``) or a non-fractional
                                float value (e.g. ``42.0``).
          - ``as_int(v)``  -->  ``v`` is a non-fractional ``float``, or in case
                                of "less common" types / scenarios. Note that
                                empty strings and ``None`` (e.g. null values)
                                are not supported.

        """
        tn = tp.type_name(extras)
        o = tp.v()
        tp.ensure_in_locals(extras, as_int=as_int_v1)

        return (f"{o} if (tp := {o}.__class__) is {tn} "
                f"else {tn}("
                f"f if '.' in {o} and (f := float({o})).is_integer() else {o}"
                ") if tp is str "
                f"else as_int({o},tp,{tn})")

        # TODO when `in_union`, we already know `o.__class__`
        #  is not `tn`, and we already have a variable `tp`.

    @staticmethod
    def load_to_float(tp: TypeInfo, extras: Extras):
        # alias: float(o)
        return tp.wrap_builtin(float, tp.v(), extras)

    @staticmethod
    def load_to_bool(tp: TypeInfo, extras: Extras):
        o = tp.v()
        tp.ensure_in_locals(extras, __TRUTHY=TRUTHY_VALUES)

        return (f'{o}.lower() in __TRUTHY '
                f'if {o}.__class__ is str '
                f'else {o} == 1')

    @staticmethod
    def load_to_bytes(tp: TypeInfo, extras: Extras):
        tp.ensure_in_locals(extras, b64decode)
        return f'b64decode({tp.v()})'

    @classmethod
    def load_to_bytearray(cls, tp: TypeInfo, extras: Extras):
        as_bytes = cls.load_to_bytes(tp, extras)
        return tp.wrap_builtin(bytearray, as_bytes, extras)

    @staticmethod
    def load_to_none(tp: TypeInfo, extras: Extras):
        return 'None'

    @staticmethod
    def load_to_enum(tp: TypeInfo, extras: Extras):
        # alias: enum_cls(o)
        return tp.wrap(tp.v(), extras)

    @staticmethod
    def load_to_uuid(tp: TypeInfo, extras: Extras):
        # alias: UUID(o)
        return tp.wrap_builtin(UUID, tp.v(), extras)

    @classmethod
    def load_to_iterable(cls, tp: TypeInfo, extras: Extras):
        v, v_next, i_next = tp.v_and_next()
        gorg = tp.origin

        # noinspection PyBroadException
        try:
            elem_type = tp.args[0]
        except:
            elem_type = Any

        string = cls.load_dispatcher_for_annotation(
            tp.replace(origin=elem_type, i=i_next, index=None), extras)

        if issubclass(gorg, set):
            start_char = '{'
            end_char = '}'
        elif issubclass(gorg, frozenset):
            start_char = 'frozenset(('
            end_char = '))'
        else:
            start_char = '['
            end_char = ']'

        result = f'{start_char}{string} for {v_next} in {v}{end_char}'

        return tp.wrap(result, extras)

    @classmethod
    def load_to_tuple(cls, tp: TypeInfo, extras: Extras):
        args = tp.args

        # Determine the code string for the annotation

        # Check if the `Tuple` appears in the variadic form
        #   i.e. Tuple[str, ...]
        if args:
            is_variadic = args[-1] is ...
        else:
            # Annotated without args, as simply `tuple`
            args = (Any, ...)
            is_variadic = True

        if is_variadic:
            # Logic that handles the variadic form of :class:`Tuple`'s,
            # i.e. ``Tuple[str, ...]``
            #
            # Per `PEP 484`_, only **one** required type is allowed before the
            # ``Ellipsis``. That is, ``Tuple[int, ...]`` is valid whereas
            # ``Tuple[int, str, ...]`` would be invalid. `See here`_ for more info.
            #
            # .. _PEP 484: https://www.python.org/dev/peps/pep-0484/
            # .. _See here: https://github.com/python/typing/issues/180
            v, v_next, i_next = tp.v_and_next()

            # Given `Tuple[T, ...]`, we only need the generated string for `T`
            string = cls.load_dispatcher_for_annotation(
                tp.replace(origin=args[0], i=i_next, index=None), extras)

            result = f'[{string} for {v_next} in {v}]'

            # Wrap because we need to create a tuple from list comprehension
            force_wrap = True
        else:
            string = ', '.join([
                cls.load_dispatcher_for_annotation(
                    tp.replace(origin=arg, index=k),
                    extras)
                for k, arg in enumerate(args)])

            result = f'({string}, )'

            force_wrap = False

        return tp.wrap(result, extras, force=force_wrap)

    @classmethod
    @setup_recursive_safe_function
    def load_to_named_tuple(cls, tp: TypeInfo, extras: Extras):
        fn_gen = extras['fn_gen']
        nt_tp = cast(NamedTuple, tp.origin)

        _locals = extras['locals']
        _locals['cls'] = nt_tp
        _locals['msg'] = "`dict` input is not supported for NamedTuple, use a dataclass instead."

        req_field_to_assign = {}
        field_assigns = []
        # noinspection PyProtectedMember
        optional_fields = set(nt_tp._field_defaults)
        has_optionals = True if optional_fields else False
        only_optionals = has_optionals and len(optional_fields) == len(nt_tp.__annotations__)
        num_fields = 0

        for field, field_tp in nt_tp.__annotations__.items():
            string = cls.load_dispatcher_for_annotation(
                tp.replace(origin=field_tp, index=num_fields), extras)

            if has_optionals and field in optional_fields:
                field_assigns.append(string)
            else:
                req_field_to_assign[f'__{field}'] = string

            num_fields += 1

        params = ', '.join(req_field_to_assign)

        with fn_gen.try_():

            for field, string in req_field_to_assign.items():
                fn_gen.add_line(f'{field} = {string}')

            if has_optionals:
                opt_start = len(req_field_to_assign)
                fn_gen.add_line(f'L = len(v1); has_opt = L > {opt_start}')
                with fn_gen.if_(f'has_opt'):
                    fn_gen.add_line(f'fields = [{field_assigns.pop(0)}]')
                    for i, string in enumerate(field_assigns, start=opt_start + 1):
                        fn_gen.add_line(f'if L > {i}: fields.append({string})')

                    if only_optionals:
                        fn_gen.add_line(f'return cls(*fields)')
                    else:
                        fn_gen.add_line(f'return cls({params}, *fields)')

            fn_gen.add_line(f'return cls({params})')

        with fn_gen.except_(Exception, 'e'):
            with fn_gen.if_('(e_cls := e.__class__) is IndexError'):
                # raise `MissingFields`, as required NamedTuple fields
                # are not present in the input object `o`.
                fn_gen.add_line("raise_missing_fields(locals(), v1, cls, None)")
            with fn_gen.if_('e_cls is KeyError and type(v1) is dict'):
                # Input object is a `dict`
                # TODO should we support dict for namedtuple?
                fn_gen.add_line('raise TypeError(msg) from None')
            # re-raise
            fn_gen.add_line('raise e from None')

    @classmethod
    def load_to_named_tuple_untyped(cls, tp: TypeInfo, extras: Extras):
        # Check if input object is `dict` or `list`.
        #
        # Assuming `Point` is a `namedtuple`, this performs
        # the equivalent logic as:
        #   Point(**x) if isinstance(x, dict) else Point(*x)
        v = tp.v()
        star, dbl_star = tp.multi_wrap(extras, 'nt_', f'*{v}', f'**{v}')
        return f'{dbl_star} if isinstance({v}, dict) else {star}'

    @classmethod
    def _build_dict_comp(cls, tp, v, i_next, k_next, v_next, kt, vt, extras):
        tp_k_next = tp.replace(origin=kt, i=i_next, prefix='k', index=None)
        string_k = cls.load_dispatcher_for_annotation(tp_k_next, extras)

        tp_v_next = tp.replace(origin=vt, i=i_next, prefix='v', index=None)
        string_v = cls.load_dispatcher_for_annotation(tp_v_next, extras)

        return f'{{{string_k}: {string_v} for {k_next}, {v_next} in {v}.items()}}'

    @classmethod
    def load_to_dict(cls, tp: TypeInfo, extras: Extras):
        v, k_next, v_next, i_next = tp.v_and_next_k_v()

        try:
            kt, vt = tp.args
        except ValueError:
            # Annotated without two arguments,
            # e.g. like `dict[str]` or `dict`
            kt = vt = Any

        result = cls._build_dict_comp(
            tp, v, i_next, k_next, v_next, kt, vt, extras)

        return tp.wrap(result, extras)

    @classmethod
    def load_to_defaultdict(cls, tp: TypeInfo, extras: Extras):
        v, k_next, v_next, i_next = tp.v_and_next_k_v()
        default_factory: DefFactory | None

        try:
            kt, vt = tp.args
            default_factory = getattr(vt, '__origin__', vt)
        except ValueError:
            # Annotated without two arguments,
            # e.g. like `defaultdict[str]` or `defaultdict`
            kt = vt = Any
            default_factory = NoneType

        result = cls._build_dict_comp(
            tp, v, i_next, k_next, v_next, kt, vt, extras)

        return tp.wrap_dd(default_factory, result, extras)

    @classmethod
    @setup_recursive_safe_function
    def load_to_typed_dict(cls, tp: TypeInfo, extras: Extras):
        fn_gen = extras['fn_gen']

        req_keys, opt_keys = get_keys_for_typed_dict(tp.origin)

        result_list = []
        # TODO set __annotations__?
        td_annotations = tp.origin.__annotations__

        # Set required keys for the `TypedDict`
        for k in req_keys:
            field_tp = td_annotations[k]
            field_name = repr(k)
            string = cls.load_dispatcher_for_annotation(
                tp.replace(origin=field_tp,
                           index=field_name), extras)

            result_list.append(f'{field_name}: {string}')

        with fn_gen.try_():
            fn_gen.add_lines('result = {',
                             *(f'  {r},' for r in result_list),
                             '}')

            # Set optional keys for the `TypedDict` (if they exist)
            for k in opt_keys:
                field_tp = td_annotations[k]
                field_name = repr(k)
                string = cls.load_dispatcher_for_annotation(
                    tp.replace(origin=field_tp, i=2, index=None), extras)
                with fn_gen.if_(f'(v2 := v1.get({field_name}, MISSING)) is not MISSING'):
                    fn_gen.add_line(f'result[{field_name}] = {string}')
            fn_gen.add_line('return result')

        with fn_gen.except_(Exception, 'e'):
            with fn_gen.if_('type(e) is KeyError'):
                fn_gen.add_line('name = e.args[0]; e = KeyError(f"Missing required key: {name!r}")')
            with fn_gen.elif_('not isinstance(v1, dict)'):
                fn_gen.add_line('e = TypeError("Incorrect type for object")')
            fn_gen.add_line('raise ParseError(e, v1, {}, "load") from None')

    @classmethod
    @setup_recursive_safe_function_for_generic
    def load_to_union(cls, tp: TypeInfo, extras: Extras):
        fn_gen = extras['fn_gen']
        config = extras['config']
        actual_cls = extras['cls']

        tag_key = config.tag_key or TAG
        auto_assign_tags = config.auto_assign_tags

        i = tp.field_i
        fields = f'fields_{i}'

        args = tp.args
        in_optional = NoneType in args

        _locals = extras['locals']
        _locals[fields] = args
        _locals['tag_key'] = tag_key

        dataclass_tag_to_lines: dict[str, list] = {}

        type_checks = []
        try_parse_at_end = []

        for possible_tp in args:

            possible_tp = eval_forward_ref_if_needed(possible_tp, actual_cls)

            tp_new = TypeInfo(possible_tp, field_i=i)
            tp_new.in_optional = in_optional

            if possible_tp is NoneType:
                with fn_gen.if_('v1 is None'):
                    fn_gen.add_line('return None')
                continue

            if is_dataclass(possible_tp):
                # we see a dataclass in `Union` declaration
                meta = get_meta(possible_tp)
                tag = meta.tag
                assign_tags_to_cls = auto_assign_tags or meta.auto_assign_tags
                cls_name = possible_tp.__name__

                if assign_tags_to_cls and not tag:
                    tag = cls_name
                    # We don't want to mutate the base Meta class here
                    if meta is AbstractMeta:
                        create_meta(possible_tp, cls_name, tag=tag)
                    else:
                        meta.tag = cls_name

                if tag:
                    string = cls.load_dispatcher_for_annotation(tp_new, extras)

                    dataclass_tag_to_lines[tag] = [
                        f'if tag == {tag!r}:',
                        f'  return {string}'
                    ]
                    continue

                elif not config.v1_unsafe_parse_dataclass_in_union:
                    e = ValueError('Cannot parse dataclass types in a Union without '
                                   'one of the following `Meta` settings:\n\n'
                                   '  * `auto_assign_tags = True`\n'
                                   f'    - Set on class `{extras["cls_name"]}`.\n\n'
                                   f'  * `tag = "{cls_name}"`\n'
                                   f'    - Set on class `{possible_tp.__qualname__}`.\n\n'
                                   '  * `v1_unsafe_parse_dataclass_in_union = True`\n'
                                   f'    - Set on class `{extras["cls_name"]}`\n\n'
                                   'For more information, refer to:\n'
                                   '  https://dcw.ritviknag.com/en/latest/common_use_cases/dataclasses_in_union_types.html')
                    raise e from None

            string = cls.load_dispatcher_for_annotation(tp_new, extras)

            try_parse_lines = [
                'try:',
                f'  return {string}',
                'except Exception:',
                '  pass',
            ]

            # TODO disable for dataclasses

            if (possible_tp in SIMPLE_TYPES
                or is_subclass_safe(
                    get_origin_v2(possible_tp), SIMPLE_TYPES)):

                tn = tp_new.type_name(extras)
                type_checks.extend([
                    f'if tp is {tn}:',
                    '  return v1'
                ])
                list_to_add = try_parse_at_end
            else:
                list_to_add = type_checks

            list_to_add.extend(try_parse_lines)

        if dataclass_tag_to_lines:

            with fn_gen.try_():
                fn_gen.add_line(f'tag = v1[tag_key]')

            with fn_gen.except_(Exception):
                fn_gen.add_line('pass')

            with fn_gen.else_():

                for lines in dataclass_tag_to_lines.values():
                    fn_gen.add_lines(*lines)

                fn_gen.add_line(
                    "raise ParseError("
                    "TypeError('Object with tag was not in any of Union types'),"
                    f"v1,{fields},'load',"
                    "input_tag=tag,"
                    "tag_key=tag_key,"
                    f"valid_tags={list(dataclass_tag_to_lines)})"
                )

        fn_gen.add_line('tp = type(v1)')

        if type_checks:
            fn_gen.add_lines(*type_checks)

        if try_parse_at_end:
            fn_gen.add_lines(*try_parse_at_end)

        # Invalid type for Union
        fn_gen.add_line("raise ParseError("
                        "TypeError('Object was not in any of Union types'),"
                        f"v1,{fields},'load',"
                        "tag_key=tag_key"
                        ")")

    @staticmethod
    @setup_recursive_safe_function_for_generic
    def load_to_literal(tp: TypeInfo, extras: Extras):
        fn_gen = extras['fn_gen']

        fields = f'fields_{tp.field_i}'

        _locals = extras['locals']
        _locals[fields] = frozenset(tp.args)

        with fn_gen.if_(f'{tp.v()} in {fields}', comment=repr(tp.args)):
            fn_gen.add_line('return v1')

        # No such Literal with the value of `o`
        fn_gen.add_line("e = ValueError('Value not in expected Literal values')")
        fn_gen.add_line(f"raise ParseError(e, v1, {fields},'load', "
                        f'allowed_values=list({fields}))')

        # TODO Checks for Literal equivalence, as mentioned here:
        #   https://www.python.org/dev/peps/pep-0586/#equivalence-of-two-literals

        # extras_cp['locals'][fields] = {
        #     a: type(a) for a in tp.args
        # }
        #
        # with fn_gen.function(fn_name, ['v1'], None, _locals):
        #
        #     with fn_gen.try_():
        #         with fn_gen.if_(f'type({tp.v()}) is {fields}[{tp.v()}]'):
        #             fn_gen.add_line('return v1')
        #
        #         # The value of `o` is in the ones defined for the Literal, but
        #         # also confirm the type matches the one defined for the Literal.
        #         fn_gen.add_line("e = TypeError('Value did not match expected type for the Literal')")
        #
        #         fn_gen.add_line('raise ParseError('
        #                         f'e, v1, {fields}, '
        #                         'have_type=type(v1), '
        #                         f'desired_type={fields}[v1], '
        #                         f'desired_value=next(v for v in {fields} if v == v1), '
        #                         f'allowed_values=list({fields})'
        #                         ')')
        #     with fn_gen.except_(KeyError):
        #         # No such Literal with the value of `o`
        #         fn_gen.add_line("e = ValueError('Value not in expected Literal values')")
        #         fn_gen.add_line('raise ParseError('
        #                         f'e, v1, {fields}, allowed_values=list({fields})'
        #                         f')')

    @staticmethod
    def load_to_decimal(tp: TypeInfo, extras: Extras):
        o = tp.v()
        s = f'str({o}) if {o}.__class__ is float else {o}'

        return tp.wrap_builtin(Decimal, s, extras)

    @staticmethod
    def load_to_path(tp: TypeInfo, extras: Extras):
        # alias: Path(o)
        return tp.wrap_builtin(Path, tp.v(), extras)

    @classmethod
    @process_patterned_date_time
    def load_to_date(cls, tp: TypeInfo, extras: Extras):
        return cls._load_to_date(tp, extras, date)

    @classmethod
    @process_patterned_date_time
    def load_to_datetime(cls, tp: TypeInfo, extras: Extras):
        return cls._load_to_date(tp, extras, datetime)

    @staticmethod
    @process_patterned_date_time
    def load_to_time(tp: TypeInfo, extras: Extras):
        o = tp.v()
        tn = tp.type_name(extras, bound=time)
        tp_time = cast('type[time]', tp.origin)

        __fromisoformat = f'__{tn}_fromisoformat'

        tp.ensure_in_locals(
            extras,
            __as_time=as_time_v1,
            **{__fromisoformat: tp_time.fromisoformat}
        )

        if PY311_OR_ABOVE:
            _parse_iso_string = f'{__fromisoformat}({o})'
        else:  # pragma: no cover
            _parse_iso_string = f"{__fromisoformat}({o}.replace('Z', '+00:00', 1))"

        return (f'{_parse_iso_string} if {o}.__class__ is str '
                f'else __as_time({o}, {tn})')

    @staticmethod
    def _load_to_date(tp: TypeInfo, extras: Extras,
                      cls: type[date] | type[datetime]):
        o = tp.v()
        tn = tp.type_name(extras, bound=cls)
        tp_date_or_datetime = cast('type[date]', tp.origin)

        _fromisoformat = f'__{tn}_fromisoformat'
        _fromtimestamp = f'__{tn}_fromtimestamp'

        name_to_func = {
            _fromisoformat: tp_date_or_datetime.fromisoformat,
            _fromtimestamp: tp_date_or_datetime.fromtimestamp,
        }

        if cls is datetime:
            _as_func = '__as_datetime'
            name_to_func[_as_func] = as_datetime_v1
        else:
            _as_func = '__as_date'
            name_to_func[_as_func] = as_date_v1

        tp.ensure_in_locals(extras, **name_to_func)

        if PY311_OR_ABOVE:
            _parse_iso_string = f'{_fromisoformat}({o})'
        else:  # pragma: no cover
            _parse_iso_string = f"{_fromisoformat}({o}.replace('Z', '+00:00', 1))"

        return (f'{_parse_iso_string} if {o}.__class__ is str '
                f'else {_as_func}({o}, {_fromtimestamp})')

    @staticmethod
    def load_to_timedelta(tp: TypeInfo, extras: Extras):
        # alias: as_timedelta
        tn = tp.type_name(extras, bound=timedelta)
        tp.ensure_in_locals(extras, as_timedelta)

        return f'as_timedelta({tp.v()}, {tn})'

    @staticmethod
    @setup_recursive_safe_function(
        fn_name=f'__{PACKAGE_NAME}_from_dict_{{cls_name}}__')
    def load_to_dataclass(tp: TypeInfo, extras: Extras):
        load_func_for_dataclass(tp.origin, extras)


def check_and_raise_missing_fields(
        _locals, o, cls,
        fields: tuple[Field, ...] | None):

    if fields is None:  # named tuple
        nt_tp = cast(NamedTuple, cls)
        # noinspection PyProtectedMember
        field_to_default = nt_tp._field_defaults

        fields = tuple([
            dataclasses.field(
                default=field_to_default.get(field, MISSING),
            )
            for field in cls.__annotations__])

        for field, name in zip(fields, cls.__annotations__):
            field.name = name

        missing_fields = [f for f in cls.__annotations__
                          if f'__{f}' not in _locals
                          and f not in field_to_default]

        missing_keys = None

    else:
        missing_fields = [f.name for f in fields
                          if f.init
                          and f'__{f.name}' not in _locals
                          and (f.default is MISSING
                               and f.default_factory is MISSING)]

        missing_keys = [v1_dataclass_field_to_env_for_load(cls).get(field, [field])[0]
                        for field in missing_fields]

    masked_environ = {k: '...' for k in o}
    raise MissingFields(
        None, masked_environ, cls, fields, None, missing_fields,
        missing_keys
    ) from None
