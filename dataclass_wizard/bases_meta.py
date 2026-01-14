"""
Ideally should be in the `bases` module, however we'll run into a Circular
Import scenario if we move it there, since the `loaders` and `dumpers` modules
both import directly from `bases`.

"""
from __future__ import annotations

import logging
from typing import Mapping

from .bases import AbstractMeta, META, AbstractEnvMeta
from .class_helper import (
    META_INITIALIZER, get_meta,
    get_outer_class_name, get_class_name, create_new_class,
    DATACLASS_FIELD_TO_ALIAS_FOR_LOAD,
    DATACLASS_FIELD_TO_ENV_FOR_LOAD,
    DATACLASS_FIELD_TO_ALIAS_FOR_DUMP, create_meta,
)
from .errors import ParseError
from .loaders import LoadMixin, get_loader
from .dumpers import DumpMixin, get_dumper
from ._log import LOG
from ._meta_cache import META_BY_DATACLASS
from .type_def import E
from .type_conv import as_enum


ALLOWED_MODES = ('runtime', 'codegen')

# global flag to determine if debug mode was ever enabled
_debug_was_enabled = False


def register_type(cls, tp, *, load=None, dump=None, mode=None) -> None:
    meta = get_meta(cls)
    if meta is AbstractMeta:
        meta = create_meta(cls)

    if load is None:
        load = tp
    if dump is None:
        dump = str

    if (load_hook := meta.type_to_load_hook) is None:
        meta.type_to_load_hook = load_hook = {}
    if (dump_hook := meta.type_to_dump_hook) is None:
        meta.type_to_dump_hook = dump_hook = {}

    load_hook[tp] = (mode if mode else _infer_mode(load), load)
    dump_hook[tp] = (mode if mode else _infer_mode(dump), dump)


# use `debug` for log level if it's a str or int.
def _enable_debug_mode_if_needed(possible_lvl):
    global _debug_was_enabled
    if not _debug_was_enabled:
        _debug_was_enabled = True
        # use `debug` for log level if it's a str or int.
        default_lvl = logging.DEBUG
        # minimum logging level for logs by this library.
        min_level = default_lvl if isinstance(possible_lvl, bool) else possible_lvl
        # set the logging level of this library's logger.
        LOG.setLevel(min_level)
        LOG.info('DEBUG Mode is enabled')


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
        return 'codegen'

    raise TypeError('hook must accept 1 arg (runtime) or 2 args (TypeInfo, Extras)')


def _normalize_hooks(hooks: Mapping | None) -> None:
    if not hooks:
        return

    for tp, hook in hooks.items():
        if isinstance(hook, tuple):
            if len(hook) != 2:
                raise ValueError(f"hook tuple must be (mode, hook), got {hook!r}") from None

            mode, fn = hook
            if mode not in ALLOWED_MODES:
                raise ValueError(
                    f"mode must be 'runtime' or 'codegen' (got {mode!r})"
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
            if cls.field_to_alias:
                AbstractMeta.field_to_alias = cls.field_to_alias
            if cls.field_to_alias_dump:
                AbstractMeta.field_to_alias_dump = cls.field_to_alias_dump
            if cls.field_to_alias_load:
                AbstractMeta.field_to_alias_load = cls.field_to_alias_load

            # Create a new class of `Type[W]`, and then pass `create=False` so
            # that we don't create new loader / dumper for the class.
            new_cls = create_new_class(cls, (AbstractJSONWizard, ))
            cls.bind_to(new_cls, create=False)

    @classmethod
    def bind_to(cls, dataclass: type, create=True, is_default=True,
                base_loader=LoadMixin,
                base_dumper=DumpMixin):
        # TODO
        from .enums import KeyAction, KeyCase, DateTimeTo as V1DateTimeTo

        cls_loader = get_loader(dataclass, create=create,
                                base_cls=base_loader)
        cls_dumper = get_dumper(dataclass, create=create,
                                base_cls=base_dumper)

        if cls.debug:
            _enable_debug_mode_if_needed(cls.debug)

        if cls.dump_date_time_as is not None:
            cls.dump_date_time_as = _as_enum_safe(cls, 'dump_date_time_as', V1DateTimeTo)

        if (key_case := cls.case) is not None:
            cls.load_case = cls.dump_case = key_case
            cls.case = None

        if cls.load_case is not None:
            cls_loader.transform_json_field = _as_enum_safe(
                cls, 'load_case', KeyCase)

        if cls.dump_case is not None:
            cls_dumper.transform_dataclass_field = _as_enum_safe(
                cls, 'dump_case', KeyCase)

        if (field_to_alias := cls.field_to_alias) is not None:
            cls.field_to_alias_dump = {
                k: v if isinstance(v, str) else v[0]
                for k, v in field_to_alias.items()
            }
            cls.field_to_alias_load = field_to_alias

        if (field_to_alias := cls.field_to_alias_dump) is not None:
            DATACLASS_FIELD_TO_ALIAS_FOR_DUMP[dataclass].update(field_to_alias)

        if (field_to_alias := cls.field_to_alias_load) is not None:
            DATACLASS_FIELD_TO_ALIAS_FOR_LOAD[dataclass].update({
                k: (v, ) if isinstance(v, str) else v
                for k, v in field_to_alias.items()
            })

        if cls.on_unknown_key is not None:
            cls.on_unknown_key = _as_enum_safe(cls, 'on_unknown_key', KeyAction)

        _normalize_hooks(cls.type_to_load_hook)
        _normalize_hooks(cls.type_to_dump_hook)

        # Finally, if needed, save the meta config for the outer class. This
        # will allow us to access this config as part of the JSON load/dump
        # process if needed.
        if is_default:
            # Check if the dataclass already has a Meta config; if so, we need to
            # copy over special attributes so they don't get overwritten.
            if dataclass in META_BY_DATACLASS:
                META_BY_DATACLASS[dataclass] &= cls
            else:
                META_BY_DATACLASS[dataclass] = cls


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
            if cls.field_to_alias_dump:
                AbstractEnvMeta.field_to_alias_dump = cls.field_to_alias_dump
            if cls.field_to_env_load:
                AbstractEnvMeta.field_to_env_load = cls.field_to_env_load

            # Create a new class of `Type[W]`, and then pass `create=False` so
            # that we don't create new loader / dumper for the class.
            new_cls = create_new_class(cls, (AbstractJSONWizard, ))
            cls.bind_to(new_cls, create=False)

    @classmethod
    def bind_to(cls, env_class: type, create=True, is_default=True):
        # TODO
        from .enums import KeyCase, EnvKeyStrategy, EnvPrecedence

        cls_dumper = get_dumper(
            env_class,
            create=create)

        if cls.debug:
            _enable_debug_mode_if_needed(cls.debug)

        if cls.load_case is not None:
            cls.load_case = _as_enum_safe(
                cls, 'load_case', EnvKeyStrategy)
        if cls.env_precedence is not None:
            cls.env_precedence = _as_enum_safe(
                cls, 'env_precedence', EnvPrecedence)

        # TODO
        cls_dumper.transform_dataclass_field = _as_enum_safe(
            cls, 'dump_case', KeyCase)

        if (field_to_alias := cls.field_to_alias_dump) is not None:
            DATACLASS_FIELD_TO_ALIAS_FOR_DUMP[env_class].update(field_to_alias)

        if (field_to_env := cls.field_to_env_load) is not None:
            DATACLASS_FIELD_TO_ENV_FOR_LOAD[env_class].update({
                k: (v, ) if isinstance(v, str) else v
                for k, v in field_to_env.items()
            })

        # set this attribute in case of nested dataclasses (which
        # uses codegen in `loaders.py`)
        cls.on_unknown_key = None

        # if cls.on_unknown_key is not None:
        #     cls.on_unknown_key = _as_enum_safe(cls, 'on_unknown_key', KeyAction)

        _normalize_hooks(cls.type_to_load_hook)
        _normalize_hooks(cls.type_to_dump_hook)

        # Finally, if needed, save the meta config for the outer class. This
        # will allow us to access this config as part of the JSON load/dump
        # process if needed.
        if is_default:
            # Check if the dataclass already has a Meta config; if so, we need to
            # copy over special attributes so they don't get overwritten.
            if env_class in META_BY_DATACLASS:
                META_BY_DATACLASS[env_class] &= cls
            else:
                META_BY_DATACLASS[env_class] = cls


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

    if (v := base_dict.pop('case', None)) is not None:
        base_dict['load_case'] = v

    if (v := base_dict.pop('field_to_alias', None)) is not None:
        base_dict['field_to_alias_load'] = v

    if (v := base_dict.pop('type_to_hook', None)) is not None:
        base_dict['type_to_load_hook'] = v

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

    if (v := base_dict.pop('case', None)) is not None:
        base_dict['dump_case'] = v

    if (v := base_dict.pop('field_to_alias', None)) is not None:
        base_dict['field_to_alias_dump'] = v

    if (v := base_dict.pop('type_to_hook', None)) is not None:
        base_dict['type_to_dump_hook'] = v

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
    return type('EnvMeta', (BaseEnvWizardMeta, ), base_dict)
