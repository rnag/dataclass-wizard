"""
Contains implementations for Abstract Base Classes
"""
import json
from abc import ABC, abstractmethod
from typing import AnyStr, TypeVar, ClassVar

from .models import Extras, TypeInfo
from .type_def import Encoder, JSONObject, ListOfJSONObject


# Create a generic variable that can be 'AbstractEnvWizard', or any subclass.
E = TypeVar('E', bound='AbstractEnvWizard')

# Create a generic variable that can be 'AbstractJSONWizard', or any subclass.
W = TypeVar('W', bound='AbstractJSONWizard')


class AbstractEnvWizard(ABC):
    """
    Abstract class that defines the methods a sub-class must implement at a
    minimum to be considered a "true" Environment Wizard.
    """
    __slots__ = ()

    # Extends the `__annotations__` attribute to return only the field
    # names of the `EnvWizard` subclass.
    #
    # .. NOTE::
    #    This excludes fields marked as ``ClassVar``, or ones which are
    #    not type-annotated.
    __field_names__: ClassVar[tuple[str, ...]]

    def raw_dict(self: E) -> JSONObject:
        """
        Same as ``__dict__``, but only returns values for fields defined
        on the `EnvWizard` instance. See :attr:`__field_names__` for more info.

        .. NOTE::
           The values in the returned dictionary object are not needed to be
           JSON serializable. Use :meth:`to_dict` if this is required.
        """

    @abstractmethod
    def to_dict(self: E) -> JSONObject:
        """
        Converts an instance of a `EnvWizard` subclass to a Python dictionary
        object that is JSON serializable.
        """

    @abstractmethod
    def to_json(self: E, indent=None) -> AnyStr:
        """
        Converts an instance of a `EnvWizard` subclass to a JSON `string`
        representation.
        """


class AbstractJSONWizard(ABC):
    """
    Abstract class that defines the methods a sub-class must implement at a
    minimum to be considered a "true" JSON Wizard.

    In particular, these are the abstract methods which - if correctly
    implemented - will allow a concrete sub-class (ideally a dataclass) to
    be properly loaded from, and serialized to, JSON.

    """
    __slots__ = ()

    @classmethod
    @abstractmethod
    def from_json(cls: type[W], string: AnyStr) -> W | list[W]:
        """
        Converts a JSON `string` to an instance of the dataclass, or a list of
        the dataclass instances.
        """

    @classmethod
    @abstractmethod
    def from_list(cls: type[W], o: ListOfJSONObject) -> list[W]:
        """
        Converts a Python `list` object to a list of the dataclass instances.
        """

    @classmethod
    @abstractmethod
    def from_dict(cls: type[W], o: JSONObject) -> W:
        """
        Converts a Python `dict` object to an instance of the dataclass.
        """

    @abstractmethod
    def to_dict(self: W) -> JSONObject:
        """
        Converts the dataclass instance to a Python dictionary object that is
        JSON serializable.
        """

    @abstractmethod
    def to_json(self: W, *,
                encoder: Encoder = json.dumps,
                indent=None,
                **encoder_kwargs) -> str:
        """
        Converts the dataclass instance to a JSON `string` representation.
        """

    @classmethod
    @abstractmethod
    def list_to_json(cls: type[W],
                     instances: list[W],
                     encoder: Encoder = json.dumps,
                     **encoder_kwargs) -> str:
        """
        Converts a ``list`` of dataclass instances to a JSON `string`
        representation.
        """


class AbstractLoaderGenerator(ABC):
    """
    Abstract code generator which defines helper methods to generate the
    code for deserializing an object `o` of a given annotated type into
    the corresponding dataclass field during dynamic function construction.
    """
    __slots__ = ()

    @staticmethod
    @abstractmethod
    def transform_json_field(string: str) -> str:
        """
        Transform a JSON field name (which will typically be camel-cased)
        into the conventional format for a dataclass field name
        (which will ideally be snake-cased).
        """

    @staticmethod
    @abstractmethod
    def is_none(tp: TypeInfo, extras: Extras) -> str:
        """
        Generate the condition to determine if a value is None.
        """

    @staticmethod
    @abstractmethod
    def load_fallback(tp: TypeInfo, extras: Extras) -> str:
        """
        Generate code for the fallback load handler when no specialized type matches.

        The default fallback implementation is typically an identity / passthrough,
        but subclasses may override this behavior.
        """

    @staticmethod
    @abstractmethod
    def load_to_str(tp: TypeInfo, extras: Extras) -> str:
        """
        Generate code to load a value into a string field.
        """

    @staticmethod
    @abstractmethod
    def load_to_int(tp: TypeInfo, extras: Extras) -> str:
        """
        Generate code to load a value into an integer field.
        """

    @staticmethod
    @abstractmethod
    def load_to_float(tp: TypeInfo, extras: Extras) -> str | TypeInfo:
        """
        Generate code to load a value into a float field.
        """

    @staticmethod
    @abstractmethod
    def load_to_bool(_: str, extras: Extras) -> str:
        """
        Generate code to load a value into a boolean field.
        Adds a helper function `as_bool` to the local context.
        """

    @staticmethod
    @abstractmethod
    def load_to_bytes(tp: TypeInfo, extras: Extras) -> str | TypeInfo:
        """
        Generate code to load a value into a bytes field.
        """

    @staticmethod
    @abstractmethod
    def load_to_bytearray(tp: TypeInfo, extras: Extras) -> str | TypeInfo:
        """
        Generate code to load a value into a bytearray field.
        """

    @staticmethod
    @abstractmethod
    def load_to_none(tp: TypeInfo, extras: Extras) -> str:
        """
        Generate code to load a value into a None.
        """

    @staticmethod
    @abstractmethod
    def load_to_literal(tp: TypeInfo, extras: Extras) -> str | TypeInfo:
        """
        Generate code to confirm a value is equivalent to one
        of the provided literals.
        """

    @classmethod
    @abstractmethod
    def load_to_union(cls, tp: TypeInfo, extras: Extras) -> str | TypeInfo:
        """
        Generate code to load a value into a `Union[X, Y, ...]` (one of [X, Y, ...] possible types)
        """

    @staticmethod
    @abstractmethod
    def load_to_enum(tp: TypeInfo, extras: Extras) -> str | TypeInfo:
        """
        Generate code to load a value into an Enum field.
        """

    @staticmethod
    @abstractmethod
    def load_to_uuid(tp: TypeInfo, extras: Extras) -> str | TypeInfo:
        """
        Generate code to load a value into a UUID field.
        """

    @staticmethod
    @abstractmethod
    def load_to_iterable(tp: TypeInfo, extras: Extras) -> str | TypeInfo:
        """
        Generate code to load a value into an iterable field (list, set, etc.).
        """

    @staticmethod
    @abstractmethod
    def load_to_tuple(tp: TypeInfo, extras: Extras) -> str | TypeInfo:
        """
        Generate code to load a value into a tuple field.
        """

    @classmethod
    @abstractmethod
    def load_to_named_tuple(cls, tp: TypeInfo, extras: Extras) -> str | TypeInfo:
        """
        Generate code to load a value into a named tuple field.
        """

    @classmethod
    @abstractmethod
    def load_to_named_tuple_untyped(cls, tp: TypeInfo, extras: Extras) -> str | TypeInfo:
        """
        Generate code to load a value into an untyped named tuple.
        """

    @staticmethod
    @abstractmethod
    def load_to_dict(tp: TypeInfo, extras: Extras) -> str | TypeInfo:
        """
        Generate code to load a value into a dictionary field.
        """

    @staticmethod
    @abstractmethod
    def load_to_defaultdict(tp: TypeInfo, extras: Extras) -> str | TypeInfo:
        """
        Generate code to load a value into a defaultdict field.
        """

    @staticmethod
    @abstractmethod
    def load_to_typed_dict(tp: TypeInfo, extras: Extras) -> str | TypeInfo:
        """
        Generate code to load a value into a typed dictionary field.
        """

    @staticmethod
    @abstractmethod
    def load_to_decimal(tp: TypeInfo, extras: Extras) -> str | TypeInfo:
        """
        Generate code to load a value into a Decimal field.
        """

    @staticmethod
    @abstractmethod
    def load_to_path(tp: TypeInfo, extras: Extras) -> str | TypeInfo:
        """
        Generate code to load a value into a Path field.
        """

    @staticmethod
    @abstractmethod
    def load_to_date(tp: TypeInfo, extras: Extras) -> str | TypeInfo:
        """
        Generate code to load a value into a date field.
        """

    @staticmethod
    @abstractmethod
    def load_to_datetime(tp: TypeInfo, extras: Extras) -> str | TypeInfo:
        """
        Generate code to load a value into a datetime field.
        """

    @staticmethod
    @abstractmethod
    def load_to_time(tp: TypeInfo, extras: Extras) -> str:
        """
        Generate code to load a value into a time field.
        """

    @staticmethod
    @abstractmethod
    def load_to_timedelta(tp: TypeInfo, extras: Extras) -> str | TypeInfo:
        """
        Generate code to load a value into a timedelta field.
        """

    @staticmethod
    def load_to_dataclass(tp: TypeInfo, extras: Extras) -> str | TypeInfo:
        """
        Generate code to load a value into a `dataclass` type field.
        """

    @classmethod
    @abstractmethod
    def load_dispatcher_for_annotation(cls,
                                       tp: TypeInfo,
                                       extras: Extras) -> str | TypeInfo:
        """
        Resolve the load dispatcher for a given annotation type.

        Returns either a string reference to a dispatcher or a TypeInfo object,
        depending on how the annotation is handled.
        """


class AbstractDumperGenerator(ABC):
    """
    Abstract code generator which defines helper methods to generate the
    code for deserializing an object `o` of a given annotated type into
    the corresponding dataclass field during dynamic function construction.
    """
    __slots__ = ()

    @staticmethod
    @abstractmethod
    def transform_dataclass_field(string: str) -> str:
        """
        Transform a dataclass field name (which will ideally be snake-cased)
        into the conventional format for a JSON field name.
        """

    @staticmethod
    @abstractmethod
    def dump_fallback(tp: TypeInfo, extras: Extras) -> str:
        """
        Generate code for the fallback dump handler when no specialized type matches.

        The default fallback implementation is typically an identity / passthrough,
        but subclasses may override this behavior.
        """

    @staticmethod
    @abstractmethod
    def dump_from_str(tp: TypeInfo, extras: Extras) -> str:
        """
        Generate code to dump a value from a string field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_int(tp: TypeInfo, extras: Extras) -> str:
        """
        Generate code to dump a value from an integer field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_float(tp: TypeInfo, extras: Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a float field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_bool(_: str, extras: Extras) -> str:
        """
        Generate code to dump a value from a boolean field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_bytes(tp: TypeInfo, extras: Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a bytes field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_bytearray(tp: TypeInfo, extras: Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a bytearray field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_none(tp: TypeInfo, extras: Extras) -> str:
        """
        Generate code to dump a value from a None.
        """

    @staticmethod
    @abstractmethod
    def dump_from_literal(tp: TypeInfo, extras: Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a literal.
        """

    @classmethod
    @abstractmethod
    def dump_from_union(cls, tp: TypeInfo, extras: Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a `Union[X, Y, ...]` (one of [X, Y, ...] possible types)
        """

    @staticmethod
    @abstractmethod
    def dump_from_enum(tp: TypeInfo, extras: Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from an Enum field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_uuid(tp: TypeInfo, extras: Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a UUID field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_iterable(tp: TypeInfo, extras: Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from an iterable field (list, set, etc.).
        """

    @staticmethod
    @abstractmethod
    def dump_from_tuple(tp: TypeInfo, extras: Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a tuple field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_named_tuple(tp: TypeInfo, extras: Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a named tuple field.
        """

    @classmethod
    @abstractmethod
    def dump_from_named_tuple_untyped(cls, tp: TypeInfo, extras: Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from an untyped named tuple.
        """

    @staticmethod
    @abstractmethod
    def dump_from_dict(tp: TypeInfo, extras: Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a dictionary field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_defaultdict(tp: TypeInfo, extras: Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a defaultdict field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_typed_dict(tp: TypeInfo, extras: Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a typed dictionary field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_decimal(tp: TypeInfo, extras: Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a Decimal field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_path(tp: TypeInfo, extras: Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a Decimal field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_datetime(tp: TypeInfo, extras: Extras) -> str:
        """
        Generate code to dump a value from a datetime field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_time(tp: TypeInfo, extras: Extras) -> str:
        """
        Generate code to dump a value from a time field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_date(tp: TypeInfo, extras: Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a date field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_timedelta(tp: TypeInfo, extras: Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a timedelta field.
        """

    @staticmethod
    def dump_from_dataclass(tp: TypeInfo, extras: Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a `dataclass` type field.
        """

    @classmethod
    @abstractmethod
    def dump_dispatcher_for_annotation(cls,
                                       tp: TypeInfo,
                                       extras: Extras) -> 'str | TypeInfo':
        """
        Resolve the dump dispatcher for a given annotation type.

        Returns either a string reference to a dispatcher or a TypeInfo object,
        depending on how the annotation is handled.
        """
