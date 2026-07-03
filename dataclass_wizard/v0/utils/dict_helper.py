"""
Dict helper module
"""


class NestedDict(dict):
    """
    A dictionary that automatically creates nested dictionaries for missing keys.

    This class extends the built-in `dict` to simplify working with deeply nested structures.
    If a key is accessed but does not exist, it will be created automatically with a new `NestedDict` as its value.

    Source: https://stackoverflow.com/a/5369984/10237506

    Example:
        >>> nd = NestedDict()
        >>> nd['a']['b']['c'] = 42
        >>> nd
        {'a': {'b': {'c': 42}}}

        >>> nd['x']['y']
        {}
    """

    __slots__ = ()

    def __getitem__(self, key):
        """
        Retrieve the value for a key, or create a nested dictionary for missing keys.

        Args:
            key (Hashable): The key to retrieve or create.

        Returns:
            Any: The value associated with the key, or a new `NestedDict` for missing keys.

        Example:
            >>> nd = NestedDict()
            >>> nd['foo']  # Creates a new NestedDict for 'foo'
            {}

        Note:
            If the key exists, its value is returned. Otherwise, a new `NestedDict` is created,
            stored, and returned.
        """
        if key in self: return self.get(key)
        return self.setdefault(key, NestedDict())


class DictWithLowerStore(dict):
    """
    A ``dict``-like object with a lower-cased key store.

    All keys are expected to be strings. The structure remembers the
    case of the lower-cased key to be set, and methods like ``get()``
    and ``get_key()`` will use the lower-cased store. However, querying
    and contains testing is case sensitive::

        dls = DictWithLowerStore()
        dls['Accept'] = 'application/json'
        dls['aCCEPT'] == 'application/json'         # False (raises KeyError)
        dls['Accept'] == 'application/json'         # True
        dls.get('aCCEPT') == 'application/json'     # True

        dls.get_key('aCCEPT') == 'Accept'           # True
        list(dls) == ['Accept']                     # True

    .. NOTE::
       I don't want to use the `CaseInsensitiveDict` from
       `request.structures`, because it turns out the lookup via that dict
       implementation is rather slow. So this version is somewhat of a
       trade-off, where I retain the same speed on lookups as a plain `dict`,
       but I also have a lower-cased key store, in case I ever need to use it.

    """
    __slots__ = ('_lower_store', )

    def __init__(self, data=None, **kwargs):
        super().__init__()
        self._lower_store = {}
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        # Store the lower-cased key for lookups via `get`. Also store the
        # actual key alongside the value.
        self._lower_store[key.lower()] = (key, value)

    def get_key(self, key) -> str:
        """Return the original cased key"""
        return self._lower_store[key.lower()][0]

    def get(self, key):
        """
        Do a case-insensitive lookup. This lower-cases `key` and looks up
        from the lower-cased key store.
        """
        try:
            return self.__getitem__(key)
        except KeyError:
            return self._lower_store[key.lower()][1]

    def __delitem__(self, key):
        lower_key = key.lower()
        actual_key, _ = self._lower_store[lower_key]

        del self[actual_key]
        del self._lower_store[lower_key]

    def lower_items(self):
        """Like iteritems(), but with all lowercase keys."""
        return (
            (lowerkey, keyval[1])
            for (lowerkey, keyval)
            in self._lower_store.items()
        )

    def __eq__(self, other):
        if isinstance(other, dict):
            other = DictWithLowerStore(other)
        else:
            return NotImplemented
        # Compare insensitively
        return dict(self.lower_items()) == dict(other.lower_items())

    def update(self, *args, **kwargs):
        if len(args) > 1:
            raise TypeError("update expected at most 1 arguments, got %d" % len(args))
        other = dict(*args, **kwargs)
        for key in other:
            self[key] = other[key]

    def copy(self):
        return DictWithLowerStore(self._lower_store.values())

    def __repr__(self):
        return str(dict(self.items()))
