"""
Helper Wizard Mixin classes.
"""
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
    def from_json(cls: type[W], string: AnyStr, *,
                  decoder: Decoder = json.loads,
                  **decoder_kwargs) -> W | Container[W]:
        """
        Converts a JSON `string` to an instance of the dataclass, or a
        Container (list) of the dataclass instances.
        """
        ...

    @classmethod
    def from_list(cls: type[W], o: ListOfJSONObject) -> Container[W]:
        """
        Converts a Python `list` object to a Container (list) of the dataclass
        instances.
        """
        ...


class JSONFileWizard(SerializerHookMixin):
    """
    A Mixin class that makes it easier to interact with JSON files.

    This can be paired with the :class:`JSONSerializable` (JSONWizard) Mixin
    class for more complete extensibility.

    """
    @classmethod
    def from_json_file(cls: type[T], file: FileType, *,
                       decoder: FileDecoder = json.load,
                       **decoder_kwargs) -> T | list[T]:
        """
        Reads in the JSON file contents and converts to an instance of the
        dataclass, or a list of the dataclass instances.
        """
        ...

    def to_json_file(self: T, file: FileType, mode: str = 'w',
                     encoder: FileEncoder = json.dump,
                     **encoder_kwargs) -> None:
        """
        Serializes the instance and writes it to a JSON file.
        """
        ...


class TOMLWizard(SerializerHookMixin):
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
        ...

    @classmethod
    def from_toml(cls: type[T],
                  string_or_stream: AnyStr | BinaryIO, *,
                  decoder: Decoder | None = None,
                  header: str = 'items',
                  parse_float: ParseFloat = float) -> T | list[T]:
        """
        Converts a TOML `string` to an instance of the dataclass, or a list of
        the dataclass instances.

        If ``header`` is provided and the corresponding value in the parsed
        data is a ``list``, the return type is ``List[T]``.
        """
        ...

    @classmethod
    def from_toml_file(cls: type[T], file: FileType, *,
                       decoder: FileDecoder | None = None,
                       header: str = 'items',
                       parse_float: ParseFloat = float) -> T | list[T]:
        """
        Reads the contents of a TOML file and converts them
        into an instance (or list of instances) of the dataclass.

        Similar to :meth:`from_toml`, it can return a list if ``header``
        is specified and points to a list in the TOML data.
        """
        ...

    def to_toml(self: T,
                /,
                *encoder_args,
                encoder: Encoder | None = None,
                multiline_strings: bool = False,
                indent: int = 4) -> AnyStr:
        """
        Converts a dataclass instance to a TOML `string`.

        Optional parameters include ``multiline_strings``
        for enabling/disabling multiline formatting of strings,
        and ``indent`` for setting the indentation level.
        """
        ...

    def to_toml_file(self: T, file: FileType, mode: str = 'wb',
                     encoder: FileEncoder | None = None,
                     multiline_strings: bool = False,
                     indent: int = 4) -> None:
        """
        Serializes a dataclass instance and writes it to a TOML file.

        By default, opens the file in "write binary" mode.
        """
        ...

    @classmethod
    def list_to_toml(cls: type[T],
                     instances: list[T],
                     header: str = 'items',
                     encoder: Encoder | None = None,
                     **encoder_kwargs) -> AnyStr:
        """
        Serializes a ``list`` of dataclass instances into a TOML `string`,
        grouped under a specified header.
        """
        ...


class YAMLWizard(SerializerHookMixin):
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
        ...

    @classmethod
    def from_yaml(cls: type[T],
                  string_or_stream: AnyStr | TextIO | BinaryIO, *,
                  decoder: Decoder | None = None,
                  **decoder_kwargs) -> T | list[T]:
        """
        Converts a YAML `string` to an instance of the dataclass, or a list of
        the dataclass instances.
        """
        ...

    @classmethod
    def from_yaml_file(cls: type[T], file: FileType, *,
                       decoder: FileDecoder | None = None,
                       **decoder_kwargs) -> T | list[T]:
        """
        Reads in the YAML file contents and converts to an instance of the
        dataclass, or a list of the dataclass instances.
        """
        ...

    def to_yaml(self: T, *,
                encoder: Encoder | None = None,
                **encoder_kwargs) -> AnyStr:
        """
        Converts the dataclass instance to a YAML `string` representation.
        """
        ...

    def to_yaml_file(self: T, file: FileType, mode: str = 'w',
                     encoder: FileEncoder | None = None,
                     **encoder_kwargs) -> None:
        """
        Serializes the instance and writes it to a YAML file.
        """
        ...

    @classmethod
    def list_to_yaml(cls: type[T],
                     instances: list[T],
                     encoder: Encoder | None = None,
                     **encoder_kwargs) -> AnyStr:
        """
        Converts a ``list`` of dataclass instances to a YAML `string`
        representation.
        """
        ...
