"""
Ideally should be in the `bases` module, however we'll run into a Circular
Import scenario if we move it there, since the `loaders` and `dumpers` modules
both import directly from `bases`.

"""
from datetime import datetime, date
from typing import ClassVar, Type

from .abstractions import W
from .class_helper import _META_INITIALIZER, get_outer_class_name
from .decorators import try_with_load
from .dumpers import get_dumper
from .enums import LetterCase, DateTimeTo
from .loaders import get_loader
from .log import LOG
from .utils.type_conv import date_to_timestamp


class BaseJSONWizardMeta:

    # How should :class:`time` and :class:`datetime` objects be serialized
    # when converted to a Python dictionary object or a JSON string.
    date_time_with_dump: ClassVar[DateTimeTo] = DateTimeTo.ISO_FORMAT

    # True to enable Debug mode for additional debug log output and more
    # helpful messages during error handling.
    debug_enabled: ClassVar[bool] = False

    # How JSON keys should be transformed to dataclass fields.
    #
    # Note that this only applies to keys which are to be set on dataclass
    # fields; other fields such as the ones for `TypedDict` or `NamedTuple`
    # sub-classes won't be similarly transformed.
    key_transform_with_load: ClassVar[LetterCase] = None

    # How dataclass fields should be transformed to JSON keys.
    #
    # Note that this only applies to dataclass fields; other fields such as
    # the ones for `TypedDict` or `NamedTuple` sub-classes won't be similarly
    # transformed.
    key_transform_with_dump: ClassVar[LetterCase] = None

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

        dt_serialize = cls.date_time_with_dump
        from_dict_transform: LetterCase = cls.key_transform_with_load
        to_dict_transform: LetterCase = cls.key_transform_with_dump
        is_debug_enabled = cls.debug_enabled

        # noop; the default dump hook for `datetime` and `date` already
        # serializes using this approach.
        if dt_serialize is not DateTimeTo.ISO_FORMAT:

            if dt_serialize is DateTimeTo.TIMESTAMP:
                # Update dump hooks for the `datetime` and `date` types
                dumper = get_dumper(outer_cls)
                dumper.register_dump_hook(datetime, lambda o, *_: round(o.timestamp()))
                dumper.register_dump_hook(date, lambda o, *_: date_to_timestamp(o))

        if is_debug_enabled:
            LOG.setLevel('DEBUG')
            LOG.info('DEBUG Mode is enabled')
            # Decorate all hooks so they format more helpful messages
            # on error.
            load_hooks = get_loader(outer_cls).__LOAD_HOOKS__
            for typ in load_hooks:
                load_hooks[typ] = try_with_load(load_hooks[typ])

        if from_dict_transform:
            transform_func = from_dict_transform
            get_loader(outer_cls).transform_json_field = transform_func

        if to_dict_transform:
            transform_func = to_dict_transform
            get_dumper(outer_cls).transform_dataclass_field = transform_func
