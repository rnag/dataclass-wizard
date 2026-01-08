"""
Dict helper module

TODO: Delete when time allows --
  See https://github.com/rnag/dataclass-wizard/issues/215
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
