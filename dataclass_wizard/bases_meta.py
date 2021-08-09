"""
Ideally should be in the `bases` module, however we'll run into a Circular
Import scenario if we move it there, since the `loaders` and `dumpers` modules
both import directly from `bases`.

"""
from datetime import datetime, date
from typing import ClassVar, Type, Union, Optional

from .abstractions import W
from .class_helper import _META_INITIALIZER, get_outer_class_name, get_class_name
from .decorators import try_with_load
from .dumpers import get_dumper
from .enums import LetterCase, DateTimeTo
from .errors import ParseError
from .loaders import get_loader
from .log import LOG
from .type_def import E
from .utils.type_conv import date_to_timestamp, as_enum


class BaseJSONWizardMeta:

    # How should :class:`time` and :class:`datetime` objects be serialized
    # when converted to a Python dictionary object or a JSON string.
    marshal_date_time_as: ClassVar[Union[DateTimeTo, str]] = None

    # True to enable Debug mode for additional debug log output and more
    # helpful messages during error handling.
    debug_enabled: ClassVar[bool] = False

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

    @classmethod
    def _meta_initialize(cls, outer_cls: Type[W]):
        """
        Initialize hook which is called by the outer class (typically
        a sub-class of :class:`AbstractJSONWizard`)
        """
        cls_loader = get_loader(outer_cls)
        cls_dumper = get_dumper(outer_cls)

        if cls.marshal_date_time_as:
            enum_val = cls._safe_as_enum('marshal_date_time_as', DateTimeTo)

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

        if cls.debug_enabled:

            LOG.setLevel('DEBUG')
            LOG.info('DEBUG Mode is enabled')
            # Decorate all hooks so they format more helpful messages
            # on error.
            load_hooks = cls_loader.__LOAD_HOOKS__
            for typ in load_hooks:
                load_hooks[typ] = try_with_load(load_hooks[typ])

        if cls.key_transform_with_load:

            cls_loader.transform_json_field = cls._safe_as_enum(
                'key_transform_with_load', LetterCase)

        if cls.key_transform_with_dump:

            cls_dumper.transform_dataclass_field = cls._safe_as_enum(
                'key_transform_with_dump', LetterCase)

    @classmethod
    def _safe_as_enum(cls, name: str, base_type: Type[E]) -> Optional[E]:
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
