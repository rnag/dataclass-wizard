"""
Ideally should be in the `bases` module, however we'll run into a Circular
Import scenario if we move it there, since the `loaders` and `dumpers` modules
both import directly from `bases`.

"""
from datetime import datetime, date
from typing import Type, Optional, Dict, Union

from .abstractions import W, AbstractJSONWizard
from .bases import BaseMeta, M
from .class_helper import (
    _META_INITIALIZER, _META,
    get_outer_class_name, get_class_name, create_new_class,
    json_field_to_dataclass_field, dataclass_field_to_json_field
)
from .decorators import try_with_load
from .dumpers import get_dumper
from .enums import LetterCase, DateTimeTo
from .errors import ParseError
from .loaders import get_loader
from .log import LOG
from .type_def import E, T
from .utils.type_conv import date_to_timestamp, as_enum


# Internal mappings which help us keep a track of whether the `Meta`
# config is already setup for a dataclass.
#
# Note: These are *only* for use with the ``fromdict`` and ``asdict``
# helper functions.
_LOAD_META: Dict[Type, Type[M]] = {}
_DUMP_META: Dict[Type, Type[M]] = {}


class BaseJSONWizardMeta(BaseMeta):
    """
    Superclass definition for the `JSONWizard.Meta` inner class.

    See the implementation of the :class:`BaseMeta` class for the
    available config that can be set.
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
            _META_INITIALIZER[outer_cls_name] = cls._meta_initialize
        else:
            # The `Meta` class is defined as an outer class. Emit a warning
            # here, just so we can ensure awareness of this special case.
            LOG.warning('The %r class is not declared as an Inner Class, so '
                        'these are global settings that will apply to all '
                        'JSONSerializable sub-classes.', get_class_name(cls))

            # Copy over global defaults to the :class:`BaseMeta`
            exclude_attrs = ('debug_enabled', )
            for attr in BaseMeta.__annotations__:
                if attr not in exclude_attrs:
                    setattr(BaseMeta, attr, getattr(cls, attr, None))

            # Create a new class of `Type[W]`, and then pass `create=False` so
            # that we don't create new loader / dumper for the class.
            new_cls = create_new_class(cls, (AbstractJSONWizard, ))
            cls._meta_initialize(new_cls, create=False)

    @classmethod
    def _meta_initialize(cls, outer_cls: Type[W], create=True):
        """
        Initialize hook which is called by the outer class (typically
        a sub-class of :class:`AbstractJSONWizard`)

        :param outer_cls:
        :param create: When true, a separate loader/dumper will be created
          for the class. If disabled, this will access the root loader/dumper,
          so modifying this should affect global settings across all
          dataclasses that use the JSON load/dump process.
        """
        cls_loader = get_loader(outer_cls, create=create)
        cls_dumper = get_dumper(outer_cls, create=create)

        if cls.debug_enabled:

            LOG.setLevel('DEBUG')
            LOG.info('DEBUG Mode is enabled')
            # Decorate all hooks so they format more helpful messages
            # on error.
            load_hooks = cls_loader.__LOAD_HOOKS__
            for typ in load_hooks:
                load_hooks[typ] = try_with_load(load_hooks[typ])

        if cls.json_key_to_field:
            add_for_both = cls.json_key_to_field.pop('__all__', None)

            json_field_to_dataclass_field(outer_cls).update(
                cls.json_key_to_field
            )

            if add_for_both:
                dataclass_to_json_field = dataclass_field_to_json_field(
                    outer_cls)

                # We unfortunately can't use a dict comprehension approach, as
                # we don't know if there are multiple JSON keys mapped to a
                # single dataclass field. So to be safe, we should only set
                # the first JSON key mapped to each dataclass field.
                for json_key, field in cls.json_key_to_field.items():
                    if field not in dataclass_to_json_field:
                        dataclass_to_json_field[field] = json_key

        if cls.marshal_date_time_as:
            enum_val = cls._as_enum_safe('marshal_date_time_as', DateTimeTo)

            if enum_val is DateTimeTo.TIMESTAMP:
                # Update dump hooks for the `datetime` and `date` types
                cls_dumper.register_dump_hook(
                    datetime, lambda o, *_: round(o.timestamp()))
                cls_dumper.register_dump_hook(
                    date, lambda o, *_: date_to_timestamp(o))

            elif enum_val is DateTimeTo.ISO_FORMAT:
                # noop; the default dump hook for `datetime` and `date` already
                # serializes using this approach.
                pass

        if cls.key_transform_with_load:

            cls_loader.transform_json_field = cls._as_enum_safe(
                'key_transform_with_load', LetterCase)

        if cls.key_transform_with_dump:

            cls_dumper.transform_dataclass_field = cls._as_enum_safe(
                'key_transform_with_dump', LetterCase)

        # Finally, save the meta config for the outer class. This will allow
        # us to access this config as part of the JSON load/dump process if
        # needed.
        _META[outer_cls] = cls

    @classmethod
    def _as_enum_safe(cls, name: str, base_type: Type[E]) -> Optional[E]:
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


# noinspection PyPep8Naming
def LoadMeta(data_class: Type[T],
             debug_enabled: bool = False,
             raise_on_unknown_json_key: bool = False,
             json_key_to_field: Dict[str, str] = None,
             key_transform: Union[LetterCase, str] = None) -> M:
    """
    Helper function to setup the ``Meta`` Config for the JSON load
    (de-serialization) process, which is intended for use alongside the
    ``fromdict`` helper function.

    For descriptions on what each of these params does, refer to the `Docs`_
    below, or check out the :class:`BaseMeta` definition (I want to avoid
    duplicating the descriptions for params here).

    Examples::

        >>> fromdict(MyClass, {"myStr": "value"}, \
                     LoadMeta(MyClass, key_transform='CAMEL'))

    .. _Docs: https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/meta.html
    """
    try:
        return _LOAD_META[data_class]

    except KeyError:
        # Initial run - we have not set up the load config for the class yet

        try:
            cls_meta = _META[data_class]
        except KeyError:
            # Meta does not exist for the class. Create a new subclass of
            # :class:`BaseMeta`, and cache it so we have it for next time
            # (for example for the dump or serialization process).
            cls_meta = create_new_class(
                data_class, (BaseJSONWizardMeta, ), suffix='Meta')

        # Set meta attributes here.
        cls_meta.debug_enabled |= debug_enabled
        cls_meta.raise_on_unknown_json_key = raise_on_unknown_json_key
        cls_meta.json_key_to_field = json_key_to_field
        cls_meta.key_transform_with_load = key_transform

        # Run the meta initialization for the dataclass, and also save the
        # mapping to `_META` so we have it for next time.
        # noinspection PyProtectedMember
        cls_meta._meta_initialize(data_class)

        # Save the load config, so we don't have to run this logic each time.
        _LOAD_META[data_class] = cls_meta


# noinspection PyPep8Naming
def DumpMeta(data_class: Type[T],
             debug_enabled: bool = False,
             marshal_date_time_as: Union[DateTimeTo, str] = None,
             key_transform: Union[LetterCase, str] = None) -> M:
    """
    Helper function to setup the ``Meta`` Config for the JSON dump
    (serialization) process, which is intended for use alongside the
    ``asdict`` helper function.

    For descriptions on what each of these params does, refer to the `Docs`_
    below, or check out the :class:`BaseMeta` definition (I want to avoid
    duplicating the descriptions for params here).

    Examples::

        >>> asdict(MyClass, {"myStr": "value"}, \
                   DumpMeta(MyClass, key_transform='CAMEL'))

    .. _Docs: https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/meta.html
    """
    try:
        return _DUMP_META[data_class]

    except KeyError:
        # Initial run - we have not set up the dump config for the class yet

        try:
            cls_meta = _META[data_class]
        except KeyError:
            # Meta does not exist for the class. Create a new subclass of
            # :class:`BaseMeta`, and cache it so we have it for next time
            # (for example for the dump or serialization process).
            cls_meta = create_new_class(
                data_class, (BaseJSONWizardMeta, ), suffix='Meta')

        # Set meta attributes here.
        cls_meta.debug_enabled |= debug_enabled
        cls_meta.marshal_date_time_as = marshal_date_time_as
        cls_meta.key_transform_with_dump = key_transform

        # Run the meta initialization for the dataclass, and also save the
        # mapping to `_META` so we have it for next time.
        # noinspection PyProtectedMember
        cls_meta._meta_initialize(data_class)

        # Save the dump config, so we don't have to run this logic each time.
        _DUMP_META[data_class] = cls_meta
