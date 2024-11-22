"""
Contains implementations for Abstract Base Classes
"""
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, InitVar
from typing import Type, TypeVar, Dict, Generic

from .models import Extras
from .type_def import T, TT


# Create a generic variable that can be 'AbstractJSONWizard', or any subclass.
W = TypeVar('W', bound='AbstractJSONWizard')

FieldToParser = Dict[str, 'AbstractParser']


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

    @classmethod
    @abstractmethod
    def get_parser_for_annotation(cls, ann_type,
                                  base_cls=None,
                                  extras=None):
        ...


class AbstractDumper(ABC):
    __slots__ = ()
