"""
Utility module for checking generic types provided by the `typing` library.
"""

__all__ = [
    'is_literal',
    'get_origin',
    'get_literal_args',
    'get_keys_for_typed_dict',
    'get_named_tuple_field_types',
    'is_typed_dict',
    'is_generic',
    'is_base_generic'
]

import typing

from ..constants import PY36, PY38
from ..type_def import PyLiteral, PyTypedDict


class RealPyTypedDict(PyTypedDict):
    pass  # create a real class, because `PyTypedDict` is a helper function


TypedDictType = type(RealPyTypedDict)

del RealPyTypedDict


def get_keys_for_typed_dict(cls):
    """
    Given a :class:`TypedDict` sub-class, returns a pair of
    (required_keys, optional_keys)
    """
    return cls.__required_keys__, cls.__optional_keys__


if not PY36:

    if PY38:
        def get_keys_for_typed_dict(cls):
            """
            Given a :class:`TypedDict` sub-class, returns a pair of
            (required_keys, optional_keys)

            Note: The `typing` library for Python 3.8 doesn't seem to define
              the ``__required_keys__`` and ``__optional_keys__`` attributes.
            """
            if cls.__total__:
                return frozenset(cls.__annotations__), frozenset()

            return frozenset(), frozenset(cls.__annotations__)

    def is_literal(cls) -> bool:
        try:
            return cls.__origin__ is PyLiteral
        except AttributeError:
            return False

    def get_origin(cls, raise_=True):
        try:
            return cls.__origin__
        except AttributeError:
            if raise_:
                raise
            return cls

    # TODO maybe refactor into a generic `get_args` method
    def get_literal_args(cls):
        return cls.__args__

    def get_named_tuple_field_types(cls, raise_=True):
        """
        Get annotations for a :class:`typing.NamedTuple` sub-class. The latest
        Python versions only support the `__annotations__` attribute.
        """
        try:
            return cls.__annotations__
        except AttributeError:
            if raise_:
                raise
            return None

else:
    # Python 3.6
    # Ref: https://github.com/python/typing/blob/master/typing_extensions/src_py3/typing_extensions.py#L572

    def is_literal(cls) -> bool:
        try:
            return cls == PyLiteral[cls.__values__]
        except AttributeError:
            return False

    def get_origin(cls, raise_=True):
        try:
            return getattr(cls, '__extra__', cls.__origin__)
        except AttributeError:
            if raise_:
                raise
            return cls

    def get_literal_args(cls):
        return cls.__values__

    def get_named_tuple_field_types(cls, raise_=True):
        """
        Get annotations for a :class:`typing.NamedTuple` sub-class. Prior to
        PEP 526, only `_field_types` attribute was assigned.
        """
        try:
            return cls._field_types
        except AttributeError:
            if raise_:
                raise
            return None


def is_typed_dict(cls: typing.Type) -> bool:
    """
    Checks if `cls` is a sub-class of ``TypedDict``
    """
    return type(cls) is TypedDictType


def is_generic(cls):
    """
    Detects any kind of generic, for example `List` or `List[int]`. This
    includes "special" types like Union, Any ,and Tuple - anything that's
    subscriptable, basically.

    https://stackoverflow.com/a/52664522/10237506
    """
    return _is_generic(cls)


def is_base_generic(cls):
    """
    Detects generic base classes, for example `List` (but not `List[int]`)
    """
    return _is_base_generic(cls)


if hasattr(typing, '_GenericAlias'):
    # python 3.7
    def _is_generic(cls):
        return isinstance(cls, (typing._GenericAlias, typing._SpecialForm))


    def _is_base_generic(cls):
        if isinstance(cls, typing._GenericAlias):
            if cls.__origin__ in {typing.Generic, typing._Protocol}:
                return False

            if isinstance(cls, typing._VariadicGenericAlias):
                return True

            return len(cls.__parameters__) > 0

        if isinstance(cls, typing._SpecialForm):
            return cls._name in {'ClassVar', 'Union', 'Optional'}

        return False

elif hasattr(typing, '_Union'):
    # python 3.6
    def _is_generic(cls):
        return isinstance(
            cls, (typing.GenericMeta, typing._Any, typing._Union,
                  typing._Optional, typing._ClassVar))


    def _is_base_generic(cls):
        if isinstance(cls, (typing.GenericMeta, typing._Union)):
            return cls.__args__ in {None, ()}

        return isinstance(cls, typing._Optional)
