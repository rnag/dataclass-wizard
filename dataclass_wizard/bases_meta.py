"""
Ideally should be in the `bases` module, however we'll run into a Circular
Import scenario if we move it there, since the `loaders` and `dumpers` modules
both import directly from `bases`.

"""
from datetime import datetime, date
from typing import ClassVar, Type, Union, Optional, Dict

from .abstractions import W, AbstractJSONWizard
from .class_helper import (
    _META_INITIALIZER, get_outer_class_name, get_class_name, create_new_class,
    json_field_to_dataclass_field, dataclass_field_to_json_field
)
from .decorators import try_with_load
from .dumpers import get_dumper
from .enums import LetterCase, DateTimeTo
from .errors import ParseError
from .loaders import get_loader
from .log import LOG
from .type_def import E
from .utils.type_conv import date_to_timestamp, as_enum


class BaseJSONWizardMeta:
    __slots__ = ()

    # True to enable Debug mode for additional debug log output and more
    # helpful messages during error handling.
    debug_enabled: ClassVar[bool] = False

    # A customized mapping of JSON keys to dataclass fields, that is used
    # whenever `from_dict` or `from_json` is called.
    #
    # Note: this is in addition to the implicit field transformations, like
    #   "myStr" -> "my_str"
    #
    # If the reverse mapping is also desired (i.e. dataclass field to JSON
    # key), then specify the "__all__" key as a truthy value. If multiple JSON
    # keys are specified for a dataclass field, only the first one provided is
    # used in this case.
    json_key_to_field: ClassVar[Dict[str, str]] = None

    # How should :class:`time` and :class:`datetime` objects be serialized
    # when converted to a Python dictionary object or a JSON string.
    marshal_date_time_as: ClassVar[Union[DateTimeTo, str]] = None

    # How JSON keys should be transformed to dataclass fields.
    #
    # Note that this only applies to keys which are to be set on dataclass
    # fields; other fields such as the ones for `TypedDict` or `NamedTuple`
    # sub-classes won't be similarly transformed.
    key_transform_with_load: ClassVar[Union[LetterCase, str]] = None

    # How dataclass fields should be transformed to JSON keys.
    #
    # Note that this only applies to dataclass fields; other fields such as
    # the ones for `TypedDict` or `NamedTuple` sub-classes won't be similarly
    # transformed.
    key_transform_with_dump: ClassVar[Union[LetterCase, str]] = None

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
