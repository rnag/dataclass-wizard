__all__ = [
    'PyForwardRef',
    'PyLiteral',
    'PyProtocol',
    'PyDeque',
    'PyTypedDict',
    'PyTypedDicts',
    'PyRequired',
    'PyNotRequired',
    'FrozenKeys',
    'DefFactory',
    'NoneType',
    'ExplicitNullType',
    'ExplicitNull',
    'JSONList',
    'JSONObject',
    'ListOfJSONObject',
    'JSONValue',
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
]

from collections import deque
from datetime import date, time, datetime
from enum import Enum
from typing import (
    Any, Type, TypeVar, Sequence, Mapping, List, Dict, DefaultDict, FrozenSet,
    Union, NamedTuple, Callable, AnyStr, TextIO, BinaryIO,
    Deque as PyDeque,
    ForwardRef as PyForwardRef,
    Literal as PyLiteral,
    Protocol as PyProtocol,
    TypedDict as PyTypedDict,
)
from uuid import UUID

from .constants import PY311_OR_ABOVE


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
DD = TypeVar('DD', bound=DefaultDict)

# Numeric type
N = Union[int, float]

# Sequence type
S = TypeVar('S', bound=Sequence)

# List or Tuple type
LT = TypeVar('LT', list, tuple)

# List, Set, or Deque (Double ended queue) type
LSQ = TypeVar('LSQ', list, set, frozenset, deque)

# A fixed set of key names
FrozenKeys = FrozenSet[str]

# Default factory type, assuming a no-args constructor
DefFactory = Callable[[], T]

# The class of the `None` singleton, cached for re-usability
NoneType = type(None)

# For Python 3.8+, we need to use both `TypedDict` implementations (from both
# the `typing` and `typing_extensions` modules). Because it's not clear which
# version users might choose to use. And they might choose to use either, due
# to the issues mentioned below (comment taken from `typing_extensions`):
#
#   The standard library TypedDict in Python 3.8 does not store runtime information
#   about which (if any) keys are optional.  See https://bugs.python.org/issue38834
#   The standard library TypedDict in Python 3.9.0/1 does not honour the "total"
#   keyword with old-style TypedDict().  See https://bugs.python.org/issue42059
PyTypedDicts: List[Type['TypedDict']] = []

# Valid collection types in JSON.
JSONList = List[Any]
JSONObject = Dict[str, Any]
ListOfJSONObject = List[JSONObject]

# Valid value types in JSON.
JSONValue = Union[None, str, bool, int, float, JSONList, JSONObject]


PyTypedDicts.append(PyTypedDict)
# Python 3.9+ users might import from either `typing` or
# `typing_extensions`, so check for both types.
try:  # pragma: no cover
    # noinspection PyUnresolvedReferences
    from typing_extensions import TypedDict as PyTypedDict
    PyTypedDicts.append(PyTypedDict)
except ImportError:
    pass

# Python 3.11 introduced `Required` and `NotRequired` wrappers for
# `TypedDict` fields (PEP 655). Python 3.9+ users can import the
# wrappers from `typing_extensions`.
if PY311_OR_ABOVE:  # pragma: no cover
    from typing import Required as PyRequired
    from typing import NotRequired as PyNotRequired
else:
    from typing_extensions import Required as PyRequired
    from typing_extensions import NotRequired as PyNotRequired


# Forward references can be either strings or explicit `ForwardRef` objects.
# noinspection SpellCheckingInspection
FREF = TypeVar('FREF', str, PyForwardRef)


class ExplicitNullType:
    __slots__ = ()  # Saves memory by preventing the creation of instance dictionaries

    _instance = None  # Class-level instance variable for singleton control

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
