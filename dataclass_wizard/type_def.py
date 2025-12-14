__all__ = [
    'Buffer',
    'PyForwardRef',
    'PyProtocol',
    'PyDeque',
    'PyTypedDict',
    'PyRequired',
    'PyNotRequired',
    'PyReadOnly',
    'PyLiteralString',
    'FrozenKeys',
    'DefFactory',
    'NoneType',
    'ExplicitNullType',
    'ExplicitNull',
    'JSONList',
    'JSONObject',
    'ListOfJSONObject',
    'JSONValue',
    'FileType',
    'EnvFileType',
    'StrCollection',
    'ParseFloat',
    'Encoder',
    'FileEncoder',
    'Decoder',
    'FileDecoder',
    'NUMBERS',
    'T',
    'E',
    'U',
    'M',
    'NT',
    'DT',
    'DD',
    'N',
    'S',
    'LT',
    'LSQ',
    'FREF',
    'dataclass_transform',
]

from collections import deque, defaultdict
from datetime import date, time, datetime
from enum import Enum
from os import PathLike
from typing import (
    Any, TypeVar, Sequence, Mapping,
    Union, NamedTuple, Callable, AnyStr, TextIO, BinaryIO,
    Deque as PyDeque,
    ForwardRef as PyForwardRef,
    Protocol as PyProtocol,
    TypedDict as PyTypedDict, Iterable, Collection,
)
from uuid import UUID

from .constants import PY310_OR_ABOVE, PY311_OR_ABOVE, PY313_OR_ABOVE, PY312_OR_ABOVE

# The class of the `None` singleton, cached for re-usability
if PY310_OR_ABOVE:
    # https://docs.python.org/3/library/types.html#types.NoneType
    from types import NoneType
else:
    # "Cannot assign to a type"
    NoneType = type(None)  # type: ignore[misc]

# Type check for numeric types - needed because `bool` is technically
# a Number.
NUMBERS = int, float

# Generic type
T = TypeVar('T')
TT = TypeVar('TT')

# Enum subclass type
E = TypeVar('E', bound=Enum)

# UUID subclass type
U = TypeVar('U', bound=UUID)

# Mapping type
M = TypeVar('M', bound=Mapping)

# NamedTuple type
NT = TypeVar('NT', bound=NamedTuple)

# Date, time, or datetime type
DT = TypeVar('DT', date, time, datetime)

# DefaultDict type
DD = TypeVar('DD', bound=defaultdict)

# Numeric type
N = Union[int, float]

# Sequence type
S = TypeVar('S', bound=Sequence)

# List or Tuple type
LT = TypeVar('LT', list, tuple)

# List, Set, or Deque (Double ended queue) type
LSQ = TypeVar('LSQ', list, set, frozenset, deque)

# A fixed set of key names
FrozenKeys = frozenset[str]

# Default factory type, assuming a no-args constructor
DefFactory = Callable[[], T]

# Valid collection types in JSON.
JSONList = list[Any]
JSONObject = dict[str, Any]
ListOfJSONObject = list[JSONObject]

# Valid value types in JSON.
JSONValue = Union[None, str, bool, int, float, JSONList, JSONObject]

# File-type argument, compatible with the type of `file` for `open`
FileType = Union[str, bytes, PathLike, int]

# DotEnv file-type argument (string, tuple of string, boolean, or None)
EnvFileType = Union[bool, FileType, Iterable[FileType], None]

# Type for a string or a collection of strings.
StrCollection = Union[str, Collection[str]]

# Python 3.11 introduced `Required` and `NotRequired` wrappers for
# `TypedDict` fields (PEP 655). Python 3.9+ users can import the
# wrappers from `typing_extensions`.

if PY313_OR_ABOVE:  # pragma: no cover
    from collections.abc import Buffer

    from typing import (Required as PyRequired,
                        NotRequired as PyNotRequired,
                        ReadOnly as PyReadOnly,
                        LiteralString as PyLiteralString,
                        dataclass_transform)
elif PY311_OR_ABOVE:  # pragma: no cover
    if PY312_OR_ABOVE:
        from collections.abc import Buffer
    else:
        from typing_extensions import Buffer

    from typing import (Required as PyRequired,
                        NotRequired as PyNotRequired,
                        LiteralString as PyLiteralString,
                        dataclass_transform)
    from typing_extensions import ReadOnly as PyReadOnly
else:
    from typing_extensions import (Buffer,
                                   Required as PyRequired,
                                   NotRequired as PyNotRequired,
                                   ReadOnly as PyReadOnly,
                                   LiteralString as PyLiteralString,
                                   dataclass_transform)

# Forward references can be either strings or explicit `ForwardRef` objects.
# noinspection SpellCheckingInspection
FREF = TypeVar('FREF', str, PyForwardRef)


class ExplicitNullType:
    __slots__ = ()  # Saves memory by preventing the creation of instance dictionaries

    # Class-level instance variable for singleton control
    _instance: "ExplicitNullType | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ExplicitNullType, cls).__new__(cls)
        return cls._instance

    def __bool__(self):
        return False

    def __repr__(self):
        return '<ExplicitNull>'


# Create the singleton instance
ExplicitNull = ExplicitNullType()

# Type annotations
ParseFloat = Callable[[str], Any]


class Encoder(PyProtocol):
    """
    Represents an encoder for Python object -> JSON, e.g. analogous to
    `json.dumps`
    """

    def __call__(self, obj: Union[JSONObject, JSONList],
                 /,
                 *args,
                 **kwargs) -> AnyStr:
        ...


class FileEncoder(PyProtocol):
    """
    Represents an encoder for Python object -> JSON file, e.g. analogous to
    `json.dump`
    """

    def __call__(self, obj: Union[JSONObject, JSONList],
                 file: Union[TextIO, BinaryIO],
                 **kwargs) -> AnyStr:
        ...


class Decoder(PyProtocol):
    """
    Represents a decoder for JSON -> Python object, e.g. analogous to
    `json.loads`
    """

    def __call__(self, s: AnyStr,
                 **kwargs) -> Union[JSONObject, ListOfJSONObject]:
        ...


class FileDecoder(PyProtocol):
    """
    Represents a decoder for JSON file -> Python object, e.g. analogous to
    `json.load`
    """
    def __call__(self, file: Union[TextIO, BinaryIO],
                 **kwargs) -> Union[JSONObject, ListOfJSONObject]:
        ...
