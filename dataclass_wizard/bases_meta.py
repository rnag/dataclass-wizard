"""
Ideally should be in the `bases` module, however we'll run into a Circular
Import scenario if we move it there, since the `loaders` and `dumpers` modules
both import directly from `bases`.

"""
from __future__ import annotations

import logging
from datetime import datetime, date
from typing import Mapping

from .bases import AbstractMeta, META, AbstractEnvMeta
from .class_helper import (
    META_INITIALIZER, _META,
    get_outer_class_name, get_class_name, create_new_class,
    json_field_to_dataclass_field, dataclass_field_to_json_field,
    field_to_env_var, DATACLASS_FIELD_TO_ALIAS_FOR_LOAD, DATACLASS_FIELD_TO_ALIAS_FOR_DUMP, get_meta,
)
from .decorators import try_with_load
from .enums import DateTimeTo, LetterCase, LetterCasePriority
from .v1.enums import KeyAction, KeyCase, DateTimeTo as V1DateTimeTo
from .environ.loaders import EnvLoader
from .errors import ParseError, show_deprecation_warning
from .loader_selection import get_dumper, get_loader
from .log import LOG
from .type_def import E
from .utils.type_conv import date_to_timestamp, as_enum

_ALLOWED_MODES = ('runtime', 'v1_codegen')

# global flag to determine if debug mode was ever enabled
_debug_was_enabled = False


def register_type(cls, tp, *, load=None, dump=None, mode=None) -> None:
    meta = get_meta(cls)

    if meta.v1:
        if load is None:
            load = tp
        if dump is None:
            dump = str

        if (load_hook := meta.v1_type_to_load_hook) is None:
            meta.v1_type_to_load_hook = load_hook = {}
        if (dump_hook := meta.v1_type_to_dump_hook) is None:
            meta.v1_type_to_dump_hook = dump_hook = {}

        load_hook[tp] = (mode if mode else _infer_mode(load), load)
        dump_hook[tp] = (mode if mode else _infer_mode(dump), dump)

    else:
        from .dumpers import DumpMixin
        from .loaders import LoadMixin

        dumper = get_dumper(cls, base_cls=DumpMixin)
        loader = get_loader(cls, base_cls=LoadMixin)

        # default hooks
        load = tp if load is None else load
        dump = str if dump is None else dump

        # adapt to what v0 expects
        load = _adapt_to_arity(load, loader.HOOK_ARITY)
        dump = _adapt_to_arity(dump, dumper.HOOK_ARITY)

        dumper.register_dump_hook(tp, dump)
        loader.register_load_hook(tp, load)


# use `debug_enabled` for log level if it's a str or int.
def _enable_debug_mode_if_needed(cls_loader, possible_lvl):
    global _debug_was_enabled
    if not _debug_was_enabled:
        _debug_was_enabled = True
        # use `debug_enabled` for log level if it's a str or int.
        default_lvl = logging.DEBUG
        # minimum logging level for logs by this library.
        min_level = default_lvl if isinstance(possible_lvl, bool) else possible_lvl
        # set the logging level of this library's logger.
        LOG.setLevel(min_level)
        LOG.info('DEBUG Mode is enabled')

    # Decorate all hooks so they format more helpful messages
    # on error.
    load_hooks = cls_loader.__LOAD_HOOKS__
    for typ in load_hooks:
        load_hooks[typ] = try_with_load(load_hooks[typ])


def _as_enum_safe(cls: type, name: str, base_type: type[E]) -> 'E | None':
    """
    Attempt to return the value for class attribute :attr:`attr_name` as
    a :type:`base_type`.

    :raises ParseError: If we are unable to convert the value of the class
      attribute to an Enum of type `base_type`.
    """
    try:
        return as_enum(getattr(cls, name), base_type)

    except ParseError as e:
        # We run into a parsing error while loading the enum; Add
        # additional info on the Exception object before re-raising it
        e.class_name = get_class_name(cls)
        e.field_name = name
        raise


def _arity(hook) -> int:
    # Python function / method
    code = getattr(hook, "__code__", None)
    if code is not None:
        # reject *args/**kwargs if you want strictness
        if code.co_flags & 0x04 or code.co_flags & 0x08:
            return -1
        return code.co_argcount

    # Classes / C-callables (e.g., IPv4Address) don't expose __code__.
    # Treat as "callable(value)" i.e., 1-arg constructor.
    return 1


def _adapt_to_arity(fn, target_arity: int):
    src = _arity(fn)

    if src == -1:
        # If they already accept *args/**kwargs, it will work everywhere.
        return fn

    if src == target_arity:
        return fn

    # Common case: user gives 1-arg callable but backend passes extra info
    if src == 1 and target_arity > 1:
        def wrapper(x, *rest):
            return fn(x)
        return wrapper

    # Less common: user gives 2-arg (v1 codegen) but v0 expects 1
    # You can reject this unless you have a sane mapping.
    raise TypeError(
        f"Hook {getattr(fn, '__name__', fn)!r} has {src} args, "
        f"but backend expects {target_arity}."
    )


def _infer_mode(hook) -> str:
    code = getattr(hook, '__code__', None)

    if code is None:
        return 'runtime'  # types/builtins

    co_flags = code.co_flags
    if co_flags & 0x04 or co_flags & 0x08:
        raise TypeError('hooks must not use *args/**kwargs')

    argc = code.co_argcount
    if argc == 1:
        return 'runtime'
    if argc == 2:
        return 'v1_codegen'

    raise TypeError('hook must accept 1 arg (runtime) or 2 args (TypeInfo, Extras)')


def _normalize_hooks(hooks: Mapping | None) -> None:
    if not hooks:
        return

    for tp, hook in hooks.items():
        if isinstance(hook, tuple):
            if len(hook) != 2:
                raise ValueError(f"hook tuple must be (mode, hook), got {hook!r}") from None

            mode, fn = hook
            if mode not in _ALLOWED_MODES:
                raise ValueError(
                    f"mode must be 'runtime' or 'v1_codegen' (got {mode!r})"
                ) from None

        else:
            mode = _infer_mode(hook)
            # noinspection PyUnresolvedReferences
            hooks[tp] = mode, hook


class BaseJSONWizardMeta(AbstractMeta):
    """
    Superclass definition for the `JSONWizard.Meta` inner class.

    See the implementation of the :class:`AbstractMeta` class for the
    available config that can be set, as well as for descriptions on any
    implemented methods.
    """

    __slots__ = ()

    @classmethod
    def _init_subclass(cls):
        """
        Hook that should ideally be run whenever the `Meta` class is
        sub-classed.

        """
        outer_cls_name = get_outer_class_name(cls, raise_=False)

        # We can retrieve the outer class name using `__qualname__`, but it's
        # not easy to find the class definition itself. The simplest way seems
        # to be to create a new callable (essentially a class method for the
        # outer class) which will later be called by the base enclosing class.
        #
        # Note that this relies on the observation that the
        # `__init_subclass__` method of any inner classes are run before the
        # one for the outer class.
        if outer_cls_name is not None:
            META_INITIALIZER[outer_cls_name] = cls.bind_to
        else:
            from .abstractions import AbstractJSONWizard

            # The `Meta` class is defined as an outer class. Emit a warning
            # here, just so we can ensure awareness of this special case.
            LOG.warning('The %r class is not declared as an Inner Class, so '
                        'these are global settings that will apply to all '
                        'JSONSerializable sub-classes.', get_class_name(cls))

            # Copy over global defaults to the :class:`AbstractMeta`
            for attr in AbstractMeta.fields_to_merge:
                setattr(AbstractMeta, attr, getattr(cls, attr, None))
            if cls.json_key_to_field:
                AbstractMeta.json_key_to_field = cls.json_key_to_field
            if cls.v1_field_to_alias:
                AbstractMeta.v1_field_to_alias = cls.v1_field_to_alias
            if cls.v1_field_to_alias_dump:
                AbstractMeta.v1_field_to_alias_dump = cls.v1_field_to_alias_dump
            if cls.v1_field_to_alias_load:
                AbstractMeta.v1_field_to_alias_load = cls.v1_field_to_alias_load

            # Create a new class of `Type[W]`, and then pass `create=False` so
            # that we don't create new loader / dumper for the class.
            new_cls = create_new_class(cls, (AbstractJSONWizard, ))
            cls.bind_to(new_cls, create=False)

    @classmethod
    def bind_to(cls, dataclass: type, create=True, is_default=True,
                base_loader=None,
                base_dumper=None):

        cls_loader = get_loader(dataclass, create=create,
                                base_cls=base_loader, v1=cls.v1)
        cls_dumper = get_dumper(dataclass, create=create,
                                base_cls=base_dumper, v1=cls.v1)

        if cls.v1_debug:
            _enable_debug_mode_if_needed(cls_loader, cls.v1_debug)

        elif cls.debug_enabled:
            show_deprecation_warning(
                'debug_enabled',
                fmt="Deprecated Meta setting {name} ({reason}).",
                reason='Use `v1_debug` instead',
            )
            _enable_debug_mode_if_needed(cls_loader, cls.debug_enabled)

        if cls.json_key_to_field is not None:
            add_for_both = cls.json_key_to_field.pop('__all__', None)

            json_field_to_dataclass_field(dataclass).update(
                cls.json_key_to_field
            )

            if add_for_both:
                dataclass_to_json_field = dataclass_field_to_json_field(
                    dataclass)

                # We unfortunately can't use a dict comprehension approach, as
                # we don't know if there are multiple JSON keys mapped to a
                # single dataclass field. So to be safe, we should only set
                # the first JSON key mapped to each dataclass field.
                for json_key, field in cls.json_key_to_field.items():
                    if field not in dataclass_to_json_field:
                        dataclass_to_json_field[field] = json_key


        if cls.v1_dump_date_time_as is not None:
            cls.v1_dump_date_time_as = _as_enum_safe(cls, 'v1_dump_date_time_as', V1DateTimeTo)

        if cls.marshal_date_time_as is not None:
            enum_val = _as_enum_safe(cls, 'marshal_date_time_as', DateTimeTo)

            if enum_val is DateTimeTo.TIMESTAMP:
                # Update dump hooks for the `datetime` and `date` types
                cls_dumper.dump_with_datetime = lambda o, *_: round(o.timestamp())
                cls_dumper.dump_with_date = lambda o, *_: date_to_timestamp(o)
                cls_dumper.register_dump_hook(
                    datetime, cls_dumper.dump_with_datetime)
                cls_dumper.register_dump_hook(
                    date, cls_dumper.dump_with_date)

            elif enum_val is DateTimeTo.ISO_FORMAT:
                # noop; the default dump hook for `datetime` and `date`
                # already serializes using this approach.
                pass

        if cls.key_transform_with_load is not None:
            cls_loader.transform_json_field = _as_enum_safe(
                cls, 'key_transform_with_load', LetterCase)

        if (key_case := cls.v1_case) is not None:
            cls.v1_load_case = cls.v1_dump_case = key_case
            cls.v1_case = None

        if cls.v1_load_case is not None:
            cls_loader.transform_json_field = _as_enum_safe(
                cls, 'v1_load_case', KeyCase)

        if cls.v1_dump_case is not None:
            cls_dumper.transform_dataclass_field = _as_enum_safe(
                cls, 'v1_dump_case', KeyCase)

        if (field_to_alias := cls.v1_field_to_alias) is not None:
            cls.v1_field_to_alias_dump = {
                k: v if isinstance(v, str) else v[0]
                for k, v in field_to_alias.items()
            }
            cls.v1_field_to_alias_load = field_to_alias

        if (field_to_alias := cls.v1_field_to_alias_dump) is not None:
            DATACLASS_FIELD_TO_ALIAS_FOR_DUMP[dataclass].update(field_to_alias)

        if (field_to_alias := cls.v1_field_to_alias_load) is not None:
            DATACLASS_FIELD_TO_ALIAS_FOR_LOAD[dataclass].update({
                k: (v, ) if isinstance(v, str) else v
                for k, v in field_to_alias.items()
            })

        if cls.key_transform_with_dump is not None:
            cls_dumper.transform_dataclass_field = _as_enum_safe(
                cls, 'key_transform_with_dump', LetterCase)

        if cls.v1_on_unknown_key is not None:
            cls.v1_on_unknown_key = _as_enum_safe(cls, 'v1_on_unknown_key', KeyAction)

        _normalize_hooks(cls.v1_type_to_load_hook)
        _normalize_hooks(cls.v1_type_to_dump_hook)

        # Finally, if needed, save the meta config for the outer class. This
        # will allow us to access this config as part of the JSON load/dump
        # process if needed.
        if is_default:
            # Check if the dataclass already has a Meta config; if so, we need to
            # copy over special attributes so they don't get overwritten.
            if dataclass in _META:
                _META[dataclass] &= cls
            else:
                _META[dataclass] = cls


class BaseEnvWizardMeta(AbstractEnvMeta):
    """
    Superclass definition for the `EnvWizard.Meta` inner class.

    See the implementation of the :class:`AbstractEnvMeta` class for the
    available config that can be set, as well as for descriptions on any
    implemented methods.
    """

    __slots__ = ()

    @classmethod
    def _init_subclass(cls):
        """
        Hook that should ideally be run whenever the `Meta` class is
        sub-classed.

        """
        outer_cls_name = get_outer_class_name(cls, raise_=False)

        if outer_cls_name is not None:
            META_INITIALIZER[outer_cls_name] = cls.bind_to
        else:
            from .abstractions import AbstractJSONWizard

            # The `Meta` class is defined as an outer class. Emit a warning
            # here, just so we can ensure awareness of this special case.
            LOG.warning('The %r class is not declared as an Inner Class, so '
                        'these are global settings that will apply to all '
                        'EnvWizard sub-classes.', get_class_name(cls))

            # Copy over global defaults to the :class:`AbstractMeta`
            for attr in AbstractEnvMeta.fields_to_merge:
                setattr(AbstractEnvMeta, attr, getattr(cls, attr, None))
            if cls.field_to_env_var:
                AbstractEnvMeta.field_to_env_var = cls.field_to_env_var

            # Create a new class of `Type[W]`, and then pass `create=False` so
            # that we don't create new loader / dumper for the class.
            new_cls = create_new_class(cls, (AbstractJSONWizard, ))
            cls.bind_to(new_cls, create=False)

    @classmethod
    def bind_to(cls, env_class: type, create=True, is_default=True):

        cls_loader = get_loader(env_class, create=create, base_cls=EnvLoader)
        cls_dumper = get_dumper(env_class, create=create)

        if cls.debug_enabled:
            _enable_debug_mode_if_needed(cls_loader, cls.debug_enabled)

        if cls.field_to_env_var is not None:
            field_to_env_var(env_class).update(
                cls.field_to_env_var
            )

        cls.key_lookup_with_load = _as_enum_safe(
            cls, 'key_lookup_with_load', LetterCasePriority)

        cls_dumper.transform_dataclass_field = _as_enum_safe(
            cls, 'key_transform_with_dump', LetterCase)

        # Finally, if needed, save the meta config for the outer class. This
        # will allow us to access this config as part of the JSON load/dump
        # process if needed.
        if is_default:
            # Check if the dataclass already has a Meta config; if so, we need to
            # copy over special attributes so they don't get overwritten.
            if env_class in _META:
                _META[env_class] &= cls
            else:
                _META[env_class] = cls


# noinspection PyPep8Naming
def LoadMeta(**kwargs) -> META:
    """
    Helper function to setup the ``Meta`` Config for the JSON load
    (de-serialization) process, which is intended for use alongside the
    ``fromdict`` helper function.

    For descriptions on what each of these params does, refer to the `Docs`_
    below, or check out the :class:`AbstractMeta` definition (I want to avoid
    duplicating the descriptions for params here).

    Examples::

        >>> LoadMeta(key_transform='CAMEL').bind_to(MyClass)
        >>> fromdict(MyClass, {"myStr": "value"})

    .. _Docs: https://dcw.ritviknag.com/en/latest/common_use_cases/meta.html
    """
    base_dict = kwargs | {'__slots__': ()}

    if (v := base_dict.pop('key_transform', None)) is not None:
        base_dict['key_transform_with_load'] = v

    if (v := base_dict.pop('v1_case', None)) is not None:
        base_dict['v1_load_case'] = v

    if (v := base_dict.pop('v1_field_to_alias', None)) is not None:
        base_dict['v1_field_to_alias_load'] = v

    # Create a new subclass of :class:`AbstractMeta`
    # noinspection PyTypeChecker
    return type('Meta', (BaseJSONWizardMeta, ), base_dict)


# noinspection PyPep8Naming
def DumpMeta(**kwargs) -> META:
    """
    Helper function to setup the ``Meta`` Config for the JSON dump
    (serialization) process, which is intended for use alongside the
    ``asdict`` helper function.

    For descriptions on what each of these params does, refer to the `Docs`_
    below, or check out the :class:`AbstractMeta` definition (I want to avoid
    duplicating the descriptions for params here).

    Examples::

        >>> DumpMeta(key_transform='CAMEL').bind_to(MyClass)
        >>> asdict(MyClass, {"myStr": "value"})

    .. _Docs: https://dcw.ritviknag.com/en/latest/common_use_cases/meta.html
    """

    # Set meta attributes here.
    base_dict = kwargs | {'__slots__': ()}

    if (v := base_dict.pop('key_transform', None)) is not None:
        base_dict['key_transform_with_dump'] = v

    if (v := base_dict.pop('v1_case', None)) is not None:
        base_dict['v1_dump_case'] = v

    if (v := base_dict.pop('v1_field_to_alias', None)) is not None:
        base_dict['v1_field_to_alias_dump'] = v

    # Create a new subclass of :class:`AbstractMeta`
    # noinspection PyTypeChecker
    return type('Meta', (BaseJSONWizardMeta, ), base_dict)


# noinspection PyPep8Naming
def EnvMeta(**kwargs) -> META:
    """
    Helper function to setup the ``Meta`` Config for the EnvWizard.

    For descriptions on what each of these params does, refer to the `Docs`_
    below, or check out the :class:`AbstractEnvMeta` definition (I want to avoid
    duplicating the descriptions for params here).

    Examples::

        >>> EnvMeta(key_transform_with_dump='SNAKE').bind_to(MyClass)

    .. _Docs: https://dcw.ritviknag.com/en/latest/common_use_cases/meta.html
    """

    # Set meta attributes here.
    base_dict = kwargs | {'__slots__': ()}

    # Create a new subclass of :class:`AbstractMeta`
    # noinspection PyTypeChecker
    return type('Meta', (BaseEnvWizardMeta, ), base_dict)
