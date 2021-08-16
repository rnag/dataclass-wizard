from dataclasses import Field, MISSING
from typing import Union, Collection


# Type for a string or a collection of strings.
_STR_COLLECTION = Union[str, Collection[str]]


def json_key(*keys: str, all=False):
    return JSON(*keys, all=all)


# Constructor sets the same defaults for keyword arguments as
# the `dataclasses.field` function.
def json_field(json_keys: _STR_COLLECTION, *,
               all=False,
               default=MISSING, default_factory=MISSING,
               init=True, repr=True,
               hash=None, compare=True, metadata=None):
    if default is not MISSING and default_factory is not MISSING:
        raise ValueError('cannot specify both default and default_factory')

    return JSONField(json_keys, all, default, default_factory, init, repr,
                     hash, compare, metadata)


class JSON:
    """Represents one or more mappings of JSON keys."""
    __slots__ = ('keys',
                 'all')

    def __init__(self, *keys: str, all=False):
        self.keys = keys
        self.all = all


class JSONField(Field):
    __slots__ = ('json_key',)

    def __init__(self,
                 keys: _STR_COLLECTION,
                 all=False,
                 default=MISSING,
                 default_factory=MISSING,
                 init=True,
                 repr=True,
                 hash=None,
                 compare=True,
                 metadata=None):
        super().__init__(
            default, default_factory, init, repr, hash, compare, metadata)

        if isinstance(keys, str):
            keys = (keys,)

        self.json_key = JSON(*keys, all=all)
