from typing import Callable, Type, Dict, Optional, ClassVar, Union, TypeVar

from .enums import DateTimeTo, LetterCase


# Create a generic variable that can be 'BaseMeta', or any subclass.
M = TypeVar('M', bound='BaseMeta')


class BaseMeta:
    """
    Base class definition for the `JSONWizard.Meta` inner class.
    """
    __slots__ = ()

    # True to enable Debug mode for additional (more verbose) log output.
    #
    # For example, a message is logged whenever an unknown JSON key is
    # encountered when `from_dict` or `from_json` is called.
    #
    # This also results in more helpful messages during error handling, which
    # can be useful when debugging the cause when values are an invalid type
    # (i.e. they don't match the annotation for the field) when unmarshalling
    # a JSON object to a dataclass instance.
    #
    # Note there is a minor performance impact when DEBUG mode is enabled.
    debug_enabled: ClassVar[bool] = False

    # True to raise an class:`UnknownJSONKey` when an unmapped JSON key is
    # encountered when `from_dict` or `from_json` is called; an unknown key is
    # one that does not have a known mapping to a dataclass field.
    #
    # The default is to only log a "warning" for such cases, which is visible
    # when `debug_enabled` is true and logging is properly configured.
    raise_on_unknown_json_key: ClassVar[bool] = False

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


class BaseLoadHook:
    """
    Container class for type hooks.
    """
    __slots__ = ()

    __LOAD_HOOKS__: ClassVar[Dict[Type, Callable]] = None

    def __init_subclass__(cls):
        super().__init_subclass__()
        # (Re)assign the dict object so we have a fresh copy per class
        cls.__LOAD_HOOKS__ = {}

    @classmethod
    def register_load_hook(cls, typ: Type, func: Callable):
        """Registers the hook for a type, on the default loader by default."""
        cls.__LOAD_HOOKS__[typ] = func

    @classmethod
    def get_load_hook(cls, typ: Type) -> Optional[Callable]:
        """Retrieves the hook for a type, if one exists."""
        return cls.__LOAD_HOOKS__.get(typ)


class BaseDumpHook:
    """
    Container class for type hooks.
    """
    __slots__ = ()

    __DUMP_HOOKS__: ClassVar[Dict[Type, Callable]] = None

    def __init_subclass__(cls):
        super().__init_subclass__()
        # (Re)assign the dict object so we have a fresh copy per class
        cls.__DUMP_HOOKS__ = {}

    @classmethod
    def register_dump_hook(cls, typ: Type, func: Callable):
        """Registers the hook for a type, on the default dumper by default."""
        cls.__DUMP_HOOKS__[typ] = func

    @classmethod
    def get_dump_hook(cls, typ: Type) -> Optional[Callable]:
        """Retrieves the hook for a type, if one exists."""
        return cls.__DUMP_HOOKS__.get(typ)
