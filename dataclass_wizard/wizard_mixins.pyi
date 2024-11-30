__all__ = ['JSONListWizard',
           'JSONFileWizard',
           'TOMLWizard',
           'YAMLWizard']

import json
from os import PathLike
from typing import AnyStr, TextIO, BinaryIO

from .abstractions import W
from .enums import LetterCase
from .models import Container
from .serial_json import JSONSerializable, SerializerHookMixin
from .type_def import (T, ListOfJSONObject,
                       Encoder, Decoder, FileDecoder, FileEncoder, ParseFloat)


# A type that can be string or `path.Path`
# https://stackoverflow.com/a/78070015/10237506
type FileType = str | bytes | PathLike


class JSONListWizard(JSONSerializable, str=False):

    @classmethod
    def from_json(cls: type[W], string: AnyStr, *,
                  decoder: Decoder = json.loads,
                  **decoder_kwargs) -> W | Container[W]:

        ...

    @classmethod
    def from_list(cls: type[W], o: ListOfJSONObject) -> Container[W]:
        ...


class JSONFileWizard(SerializerHookMixin):

    @classmethod
    def from_json_file(cls: type[T], file: FileType, *,
                       decoder: FileDecoder = json.load,
                       **decoder_kwargs) -> T | list[T]:
        ...

    def to_json_file(self: T, file: FileType, mode: str = 'w',
                     encoder: FileEncoder = json.dump,
                     **encoder_kwargs) -> None:
        ...


class TOMLWizard(SerializerHookMixin):

    def __init_subclass__(cls, key_transform=LetterCase.NONE):
        ...

    @classmethod
    def from_toml(cls: type[T],
                  string_or_stream: AnyStr | BinaryIO, *,
                  decoder: Decoder | None = None,
                  header: str = 'items',
                  parse_float: ParseFloat = float) -> T | list[T]:
        ...

    @classmethod
    def from_toml_file(cls: type[T], file: FileType, *,
                       decoder: FileDecoder | None = None,
                       header: str = 'items',
                       parse_float: ParseFloat = float) -> T | list[T]:
        ...

    def to_toml(self: T,
                /,
                *encoder_args,
                encoder: Encoder | None = None,
                multiline_strings: bool = False,
                indent: int = 4) -> AnyStr:
        ...

    def to_toml_file(self: T, file: FileType, mode: str = 'wb',
                     encoder: FileEncoder | None = None,
                     multiline_strings: bool = False,
                     indent: int = 4) -> None:
        ...

    @classmethod
    def list_to_toml(cls: type[T],
                     instances: list[T],
                     header: str = 'items',
                     encoder: Encoder | None = None,
                     **encoder_kwargs) -> AnyStr:
        ...


class YAMLWizard(SerializerHookMixin):

    def __init_subclass__(cls, key_transform=LetterCase.LISP):
        ...

    @classmethod
    def from_yaml(cls: type[T],
                  string_or_stream: AnyStr | TextIO | BinaryIO, *,
                  decoder: Decoder | None = None,
                  **decoder_kwargs) -> T | list[T]:
        ...

    @classmethod
    def from_yaml_file(cls: type[T], file: FileType, *,
                       decoder: FileDecoder | None = None,
                       **decoder_kwargs) -> T | list[T]:
        ...

    def to_yaml(self: T, *,
                encoder: Encoder | None = None,
                **encoder_kwargs) -> AnyStr:
        ...

    def to_yaml_file(self: T, file: FileType, mode: str = 'w',
                     encoder: FileEncoder | None = None,
                     **encoder_kwargs) -> None:
        ...

    @classmethod
    def list_to_yaml(cls: type[T],
                     instances: list[T],
                     encoder: Encoder | None = None,
                     **encoder_kwargs) -> AnyStr:
        ...
