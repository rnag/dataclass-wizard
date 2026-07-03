from .._bases_meta import DumpMeta
from .._dumpers import asdict
from .._lazy_imports import toml, toml_w
from .._loaders import fromdict, fromlist
from .._meta_cache import META_BY_DATACLASS


class TOMLWizard:
    # noinspection PyUnresolvedReferences,GrazieInspection
    """
    A Mixin class that makes it easier to interact with TOML data.

    .. NOTE::
      By default, *NO* key transform is used in the TOML dump process.
      In practice, this means that a `snake_case` field name in Python is saved
      as `snake_case` to TOML; however, this can easily be customized without
      the need to sub-class from :class:`JSONWizard`.

    For example:

        >>> @dataclass
        >>> class MyClass(TOMLWizard, dump_case='CAMEL'):
        >>>     ...

    """
    def __init_subclass__(cls, dump_case=None):
        """Allow easy setup of common config, such as key casing transform."""
        # Only add the key transform if Meta config has not been specified
        # for the dataclass.
        if dump_case and cls not in META_BY_DATACLASS:
            DumpMeta(case=dump_case).bind_to(cls)

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
