__all__ = ['JSONListWizard',
           'JSONFileWizard',
           'YAMLWizard']

import json
from typing import Type, Union, AnyStr, List, Optional, TextIO, BinaryIO

from .abstractions import W
from .dumpers import asdict
from .lazy_imports import yaml
from .loaders import fromdict, fromlist
from .models import Container
from .serial_json import JSONSerializable
from .type_def import (T, ListOfJSONObject,
                       Encoder, Decoder, FileDecoder, FileEncoder)


class JSONListWizard(JSONSerializable, str=False):
    """
    A mixin class that extends :class:`JSONSerializable` (JSONWizard)
    to return :class:`Container` - instead of `list` - objects.

    Note that `Container` objects are simply convenience wrappers around a
    collection of dataclass instances. For all intents and purposes, they
    behave exactly the same as `list` objects, with some added helper methods:

        * ``prettify`` - Convert the list of instances to a *prettified* JSON
          string.

        * ``to_json`` - Convert the list of instances to a JSON string.

        * ``to_json_file`` - Serialize the list of instances and write it to a
          JSON file.

    """
    @classmethod
    def from_json(cls: Type[W], string: AnyStr, *,
                  decoder: Decoder = json.loads,
                  **decoder_kwargs) -> Union[W, Container[W]]:
        """
        Converts a JSON `string` to an instance of the dataclass, or a
        Container (list) of the dataclass instances.
        """
        o = decoder(string, **decoder_kwargs)

        if isinstance(o, dict):
            return fromdict(cls, o)

        return Container[cls](fromlist(cls, o))

    @classmethod
    def from_list(cls: Type[W], o: ListOfJSONObject) -> Container[W]:
        """
        Converts a Python `list` object to a Container (list) of the dataclass
        instances.
        """
        return Container[cls](fromlist(cls, o))


class JSONFileWizard:
    """
    A mixin class that makes it easier to interact with JSON files.

    This can be paired with the :class:`JSONSerializable` (JSONWizard) mixin
    class for complete extensibility.

    """
    @classmethod
    def from_json_file(cls: Type[T], file: str, *,
                       decoder: FileDecoder = json.load,
                       **decoder_kwargs) -> Union[T, List[T]]:
        """
        Reads in the JSON file contents and converts to an instance of the
        dataclass, or a list of the dataclass instances.
        """
        with open(file) as in_file:
            o = decoder(in_file, **decoder_kwargs)

        return fromdict(cls, o) if isinstance(o, dict) else fromlist(cls, o)

    def to_json_file(self: T, file: str, mode: str = 'w',
                     encoder: FileEncoder = json.dump,
                     **encoder_kwargs) -> None:
        """
        Serializes the instance and writes it to a JSON file.
        """
        with open(file, mode) as out_file:
            encoder(asdict(self), out_file, **encoder_kwargs)


class YAMLWizard:
    """
    A mixin class that makes it easier to interact with YAML data.

    """
    @classmethod
    def from_yaml(cls: Type[T],
                  string_or_stream: Union[AnyStr, TextIO, BinaryIO], *,
                  decoder: Optional[Decoder] = None,
                  **decoder_kwargs) -> Union[T, List[T]]:
        """
        Converts a YAML `string` to an instance of the dataclass, or a list of
        the dataclass instances.
        """
        if decoder is None:
            decoder = yaml.safe_load

        o = decoder(string_or_stream, **decoder_kwargs)

        return fromdict(cls, o) if isinstance(o, dict) else fromlist(cls, o)

    @classmethod
    def from_yaml_file(cls: Type[T], file: str, *,
                       decoder: Optional[FileDecoder] = None,
                       **decoder_kwargs) -> Union[T, List[T]]:
        """
        Reads in the YAML file contents and converts to an instance of the
        dataclass, or a list of the dataclass instances.
        """
        with open(file) as in_file:
            return cls.from_yaml(in_file, decoder=decoder,
                                 **decoder_kwargs)

    def to_yaml(self: T, *,
                encoder: Optional[Encoder] = None,
                **encoder_kwargs) -> AnyStr:
        """
        Converts the dataclass instance to a YAML `string` representation.
        """
        if encoder is None:
            encoder = yaml.dump

        return encoder(asdict(self), **encoder_kwargs)

    def to_yaml_file(self: T, file: str, mode: str = 'w',
                     encoder: Optional[FileEncoder] = None,
                     **encoder_kwargs) -> None:
        """
        Serializes the instance and writes it to a YAML file.
        """
        with open(file, mode) as out_file:
            self.to_yaml(stream=out_file, encoder=encoder,
                         **encoder_kwargs)

    @classmethod
    def list_to_yaml(cls: Type[T],
                     instances: List[T],
                     encoder: Optional[Encoder] = None,
                     **encoder_kwargs) -> AnyStr:
        """
        Converts a ``list`` of dataclass instances to a YAML `string`
        representation.
        """
        if encoder is None:
            encoder = yaml.dump

        list_of_dict = [asdict(o, cls=cls) for o in instances]

        return encoder(list_of_dict, **encoder_kwargs)
