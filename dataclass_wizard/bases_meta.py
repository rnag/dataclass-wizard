"""
Ideally should be in the `bases` module, however we'll run into a Circular
Import scenario if we move it there, since the `loaders` and `dumpers` modules
both import directly from `bases`.

"""
import logging
from datetime import datetime, date

from .abstractions import AbstractJSONWizard
from .bases import AbstractMeta, META, AbstractEnvMeta
from .class_helper import (
    META_INITIALIZER, _META,
    get_outer_class_name, get_class_name, create_new_class,
    json_field_to_dataclass_field, dataclass_field_to_json_field,
    field_to_env_var, DATACLASS_FIELD_TO_ALIAS_FOR_LOAD,
)
from .decorators import try_with_load
from .dumpers import get_dumper
from .enums import DateTimeTo, LetterCase, LetterCasePriority
from .v1.enums import KeyAction, KeyCase
from .environ.loaders import EnvLoader
from .errors import ParseError, show_deprecation_warning
from .loader_selection import get_loader
from .log import LOG
from .type_def import E
from .utils.type_conv import date_to_timestamp, as_enum


# global flag to determine if debug mode was ever enabled
_debug_was_enabled = False


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

            # Create a new class of `Type[W]`, and then pass `create=False` so
            # that we don't create new loader / dumper for the class.
            new_cls = create_new_class(cls, (AbstractJSONWizard, ))
            cls.bind_to(new_cls, create=False)

    @classmethod
    def bind_to(cls, dataclass: type, create=True, is_default=True,
                base_loader=None):

        cls_loader = get_loader(dataclass, create=create,
                                base_cls=base_loader, v1=cls.v1)
        cls_dumper = get_dumper(dataclass, create=create)

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

        if cls.v1_key_case is not None:
            cls_loader.transform_json_field = _as_enum_safe(
                cls, 'v1_key_case', KeyCase)

        if (field_to_alias := cls.v1_field_to_alias) is not None:

            add_for_load = field_to_alias.pop('__load__', True)
            add_for_dump = field_to_alias.pop('__dump__', True)

            # Convert string values to single-element tuples
            field_to_aliases = {k: (v, ) if isinstance(v, str) else v
                              for k, v in field_to_alias.items()}

            if add_for_load:
                DATACLASS_FIELD_TO_ALIAS_FOR_LOAD[dataclass].update(
                    field_to_aliases
                )

            if add_for_dump:
                dataclass_field_to_json_field(dataclass).update(
                    {k: v[0] for k, v in field_to_aliases.items()}
                )

        if cls.key_transform_with_dump is not None:
            cls_dumper.transform_dataclass_field = _as_enum_safe(
                cls, 'key_transform_with_dump', LetterCase)

        if cls.v1_on_unknown_key is not None:
            cls.v1_on_unknown_key = _as_enum_safe(cls, 'v1_on_unknown_key', KeyAction)

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

    .. _Docs: https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/meta.html
    """
    base_dict = kwargs | {'__slots__': ()}

    if 'key_transform' in kwargs:
        base_dict['key_transform_with_load'] = base_dict.pop('key_transform')

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

    .. _Docs: https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/meta.html
    """

    # Set meta attributes here.
    base_dict = kwargs | {'__slots__': ()}

    if 'key_transform' in kwargs:
        base_dict['key_transform_with_dump'] = base_dict.pop('key_transform')

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

    .. _Docs: https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/meta.html
    """

    # Set meta attributes here.
    base_dict = kwargs | {'__slots__': ()}

    # Create a new subclass of :class:`AbstractMeta`
    # noinspection PyTypeChecker
    return type('Meta', (BaseEnvWizardMeta, ), base_dict)
