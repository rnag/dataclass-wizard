from __future__ import annotations

import json
import logging
import os
from collections import ChainMap
from dataclasses import Field, MISSING
# noinspection PyUnresolvedReferences,PyProtectedMember
from dataclasses import _FIELD_INITVAR, _POST_INIT_NAME
from typing import (Any, Callable, Mapping, TYPE_CHECKING)

from ._path_util import get_secrets_map, get_dotenv_map
from .enums import EnvKeyStrategy, EnvPrecedence
from .loaders import LoadMixin as V1LoadMixin
from .models import Extras, TypeInfo, SEQUENCE_ORIGINS, MAPPING_ORIGINS
from .type_conv import as_list_v1, as_dict_v1
from ..bases import META, AbstractEnvMeta, ENV_META
from ..bases_meta import BaseEnvWizardMeta, EnvMeta, register_type
from ..class_helper import (dataclass_fields,
                            dataclass_field_to_default,
                            dataclass_init_fields,
                            dataclass_init_field_names,
                            get_meta,
                            v1_dataclass_field_to_env_for_load,
                            CLASS_TO_LOAD_FUNC,
                            DATACLASS_FIELD_TO_ALIAS_PATH_FOR_LOAD,
                            call_meta_initializer_if_needed,
                            dataclass_field_names)
from ..constants import CATCH_ALL, PACKAGE_NAME
from ..decorators import cached_class_property
from ..errors import (JSONWizardError,
                      MissingData,
                      ParseError,
                      type_name, MissingVars)
from ..loader_selection import get_loader, asdict
from ..log import LOG, enable_library_debug_logging
from ..type_def import T, JSONObject, dataclass_transform
# noinspection PyProtectedMember
from ..utils.dataclass_compat import (_apply_env_wizard_dataclass,
                                      _dataclass_needs_refresh,
                                      _set_new_attribute)
from ..utils.function_builder import FunctionBuilder
from ..utils.object_path import v1_env_safe_get
from ..utils.string_conv import possible_env_vars
from ..utils.typing_compat import (eval_forward_ref_if_needed)

if TYPE_CHECKING:
    from ._env import EnvInit, E_


def env_config(**kw):
    return kw


_PRECEDENCE_ORDER: dict[EnvPrecedence, tuple[str, ...]] = {
    EnvPrecedence.SECRETS_ENV_DOTENV: ('secrets', 'env', 'dotenv'),
    EnvPrecedence.SECRETS_DOTENV_ENV: ('secrets', 'dotenv', 'env'),
    EnvPrecedence.ENV_ONLY: ('env', ),
}


def _pre_decoder(_cls: V1LoadMixin, container_tp: type, tp: TypeInfo, extras: Extras):
    if tp.i == 1:  # Outermost container (first seen in field annotation)
        if container_tp in SEQUENCE_ORIGINS:
            tp.ensure_in_locals(extras, as_list=as_list_v1)
            return tp.replace(val_name=f'as_list({tp.v()})')

        elif container_tp in MAPPING_ORIGINS:
            tp.ensure_in_locals(extras, as_dict=as_dict_v1)
            return tp.replace(val_name=f'as_dict({tp.v()})')

    return tp


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
        if cls.__module__.startswith(f'{PACKAGE_NAME}.'):  # pragma: no cover
            return

        # Apply the @dataclass decorator.
        if _apply_dataclass and _dataclass_needs_refresh(cls):
            # noinspection PyArgumentList
            _apply_env_wizard_dataclass(cls, dc_kwargs)

        load_meta_kwargs = {'v1': True, 'v1_pre_decoder': _pre_decoder}

        if debug:
            lvl = logging.DEBUG if isinstance(debug, bool) else debug
            enable_library_debug_logging(lvl)
            # set `v1_debug` flag for the class's Meta
            load_meta_kwargs['v1_debug'] = lvl

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

    # Does this class have a post-init function?
    has_post_init = hasattr(cls, _POST_INIT_NAME)

    # Get the loader for the class, or create a new one as needed.
    cls_loader = get_loader(cls, base_cls=loader_cls or LoadMixin, v1=True)

    cls_name = cls.__name__

    fn_name = f'__{PACKAGE_NAME}_init_{cls_name}__'
    raw_dict_name = f'__{PACKAGE_NAME}_raw_dict_{cls_name}__'

    # Get the meta config for the class, or the default config otherwise.
    meta = get_meta(cls, base_meta_cls)

    # if extras is None:  # we are being run for the main dataclass
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
        're_raise': re_raise,
    }

    # we are being run for a nested dataclass
    # NOTE: I don't believe this path exists, since `v1.loaders.from_dict`
    # is used for nested dataclasses.
    #
    # else:
    #     is_main_class = False

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
        new_locals['safe_get'] = v1_env_safe_get

    add_body_lines = cls_init_fields or has_catch_all

    _env_defaults: EnvInit = {}
    if _env_file := meta.env_file:
        _env_defaults['file'] = _env_file
    if (_env_prefix := meta.env_prefix) is not None:
        _env_defaults['prefix'] = _env_prefix
    LOG.debug('__env__ defaults = %r', _env_defaults)
    if (_secrets_dir := meta.secrets_dir) is not None:
        _env_defaults['secrets_dir'] = _secrets_dir
        LOG.debug('secrets_dir = <configured>')

    new_locals['_env_defaults'] = _env_defaults
    init_params = ['self',
                   "__env__:'EnvInit'=None",
                   '*']

    with fn_gen.function(fn_name, init_params, MISSING, new_locals):
        if add_body_lines:
            fn_gen.add_line('cfg = _env_defaults if __env__ is None else _env_defaults | __env__')
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

            with fn_gen.try_():

                if expect_tag_as_unknown_key and pre_assign:
                    with fn_gen.if_(f'{meta.tag_key!r} in env'):
                        fn_gen.add_line('i+=1')

                val = 'v1'
                _val_is_found = f'{val} is not MISSING'
                for i, f in enumerate(cls_init_fields):
                    name = f.name
                    preferred_env_var = f"f'{{pfx}}{name}'"
                    has_default = has_defaults and name in field_to_default
                    val_is_found = _val_is_found

                    tp_var = f'tp_{i}'
                    new_locals[tp_var] = f.type

                    init_params.append(f'{name}:{tp_var}=MISSING')

                    f_assign = f'field={name!r}; {val}={name}'

                    condition = [val_is_found]

                    if (has_alias_paths
                            and (paths := field_to_paths.get(name)) is not None):

                        if len(paths) == 1:
                            first_key, *path = paths[0]

                            # add the first part (top-level key) of the path
                            if set_aliases:
                                aliases.add(first_key)

                            condition.append(
                                f'({val} := safe_get(env, {first_key!r}, {path!r}, {not has_default})) is not MISSING'
                            )
                        else:
                            last_idx = len(paths) - 1

                            for k, path in enumerate(paths):
                                first_key, *path = path

                                # add the first part (top-level key) of each path
                                if set_aliases:
                                    aliases.add(first_key)

                                if k == last_idx:
                                    condition.append(
                                        f'({val} := safe_get(env, {first_key!r}, {path!r}, {not has_default})) is not MISSING')
                                else:
                                    condition.append(
                                        f'({val} := safe_get(env, {first_key!r}, {path!r}, False)) is not MISSING')

                        # TODO raise some useful message like (ex. on IndexError):
                        #       Field "my_str" of type tuple[float, str] in A2 has invalid value ['123']

                    else:
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
                        with fn_gen.if_(val_is_found):
                            fn_gen.add_line(f'{pre_assign}self.{name} = {string}')
                        with fn_gen.else_():
                            fn_gen.add_line(f'_vars = add(_vars, field, {preferred_env_var}, {tp_var})')

                # check for any required fields with missing values
                with fn_gen.if_('_vars is not None'):
                    fn_gen.add_line('raise MissingVars(cls, _vars) from None')

            # create a broad `except Exception` block, as we will be
            # re-raising all exception(s) as a custom `ParseError`.
            with fn_gen.except_(Exception, 'e', ParseError):
                fn_gen.add_line("re_raise(e, cls, env, fields, field, locals().get('v1'))")

        elif not has_post_init:
            fn_gen.add_line('pass')

        if not cls_init_fields:
            init_params.pop()  # remove trailing `*` in function params

        if has_catch_all:
            catch_all_def = f'{{k: env[k] for k in env if k not in aliases}}'

            if catch_all_field.endswith('?'):  # Default value
                with fn_gen.if_('len(env) != i'):
                    fn_gen.add_line(f'self.{catch_all_field_stripped} = {catch_all_def}')
            else:
                fn_gen.add_line(f'self.{catch_all_field_stripped} = {{}} if len(env) == i else {catch_all_def}')

        # elif set_aliases:  # warn / raise on unknown key
        #     line = 'extra_keys = set(env) - aliases'
        #
        #     with fn_gen.if_('len(env) != i'):
        #         fn_gen.add_line(line)
        #         if should_raise:
        #             # Raise an error here (if needed)
        #             new_locals['UnknownKeysError'] = UnknownKeysError
        #             fn_gen.add_line('raise UnknownKeysError(extra_keys, env, cls, fields) from None')
        #         elif should_warn:
        #             # Show a warning here
        #             new_locals['LOG'] = LOG
        #             fn_gen.add_line(r"LOG.warning('Found %d unknown keys %r not mapped to the dataclass schema.\n"
        #                             r"  Class: %r\n  Dataclass fields: %r', "
        #                             "len(extra_keys), extra_keys, "
        #                             "cls.__qualname__, [f.name for f in fields])")

        # Does this class have a post-init function?
        if has_post_init:
            # noinspection PyUnresolvedReferences,PyProtectedMember
            params_str = ','.join(f.name for f in fields
                                  if f._field_type is _FIELD_INITVAR)
            fn_gen.add_line(f'self.{_POST_INIT_NAME}({params_str})')

    # Save the load function for the main dataclass, so we don't need to run
    # this logic each time.
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
        cls, 'raw_dict', cls_raw_dict)
    LOG.debug("setattr(%s, 'raw_dict', %s)",
              cls_name, raw_dict_name)

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


class LoadMixin(V1LoadMixin):
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
    def is_none(tp: TypeInfo, extras: Extras) -> str:
        o = tp.v()
        return f"{o} is None or {o} == 'null'"

    @staticmethod
    def load_to_bytes(tp: TypeInfo, extras: Extras):
        # could add support for b64-encoded strings later:
        # bytes(__b64decode(o)) if (o.__class__ is str and __env_b64)
        o = tp.v()
        return (f"{o} if (t := {o}.__class__) is bytes "
                f"else {o}.encode('utf-8') if t is str "
                f"else bytes({o})")

    @classmethod
    def load_to_bytearray(cls, tp: TypeInfo, extras: Extras):
        o = tp.v()
        as_bytes = cls.load_to_bytes(tp, extras)
        return (f'{o} if {o}.__class__ is bytearray '
                f'else {tp.wrap_builtin(bytearray, as_bytes, extras)}')

    @classmethod
    def load_to_dataclass(cls, tp: TypeInfo, extras: Extras):
        # pre-decoder wraps `v()` in `asdict(...)`, so use the wrapped value
        o = tp.v_for_def()
        tn = tp.type_name(extras)
        from_dict = super().load_to_dataclass(tp, extras)
        return f'{o} if {o}.__class__ is {tn} else {from_dict}'
