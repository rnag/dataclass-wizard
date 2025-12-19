"""
Contains implementations for Abstract Base Classes
"""
import json

from abc import ABC, abstractmethod
from dataclasses import dataclass, InitVar, Field
from typing import Type, TypeVar, Dict, Generic

from .models import Extras
from .v1.models import Extras as V1Extras, TypeInfo
from .type_def import T, TT


# Create a generic variable that can be 'AbstractJSONWizard', or any subclass.
W = TypeVar('W', bound='AbstractJSONWizard')


class AbstractEnvWizard(ABC):
    """
    Abstract class that defines the methods a sub-class must implement at a
    minimum to be considered a "true" Environment Wizard.
    """
    __slots__ = ()

    # Extends the `__annotations__` attribute to return only the fields
    # (variables) of the `EnvWizard` subclass.
    #
    # .. NOTE::
    #    This excludes fields marked as ``ClassVar``, or ones which are
    #    not type-annotated.
    __fields__: dict[str, Field]

    def dict(self):
        ...

    @abstractmethod
    def to_dict(self):
        ...

    @abstractmethod
    def to_json(self, indent=None):
        ...


class AbstractJSONWizard(ABC):

    __slots__ = ()

    @classmethod
    @abstractmethod
    def from_json(cls, string):
        ...

    @classmethod
    @abstractmethod
    def from_list(cls, o):
        ...

    @classmethod
    @abstractmethod
    def from_dict(cls, o):
        ...

    @abstractmethod
    def to_dict(self):
        ...

    @abstractmethod
    def to_json(self, *,
                encoder=json.dumps,
                indent=None,
                **encoder_kwargs):
        ...

    @classmethod
    @abstractmethod
    def list_to_json(cls,
                     instances,
                     encoder=json.dumps,
                     indent=None,
                     **encoder_kwargs):
        ...


@dataclass
class AbstractParser(ABC, Generic[T, TT]):

    __slots__ = ('base_type', )

    # Please see `abstractions.pyi` for documentation on each field.

    cls: InitVar[Type]
    extras: InitVar[Extras]
    base_type: type[T]

    def __contains__(self, item):
        return type(item) is self.base_type

    @abstractmethod
    def __call__(self, o) -> TT:
        ...


class AbstractLoader(ABC):

    __slots__ = ()

    @staticmethod
    @abstractmethod
    def transform_json_field(string):
        ...

    @staticmethod
    @abstractmethod
    def default_load_to(o, _):
        ...

    @staticmethod
    @abstractmethod
    def load_after_type_check(o, base_type):
        ...

    @staticmethod
    @abstractmethod
    def load_to_str(o, base_type):
        ...

    @staticmethod
    @abstractmethod
    def load_to_int(o, base_type):
        ...

    @staticmethod
    @abstractmethod
    def load_to_float(o, base_type):
        ...

    @staticmethod
    @abstractmethod
    def load_to_bool(o, _):
        ...

    @staticmethod
    @abstractmethod
    def load_to_enum(o, base_type):
        ...

    @staticmethod
    @abstractmethod
    def load_to_uuid(o, base_type):
        ...

    @staticmethod
    @abstractmethod
    def load_to_iterable(
            o, base_type,
            elem_parser):
        ...

    @staticmethod
    @abstractmethod
    def load_to_tuple(
            o, base_type,
            elem_parsers):
        ...

    @staticmethod
    @abstractmethod
    def load_to_named_tuple(
            o, base_type,
            field_to_parser,
            field_parsers):
        ...

    @staticmethod
    @abstractmethod
    def load_to_named_tuple_untyped(
            o, base_type,
            dict_parser, list_parser):
        ...

    @staticmethod
    @abstractmethod
    def load_to_dict(
            o, base_type,
            key_parser,
            val_parser):
        ...

    @staticmethod
    @abstractmethod
    def load_to_defaultdict(
            o, base_type,
            default_factory,
            key_parser,
            val_parser):
        ...

    @staticmethod
    @abstractmethod
    def load_to_typed_dict(
            o, base_type,
            key_to_parser,
            required_keys,
            optional_keys):
        ...

    @staticmethod
    @abstractmethod
    def load_to_decimal(o, base_type):
        ...

    @staticmethod
    @abstractmethod
    def load_to_datetime(o, base_type):
        ...

    @staticmethod
    @abstractmethod
    def load_to_time(o, base_type):
        ...

    @staticmethod
    @abstractmethod
    def load_to_date(o, base_type):
        ...

    @staticmethod
    @abstractmethod
    def load_to_timedelta(o, base_type):
        ...

    # @staticmethod
    # @abstractmethod
    # def load_func_for_dataclass(
    #     cls: Type[T],
    #     config: Optional[META],
    # ) -> Callable[[JSONObject], T]:
    #     """
    #     Generate and return the load function for a (nested) dataclass of
    #     type `cls`.
    #     """

    @classmethod
    @abstractmethod
    def get_parser_for_annotation(cls, ann_type,
                                  base_cls=None,
                                  extras=None):
        ...


class AbstractDumper(ABC):
    __slots__ = ()


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
    def default_load_to(tp: TypeInfo, extras: V1Extras) -> str:
        """
        Generate code for the default load function if no other types match.
        Generally, this will be a stub load method.
        """

    @staticmethod
    @abstractmethod
    def load_to_str(tp: TypeInfo, extras: V1Extras) -> str:
        """
        Generate code to load a value into a string field.
        """

    @staticmethod
    @abstractmethod
    def load_to_int(tp: TypeInfo, extras: V1Extras) -> str:
        """
        Generate code to load a value into an integer field.
        """

    @staticmethod
    @abstractmethod
    def load_to_float(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to load a value into a float field.
        """

    @staticmethod
    @abstractmethod
    def load_to_bool(_: str, extras: V1Extras) -> str:
        """
        Generate code to load a value into a boolean field.
        Adds a helper function `as_bool` to the local context.
        """

    @staticmethod
    @abstractmethod
    def load_to_bytes(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to load a value into a bytes field.
        """

    @staticmethod
    @abstractmethod
    def load_to_bytearray(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to load a value into a bytearray field.
        """

    @staticmethod
    @abstractmethod
    def load_to_none(tp: TypeInfo, extras: V1Extras) -> str:
        """
        Generate code to load a value into a None.
        """

    @staticmethod
    @abstractmethod
    def load_to_literal(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to confirm a value is equivalent to one
        of the provided literals.
        """

    @classmethod
    @abstractmethod
    def load_to_union(cls, tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to load a value into a `Union[X, Y, ...]` (one of [X, Y, ...] possible types)
        """

    @staticmethod
    @abstractmethod
    def load_to_enum(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to load a value into an Enum field.
        """

    @staticmethod
    @abstractmethod
    def load_to_uuid(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to load a value into a UUID field.
        """

    @staticmethod
    @abstractmethod
    def load_to_iterable(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to load a value into an iterable field (list, set, etc.).
        """

    @staticmethod
    @abstractmethod
    def load_to_tuple(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to load a value into a tuple field.
        """

    @staticmethod
    @abstractmethod
    def load_to_named_tuple(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to load a value into a named tuple field.
        """

    @classmethod
    @abstractmethod
    def load_to_named_tuple_untyped(cls, tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to load a value into an untyped named tuple.
        """

    @staticmethod
    @abstractmethod
    def load_to_dict(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to load a value into a dictionary field.
        """

    @staticmethod
    @abstractmethod
    def load_to_defaultdict(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to load a value into a defaultdict field.
        """

    @staticmethod
    @abstractmethod
    def load_to_typed_dict(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to load a value into a typed dictionary field.
        """

    @staticmethod
    @abstractmethod
    def load_to_decimal(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to load a value into a Decimal field.
        """

    @staticmethod
    @abstractmethod
    def load_to_path(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to load a value into a Decimal field.
        """

    @staticmethod
    @abstractmethod
    def load_to_datetime(tp: TypeInfo, extras: V1Extras) -> str:
        """
        Generate code to load a value into a datetime field.
        """

    @staticmethod
    @abstractmethod
    def load_to_time(tp: TypeInfo, extras: V1Extras) -> str:
        """
        Generate code to load a value into a time field.
        """

    @staticmethod
    @abstractmethod
    def load_to_date(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to load a value into a date field.
        """

    @staticmethod
    @abstractmethod
    def load_to_timedelta(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to load a value into a timedelta field.
        """

    @staticmethod
    def load_to_dataclass(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to load a value into a `dataclass` type field.
        """

    @classmethod
    @abstractmethod
    def load_dispatcher_for_annotation(cls,
                                       tp: TypeInfo,
                                       extras: V1Extras) -> 'str | TypeInfo':
        """
        Resolve the load dispatcher for a given annotation type.

        Returns either a string reference to a dispatcher or a TypeInfo object,
        depending on how the annotation is handled.

        `base_cls` is the original class object, useful when the annotated
        type is a :class:`typing.ForwardRef` object.
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
    def default_dump_from(tp: TypeInfo, extras: V1Extras) -> str:
        """
        Generate code for the default dump function if no other types match.
        Generally, this will be a stub dump method.
        """

    @staticmethod
    @abstractmethod
    def dump_from_str(tp: TypeInfo, extras: V1Extras) -> str:
        """
        Generate code to dump a value from a string field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_int(tp: TypeInfo, extras: V1Extras) -> str:
        """
        Generate code to dump a value from an integer field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_float(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a float field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_bool(_: str, extras: V1Extras) -> str:
        """
        Generate code to dump a value from a boolean field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_bytes(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a bytes field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_bytearray(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a bytearray field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_none(tp: TypeInfo, extras: V1Extras) -> str:
        """
        Generate code to dump a value from a None.
        """

    @staticmethod
    @abstractmethod
    def dump_from_literal(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a literal.
        """

    @classmethod
    @abstractmethod
    def dump_from_union(cls, tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a `Union[X, Y, ...]` (one of [X, Y, ...] possible types)
        """

    @staticmethod
    @abstractmethod
    def dump_from_enum(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from an Enum field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_uuid(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a UUID field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_iterable(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from an iterable field (list, set, etc.).
        """

    @staticmethod
    @abstractmethod
    def dump_from_tuple(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a tuple field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_named_tuple(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a named tuple field.
        """

    @classmethod
    @abstractmethod
    def dump_from_named_tuple_untyped(cls, tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from an untyped named tuple.
        """

    @staticmethod
    @abstractmethod
    def dump_from_dict(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a dictionary field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_defaultdict(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a defaultdict field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_typed_dict(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a typed dictionary field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_decimal(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a Decimal field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_path(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a Decimal field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_datetime(tp: TypeInfo, extras: V1Extras) -> str:
        """
        Generate code to dump a value from a datetime field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_time(tp: TypeInfo, extras: V1Extras) -> str:
        """
        Generate code to dump a value from a time field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_date(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a date field.
        """

    @staticmethod
    @abstractmethod
    def dump_from_timedelta(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a timedelta field.
        """

    @staticmethod
    def dump_from_dataclass(tp: TypeInfo, extras: V1Extras) -> 'str | TypeInfo':
        """
        Generate code to dump a value from a `dataclass` type field.
        """

    @classmethod
    @abstractmethod
    def dump_dispatcher_for_annotation(cls,
                                       tp: TypeInfo,
                                       extras: V1Extras) -> 'str | TypeInfo':
        """
        Resolve the dump dispatcher for a given annotation type.

        Returns either a string reference to a dispatcher or a TypeInfo object,
        depending on how the annotation is handled.

        `base_cls` is the original class object, useful when the annotated
        type is a :class:`typing.ForwardRef` object.
        """
