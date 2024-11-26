"""
Helper Wizard Mixin classes.
"""
__all__ = ['JSONListWizard',
           'JSONFileWizard',
           'TOMLWizard',
           'YAMLWizard']

import json
from typing import AnyStr

from .bases_meta import DumpMeta
from .class_helper import _META
from .dumpers import asdict
from .enums import LetterCase
from .lazy_imports import toml, toml_w, yaml
from .loaders import fromdict, fromlist
from .models import Container
from .serial_json import JSONSerializable


class JSONListWizard(JSONSerializable, str=False):

    @classmethod
    def from_json(cls, string, *,
                  decoder=json.loads,
                  **decoder_kwargs):

        o = decoder(string, **decoder_kwargs)

        if isinstance(o, dict):
            return fromdict(cls, o)

        return Container[cls](fromlist(cls, o))

    @classmethod
    def from_list(cls, o):

        return Container[cls](fromlist(cls, o))


class JSONFileWizard:

    @classmethod
    def from_json_file(cls, file, *,
                       decoder=json.load,
                       **decoder_kwargs):

        with open(file) as in_file:
            o = decoder(in_file, **decoder_kwargs)

        return fromdict(cls, o) if isinstance(o, dict) else fromlist(cls, o)

    def to_json_file(self, file, mode='w',
                     encoder=json.dump,
                     **encoder_kwargs):

        with open(file, mode) as out_file:
            encoder(asdict(self), out_file, **encoder_kwargs)


class TOMLWizard:

    def __init_subclass__(cls, key_transform=LetterCase.NONE):

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

        if encoder is None:  # pragma: no cover
            encoder = toml_w.dumps

        return encoder(asdict(self), *encoder_args,
                       multiline_strings=multiline_strings,
                       indent=indent)

    def to_toml_file(self, file, mode='wb',
                     encoder=None,
                     multiline_strings=False,
                     indent=4):

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

        if encoder is None:
            encoder = toml_w.dumps

        list_of_dict = [asdict(o, cls=cls) for o in instances]

        return encoder({header: list_of_dict}, **encoder_kwargs)


class YAMLWizard:

    def __init_subclass__(cls, key_transform=LetterCase.LISP):

        # Only add the key transform if Meta config has not been specified
        # for the dataclass.
        if key_transform and cls not in _META:
            DumpMeta(key_transform=key_transform).bind_to(cls)

    @classmethod
    def from_yaml(cls,
                  string_or_stream, *,
                  decoder=None,
                  **decoder_kwargs):

        if decoder is None:
            decoder = yaml.safe_load

        o = decoder(string_or_stream, **decoder_kwargs)

        return fromdict(cls, o) if isinstance(o, dict) else fromlist(cls, o)

    @classmethod
    def from_yaml_file(cls, file, *,
                       decoder=None,
                       **decoder_kwargs):

        with open(file) as in_file:
            return cls.from_yaml(in_file, decoder=decoder,
                                 **decoder_kwargs)

    def to_yaml(self, *,
                encoder=None,
                **encoder_kwargs):

        if encoder is None:
            encoder = yaml.dump

        return encoder(asdict(self), **encoder_kwargs)

    def to_yaml_file(self, file, mode='w',
                     encoder = None,
                     **encoder_kwargs):

        with open(file, mode) as out_file:
            self.to_yaml(stream=out_file, encoder=encoder,
                         **encoder_kwargs)

    @classmethod
    def list_to_yaml(cls,
                     instances,
                     encoder = None,
                     **encoder_kwargs):

        if encoder is None:
            encoder = yaml.dump

        list_of_dict = [asdict(o, cls=cls) for o in instances]

        return encoder(list_of_dict, **encoder_kwargs)
