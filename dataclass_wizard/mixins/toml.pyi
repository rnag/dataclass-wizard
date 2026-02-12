from typing import AnyStr, BinaryIO

from .._serial_json import SerializerHookMixin
from .._type_def import FileType, T, Decoder, ParseFloat, FileDecoder, Encoder, FileEncoder

class TOMLWizard(SerializerHookMixin):

    def __init_subclass__(cls, dump_case=None):
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
                indent: int = 4) -> str:
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
                     **encoder_kwargs) -> str:
        ...
