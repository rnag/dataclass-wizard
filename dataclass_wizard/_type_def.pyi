__all__ = ['Buffer', 'Unpack', 'PyForwardRef', 'PyProtocol', 'PyDeque', 'PyTypedDict', 'PyRequired', 'PyNotRequired', 'PyReadOnly', 'PyLiteralString', 'FrozenKeys', 'DefFactory', 'NoneType', 'ExplicitNullType', 'ExplicitNull', 'JSONList', 'JSONObject', 'ListOfJSONObject', 'JSONValue', 'FileType', 'EnvFileType', 'StrCollection', 'ParseFloat', 'Encoder', 'FileEncoder', 'Decoder', 'FileDecoder', 'NUMBERS', 'T', 'E', 'U', 'M', 'NT', 'DT', 'DD', 'N', 'S', 'LT', 'LSQ', 'FREF', 'dataclass_transform', 'UNSET', 'META', 'ENV_META', '_META', '_ENV_META']

import typing
from collections.abc import Buffer as Buffer
from datetime import date, datetime, time
from enum import Enum
from os import PathLike
from typing import ClassVar
from typing import Deque as PyDeque
from typing import ForwardRef as PyForwardRef
from typing import LiteralString as PyLiteralString
from typing import NotRequired as PyNotRequired
from typing import Protocol as PyProtocol
from typing import ReadOnly as PyReadOnly
from typing import Required as PyRequired
from typing import TypedDict as PyTypedDict
from typing import Unpack as Unpack
from typing import dataclass_transform as dataclass_transform

from _typeshed import SupportsRead, SupportsWrite

from ._bases import AbstractEnvMeta, AbstractMeta

FrozenKeys = frozenset[str]
JSONList = list[typing.Any]
JSONObject = dict[str, typing.Any]
ListOfJSONObject = list[JSONObject]
NoneType = type(None)

FileType = typing.Union[str, bytes, PathLike, int]
EnvFileType = typing.Union[bool, FileType, typing.Iterable[FileType], None]
JSONValue = typing.Union[None, str, bool, int, float, JSONList, JSONObject]
ParseFloat = typing.Callable[[str], typing.Any]
N = typing.Union[int, float]
StrCollection = typing.Union[str, typing.Collection[str]]

# Create a generic variable that can be 'AbstractMeta', or any subclass.
# Full word as `M` is already defined in another module
_META = typing.TypeVar('_META', bound=AbstractMeta)
# Use `type` here explicitly, because we will never have an `META_` object.
META = type[_META]

# Create a generic variable that can be 'AbstractMeta', or any subclass.
# Full word as `M` is already defined in another module
_ENV_META = typing.TypeVar('_ENV_META', bound=AbstractEnvMeta)
# Use `type` here explicitly, because we will never have an `META_` object.
ENV_META = type[_ENV_META]

NUMBERS: tuple
T = typing.TypeVar('T')
T_co = typing.TypeVar('T_co', covariant=True)

@typing.type_check_only
class DefFactory(typing.Protocol[T_co]):
    def __call__(self) -> T_co: ...

E = typing.TypeVar('E', bound=Enum)
U: typing.TypeVar
M: typing.TypeVar
NT: typing.TypeVar
DT = typing.TypeVar('DT', date, time, datetime)
DD: typing.TypeVar
S: typing.TypeVar
LT: typing.TypeVar
LSQ: typing.TypeVar
FREF = typing.TypeVar('FREF', str, PyForwardRef)

class _UnsetType: ...
UNSET: _UnsetType

class ExplicitNullType:
    _instance: ClassVar[ExplicitNullType] = ...
    @classmethod
    def __init__(cls) -> None: ...
    def __bool__(self) -> bool: ...
ExplicitNull: ExplicitNullType

class Encoder(typing.Protocol):
    def __call__(self, obj: JSONObject | JSONList, /, *args: typing.Any, **kwargs: typing.Any) -> str: ...
    @classmethod
    def __subclasshook__(cls, other): ...
    def __init__(self, *args, **kwargs) -> None: ...

class FileEncoder(typing.Protocol):
    def __call__(self, obj: JSONObject | JSONList,
                 file: SupportsWrite[str],
                 /, *args: typing.Any, **kwargs: typing.Any) -> None: ...
    @classmethod
    def __subclasshook__(cls, other): ...
    def __init__(self, *args, **kwargs) -> None: ...

class Decoder(typing.Protocol):
    def __call__(self, s: str | bytes | bytearray, /, *args: typing.Any, **kwargs: typing.Any) -> JSONObject | ListOfJSONObject: ...
    @classmethod
    def __subclasshook__(cls, other): ...
    def __init__(self, *args, **kwargs) -> None: ...

class FileDecoder(typing.Protocol):
    def __call__(self, file: SupportsRead[str | bytes], /, *args: typing.Any, **kwargs: typing.Any) -> JSONObject | ListOfJSONObject: ...
    @classmethod
    def __subclasshook__(cls, other): ...
    def __init__(self, *args, **kwargs) -> None: ...

# Names in __all__ with no definition:
#   Buffer
#   DefFactory
#   EnvFileType
#   FileType
#   FrozenKeys
#   JSONList
#   JSONObject
#   JSONValue
#   ListOfJSONObject
#   N
#   NoneType
#   ParseFloat
#   PyDeque
#   PyForwardRef
#   PyLiteralString
#   PyNotRequired
#   PyProtocol
#   PyReadOnly
#   PyRequired
#   PyTypedDict
#   StrCollection
#   Unpack
#   dataclass_transform
