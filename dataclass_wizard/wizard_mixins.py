"""
Helper Wizard Mixin classes.
"""
__all__ = ['JSONListWizard',
           'JSONFileWizard',
           'TOMLWizard',
           'YAMLWizard']

import json
from typing import Type, Union, AnyStr, List, Optional, TextIO, BinaryIO

from .abstractions import W
from .bases_meta import DumpMeta
from .class_helper import _META
from .dumpers import asdict
from .enums import LetterCase
from .lazy_imports import toml, toml_w, yaml
from .loaders import fromdict, fromlist
from .models import Container
from .serial_json import JSONSerializable
from .type_def import (T, ListOfJSONObject,
                       Encoder, Decoder, FileDecoder, FileEncoder, ParseFloat)


class JSONListWizard(JSONSerializable, str=False):
    """
    A Mixin class that extends :class:`JSONSerializable` (JSONWizard)
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
    A Mixin class that makes it easier to interact with JSON files.

    This can be paired with the :class:`JSONSerializable` (JSONWizard) Mixin
    class for more complete extensibility.

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


class TOMLWizard:
    # noinspection PyUnresolvedReferences
    """
    A Mixin class that makes it easier to interact with TOML data.

    .. NOTE::
      By default, *NO* key transform is used in the TOML dump process.
      In practice, this means that a `snake_case` field name in Python is saved
      as `snake_case` to TOML; however, this can easily be customized without
      the need to sub-class from :class:`JSONWizard`.

    For example:

        >>> @dataclass
        >>> class MyClass(TOMLWizard, key_transform='CAMEL'):
        >>>     ...

    """
    def __init_subclass__(cls, key_transform=LetterCase.NONE):
        """Allow easy setup of common config, such as key casing transform."""

        # Only add the key transform if Meta config has not been specified
        # for the dataclass.
        if key_transform and cls not in _META:
            DumpMeta(key_transform=key_transform).bind_to(cls)

    @classmethod
    def from_toml(cls: Type[T],
                  string_or_stream: Union[AnyStr, BinaryIO], *,
                  decoder: Optional[Decoder] = None,
                  header: str = 'items',
                  parse_float: ParseFloat = float) -> Union[T, List[T]]:
        """
        Converts a TOML `string` to an instance of the dataclass, or a list of
        the dataclass instances.

        If `header` is passed in, and the value of this key in the parsed
        ``dict`` object is a ``list``, then the return type is a ``List[T]``.
        """
        if decoder is None:  # pragma: no cover
            decoder = toml.loads

        o = decoder(string_or_stream, parse_float=parse_float)

        return (fromlist(cls, maybe_l)
                if (maybe_l := o.get(header)) and isinstance(maybe_l, list)
                else fromdict(cls, o))

    @classmethod
    def from_toml_file(cls: Type[T], file: str, *,
                       decoder: Optional[FileDecoder] = None,
                       header: str = 'items',
                       parse_float: ParseFloat = float) -> Union[T, List[T]]:
        """
        Reads in the TOML file contents and converts to an instance of the
        dataclass, or a list of the dataclass instances.

        If `header` is passed in, and the value of this key in the parsed
        ``dict`` object is a ``list``, then the return type is a ``List[T]``.
        """
        if decoder is None:  # pragma: no cover
            decoder = toml.load

        with open(file, 'rb') as in_file:
            return cls.from_toml(in_file,
                                 decoder=decoder,
                                 header=header,
                                 parse_float=parse_float)

    def to_toml(self: T,
                /,
                *encoder_args,
                encoder: Optional[Encoder] = None,
                multiline_strings: bool = False,
                indent: int = 4) -> AnyStr:
        """
        Converts the dataclass instance to a TOML `string` representation.
        """
        if encoder is None:  # pragma: no cover
            encoder = toml_w.dumps

        return encoder(asdict(self), *encoder_args,
                       multiline_strings=multiline_strings,
                       indent=indent)

    def to_toml_file(self: T, file: str, mode: str = 'w',
                     encoder: Optional[FileEncoder] = None,
                     multiline_strings: bool = False,
                     indent: int = 4) -> None:
        """
        Serializes the instance and writes it to a TOML file.
        """
        if encoder is None:  # pragma: no cover
            encoder = toml_w.dump

        with open(file, mode) as out_file:
            self.to_toml(out_file, encoder=encoder,
                         multiline_strings=multiline_strings,
                         indent=indent)

    @classmethod
    def list_to_toml(cls: Type[T],
                     instances: List[T],
                     header: str = 'items',
                     encoder: Optional[Encoder] = None,
                     **encoder_kwargs) -> AnyStr:
        """
        Converts a ``list`` of dataclass instances to a TOML `string`
        representation.
        """
        if encoder is None:
            encoder = toml_w.dumps

        list_of_dict = [asdict(o, cls=cls) for o in instances]

        return encoder({header: list_of_dict}, **encoder_kwargs)


class YAMLWizard:
    # noinspection PyUnresolvedReferences
    """
    A Mixin class that makes it easier to interact with YAML data.

    .. NOTE::
      The default key transform used in the YAML dump process is `lisp-case`,
      however this can easily be customized without the need to sub-class
      from :class:`JSONWizard`.

    For example:

        >>> @dataclass
        >>> class MyClass(YAMLWizard, key_transform='CAMEL'):
        >>>     ...

    """
    def __init_subclass__(cls, key_transform=LetterCase.LISP):
        """Allow easy setup of common config, such as key casing transform."""

        # Only add the key transform if Meta config has not been specified
        # for the dataclass.
        if key_transform and cls not in _META:
            DumpMeta(key_transform=key_transform).bind_to(cls)

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
