from dataclasses import Field, MISSING
from typing import Union, Collection

from .constants import PY310_OR_ABOVE


# Type for a string or a collection of strings.
_STR_COLLECTION = Union[str, Collection[str]]


def json_key(*keys: str, all=False, dump=True):
    """
    Represents a mapping of one or more JSON key names for a dataclass field.

    This is only in *addition* to the default key transform; for example, a
    JSON key appearing as "myField", "MyField" or "my-field" will already map
    to a dataclass field "my_field" by default (assuming the key transform
    converts to snake case).

    The mapping to each JSON key name is case-sensitive, so passing "myfield"
    will not match a "myField" key in a JSON string or a Python dict object.

    :param keys: A list of one of more JSON keys to associate with the
      dataclass field.
    :param all: True to also associate the reverse mapping, i.e. from
      dataclass field to JSON key. If multiple JSON keys are passed in, it
      uses the first one provided in this case. This mapping is then used when
      `to_dict` or `to_json` is called, instead of the default key transform.
    :param dump: False to skip this field in the serialization process to
      JSON. By default, this field and its value is included.
    """

    return JSON(*keys, all=all, dump=dump)


def json_field(keys: _STR_COLLECTION, *,
               all=False, dump=True,
               default=MISSING, default_factory=MISSING,
               init=True, repr=True,
               hash=None, compare=True, metadata=None):
    """
    This is a helper function that sets the same defaults for keyword
    arguments as the ``dataclasses.field`` function. It can be thought of as
    an alias to ``dataclasses.field(...)``, but one which also represents
    a mapping of one or more JSON key names to a dataclass field.

    This is only in *addition* to the default key transform; for example, a
    JSON key appearing as "myField", "MyField" or "my-field" will already map
    to a dataclass field "my_field" by default (assuming the key transform
    converts to snake case).

    The mapping to each JSON key name is case-sensitive, so passing "myfield"
    will not match a "myField" key in a JSON string or a Python dict object.

    `keys` is a string, or a collection (list, tuple, etc.) of strings. It
    represents one of more JSON keys to associate with the dataclass field.

    When `all` is passed as True (default is False), it will also associate
    the reverse mapping, i.e. from dataclass field to JSON key. If multiple
    JSON keys are passed in, it uses the first one provided in this case.
    This mapping is then used when ``to_dict`` or ``to_json`` is called,
    instead of the default key transform.

    When `dump` is passed as False (default is True), this field will be
    skipped, or excluded, in the serialization process to JSON.
    """

    if default is not MISSING and default_factory is not MISSING:
        raise ValueError('cannot specify both default and default_factory')

    return JSONField(keys, all, dump, default, default_factory, init, repr,
                     hash, compare, metadata)


class JSON:
    """
    Represents one or more mappings of JSON keys.

    See the docs on the :func:`json_key` function for more info.
    """
    __slots__ = ('keys',
                 'all',
                 'dump')

    def __init__(self, *keys: str, all=False, dump=True):
        self.keys = keys
        self.all = all
        self.dump = dump


class JSONField(Field):
    """
    Alias to a :class:`dataclasses.Field`, but one which also represents a
    mapping of one or more JSON key names to a dataclass field.

    See the docs on the :func:`json_field` function for more info.
    """
    __slots__ = ('json', )

    # In Python 3.10, dataclasses adds a new parameter to the :class:`Field`
    # constructor: `kw_only`
    #
    # Ref: https://docs.python.org/3.10/library/dataclasses.html#dataclasses.dataclass
    if PY310_OR_ABOVE:
        def __init__(self, keys: _STR_COLLECTION, all: bool, dump: bool,
                     default, default_factory, init, repr, hash, compare,
                     metadata):

            super().__init__(default, default_factory, init, repr, hash,
                             compare, metadata, False)

            if isinstance(keys, str):
                keys = (keys,)

            self.json = JSON(*keys, all=all, dump=dump)

    else:
        def __init__(self, keys: _STR_COLLECTION, all: bool, dump: bool,
                     default, default_factory, init, repr, hash, compare,
                     metadata):

            super().__init__(default, default_factory, init, repr, hash,
                             compare, metadata)

            if isinstance(keys, str):
                keys = (keys, )

            self.json = JSON(*keys, all=all, dump=dump)
