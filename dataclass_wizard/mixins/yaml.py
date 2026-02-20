from .._bases_meta import DumpMeta
from .._dumpers import asdict
from .._lazy_imports import yaml
from .._loaders import fromdict, fromlist
from .._meta_cache import META_BY_DATACLASS
from ..enums import KeyCase


class YAMLWizard:
    # noinspection PyUnresolvedReferences,GrazieInspection
    """
    A Mixin class that makes it easier to interact with YAML data.

    .. NOTE::
      The default key transform used in the YAML dump process is `lisp-case`,
      however this can easily be customized without the need to sub-class
      from :class:`JSONWizard`.

    For example:

        >>> @dataclass
        >>> class MyClass(YAMLWizard, dump_case='CAMEL'):
        >>>     ...

    """
    def __init_subclass__(cls, dump_case=KeyCase.KEBAB):
        """Allow easy setup of common config, such as key casing transform."""
        # Only add the key transform if Meta config has not been specified
        # for the dataclass.
        if dump_case and cls not in META_BY_DATACLASS:
            DumpMeta(case=dump_case).bind_to(cls)

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
