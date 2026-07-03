from typing import AnyStr, BinaryIO, TextIO

from .._serial_json import SerializerHookMixin
from .._type_def import Decoder, Encoder, FileDecoder, FileEncoder, FileType, T
from ..enums import KeyCase

class YAMLWizard(SerializerHookMixin):

    def __init_subclass__(cls, dump_case=KeyCase.KEBAB):
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
                **encoder_kwargs) -> str:
        ...

    def to_yaml_file(self: T, file: FileType, mode: str = 'w',
                     encoder: FileEncoder | None = None,
                     **encoder_kwargs) -> None:
        ...

    @classmethod
    def list_to_yaml(cls: type[T],
                     instances: list[T],
                     encoder: Encoder | None = None,
                     **encoder_kwargs) -> str:
        ...
