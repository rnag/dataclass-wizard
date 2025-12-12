"""
Helper Wizard Mixin classes.
"""
__all__ = ['JSONListWizard',
           'JSONFileWizard',
           'TOMLWizard',
           'YAMLWizard']

import json

from .bases_meta import DumpMeta
from .class_helper import _META
from .enums import LetterCase
from .lazy_imports import toml, toml_w, yaml
from .loader_selection import asdict, fromdict, fromlist
from .models import Container
from .serial_json import JSONSerializable


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
    def from_json(cls, string, *,
                  decoder=json.loads,
                  **decoder_kwargs):
        """
        Converts a JSON `string` to an instance of the dataclass, or a
        Container (list) of the dataclass instances.
        """
        o = decoder(string, **decoder_kwargs)

        if isinstance(o, dict):
            return fromdict(cls, o)

        return Container[cls](fromlist(cls, o))

    @classmethod
    def from_list(cls, o):
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
    def from_json_file(cls, file, *,
                       decoder=json.load,
                       **decoder_kwargs):
        """
        Reads in the JSON file contents and converts to an instance of the
        dataclass, or a list of the dataclass instances.
        """
        with open(file) as in_file:
            o = decoder(in_file, **decoder_kwargs)

        return fromdict(cls, o) if isinstance(o, dict) else fromlist(cls, o)

    def to_json_file(self, file, mode='w',
                     encoder=json.dump,
                     **encoder_kwargs):
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
    def from_toml(cls,
                  string_or_stream, *,
                  decoder=None,
                  header='items',
                  parse_float=float):
        """
        Converts a TOML `string` to an instance of the dataclass, or a list of
        the dataclass instances.

        If ``header`` is provided and the corresponding value in the parsed
        data is a ``list``, the return type is ``List[T]``.
        """
        if decoder is None:  # pragma: no cover
            decoder = toml.loads

        o = decoder(string_or_stream, parse_float=parse_float)

        return (fromlist(cls, maybe_l)
                if (maybe_l := o.get(header)) and isinstance(maybe_l, list)
                else fromdict(cls, o))

    @classmethod
    def from_toml_file(cls, file, *,
                       decoder=None,
                       header='items',
                       parse_float=float):
        """
        Reads the contents of a TOML file and converts them
        into an instance (or list of instances) of the dataclass.

        Similar to :meth:`from_toml`, it can return a list if ``header``
        is specified and points to a list in the TOML data.
        """
        if decoder is None:  # pragma: no cover
            decoder = toml.load

        with open(file, 'rb') as in_file:
            return cls.from_toml(in_file,
                                 decoder=decoder,
                                 header=header,
                                 parse_float=parse_float)

    def to_toml(self,
                /,
                *encoder_args,
                encoder=None,
                multiline_strings=False,
                indent=4):
        """
        Converts a dataclass instance to a TOML `string`.

        Optional parameters include ``multiline_strings``
        for enabling/disabling multiline formatting of strings,
        and ``indent`` for setting the indentation level.
        """
        if encoder is None:  # pragma: no cover
            encoder = toml_w.dumps

        return encoder(asdict(self), *encoder_args,
                       multiline_strings=multiline_strings,
                       indent=indent)

    def to_toml_file(self, file, mode='wb',
                     encoder=None,
                     multiline_strings=False,
                     indent=4):
        """
        Serializes a dataclass instance and writes it to a TOML file.

        By default, opens the file in "write binary" mode.
        """
        if encoder is None:  # pragma: no cover
            encoder = toml_w.dump

        with open(file, mode) as out_file:
            self.to_toml(out_file, encoder=encoder,
                         multiline_strings=multiline_strings,
                         indent=indent)

    @classmethod
    def list_to_toml(cls,
                     instances,
                     header='items',
                     encoder=None,
                     **encoder_kwargs):
        """
        Serializes a ``list`` of dataclass instances into a TOML `string`,
        grouped under a specified header.
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
    def from_yaml(cls,
                  string_or_stream, *,
                  decoder=None,
                  **decoder_kwargs):
        """
        Converts a YAML `string` to an instance of the dataclass, or a list of
        the dataclass instances.
        """
        if decoder is None:
            decoder = yaml.safe_load

        o = decoder(string_or_stream, **decoder_kwargs)

        return fromdict(cls, o) if isinstance(o, dict) else fromlist(cls, o)

    @classmethod
    def from_yaml_file(cls, file, *,
                       decoder=None,
                       **decoder_kwargs):
        """
        Reads in the YAML file contents and converts to an instance of the
        dataclass, or a list of the dataclass instances.
        """
        with open(file) as in_file:
            return cls.from_yaml(in_file, decoder=decoder,
                                 **decoder_kwargs)

    def to_yaml(self, *,
                encoder=None,
                **encoder_kwargs):
        """
        Converts the dataclass instance to a YAML `string` representation.
        """
        if encoder is None:
            encoder = yaml.dump

        return encoder(asdict(self), **encoder_kwargs)

    def to_yaml_file(self, file, mode='w',
                     encoder = None,
                     **encoder_kwargs):
        """
        Serializes the instance and writes it to a YAML file.
        """
        with open(file, mode) as out_file:
            self.to_yaml(stream=out_file, encoder=encoder,
                         **encoder_kwargs)

    @classmethod
    def list_to_yaml(cls,
                     instances,
                     encoder = None,
                     **encoder_kwargs):
        """
        Converts a ``list`` of dataclass instances to a YAML `string`
        representation.
        """
        if encoder is None:
            encoder = yaml.dump

        list_of_dict = [asdict(o, cls=cls) for o in instances]

        return encoder(list_of_dict, **encoder_kwargs)
