import json
from typing import AnyStr

from .._abstractions import W
from .._serial_json import JSONWizard, SerializerHookMixin
from .._type_def import (
    Decoder,
    FileDecoder,
    FileEncoder,
    FileType,
    ListOfJSONObject,
    T,
)
from ..utils.containers import Container

class JSONListWizard(JSONWizard):

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
