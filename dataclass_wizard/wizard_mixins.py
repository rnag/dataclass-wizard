import json
from typing import Type, Union, AnyStr, List

from .abstractions import W
from .dumpers import asdict
from .loaders import fromdict, fromlist
from .models import Container
from .serial_json import JSONSerializable
from .type_def import ListOfJSONObject, Decoder, FileDecoder, FileEncoder


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
    def from_json_file(cls: Type[W], file: str, *,
                       decoder: FileDecoder = json.load,
                       **decoder_kwargs) -> Union[W, List[W]]:
        """
        Reads in the JSON file contents and converts to an instance of the
        dataclass, or a list of the dataclass instances.
        """
        with open(file) as in_file:
            o = decoder(in_file, **decoder_kwargs)

        return fromdict(cls, o) if isinstance(o, dict) else fromlist(cls, o)

    def to_json_file(self, file: str, mode: str = 'w',
                     encoder: FileEncoder = json.dump,
                     **encoder_kwargs) -> None:
        """
        Serializes the instance and writes it to a JSON file.
        """
        with open(file, mode) as out_file:
            encoder(asdict(self), out_file, **encoder_kwargs)
