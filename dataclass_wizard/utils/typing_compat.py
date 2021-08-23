"""
Utility module for checking generic types provided by the `typing` library.
"""

__all__ = [
    'is_literal',
    'get_origin',
    'get_args',
    'get_keys_for_typed_dict',
    'get_named_tuple_field_types',
    'is_typed_dict',
    'is_generic',
    'is_base_generic',
    'is_annotated',
    'get_type_hints_with_extras'
]

import typing
from collections.abc import Callable
from functools import partial

from ..constants import PY36, PY38, PY310_OR_ABOVE
from ..type_def import PyLiteral, PyTypedDicts


# TODO maybe move this to `type_def` if it makes sense
TypedDictTypes = []

for PyTypedDict in PyTypedDicts:
    class RealPyTypedDict(PyTypedDict):
        pass  # create a real class, because `PyTypedDict` is a helper function

    TypedDictTypes.append(type(RealPyTypedDict))

    del RealPyTypedDict


def get_keys_for_typed_dict(cls):
    """
    Given a :class:`TypedDict` sub-class, returns a pair of
    (required_keys, optional_keys)
    """
    return cls.__required_keys__, cls.__optional_keys__


if not PY36:    # pragma: no cover
    # Python 3.7+

    _BASE_GENERIC_TYPES = (
        typing._GenericAlias,
        typing._SpecialForm,
    )

    try:
        from typing_extensions import get_type_hints, _AnnotatedAlias
    except ImportError:
        from typing import get_type_hints, _AnnotatedAlias

    _get_type_hints_with_extras = partial(get_type_hints, include_extras=True)


    def _is_annotated(cls):
        return isinstance(cls, _AnnotatedAlias)


    def _is_generic(cls):
        return isinstance(cls, _BASE_GENERIC_TYPES)


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

    def _get_origin(cls, raise_=False):
        try:
            return cls.__origin__
        except AttributeError:
            if raise_:
                raise
            return cls

    # Ref:
    #   https://github.com/python/typing/blob/master/typing_extensions/src_py3/typing_extensions.py#L2111
    if PY310_OR_ABOVE:
        _get_args = typing.get_args
    else:
        from typing_extensions import get_args as _get_args


    def _get_named_tuple_field_types(cls, raise_=True):
        """
        Note: The latest Python versions only support the `__annotations__`
        attribute.
        """
        try:
            return cls.__annotations__
        except AttributeError:
            if raise_:
                raise
            return None

else:   # pragma: no cover
    # Python 3.6

    _BASE_GENERIC_TYPES = (
        typing._FinalTypingBase,
        typing.GenericMeta,
    )

    from typing import get_type_hints as _get_type_hints_with_extras
    from typing_extensions import AnnotatedMeta


    def _is_generic(cls):
        return isinstance(cls, _BASE_GENERIC_TYPES)


    def _is_base_generic(cls):
        if isinstance(cls, (typing.GenericMeta, typing._Union)):
            return cls.__args__ in {None, ()}

        return isinstance(cls, typing._Optional)

    def _is_annotated(cls):
        return isinstance(cls, AnnotatedMeta)

    # Ref: https://github.com/python/typing/blob/master/typing_extensions/src_py3/typing_extensions.py#L572

    def is_literal(cls) -> bool:
        try:
            return cls == PyLiteral[cls.__values__]
        except AttributeError:
            return False

    def _get_origin(cls, raise_=False):

        try:
            extra = cls.__extra__
            if extra is None and isinstance(cls, typing.GenericMeta):
                return typing.Generic
            return extra

        except AttributeError:

            try:
                return cls.__origin__
            except AttributeError:
                if is_literal(cls):
                    return PyLiteral
                if isinstance(cls, typing._ClassVar):
                    return typing.ClassVar
                if raise_:
                    raise
                return cls


    def _get_args(cls):
        if is_literal(cls):
            return cls.__values__

        if is_annotated(cls):
            return (cls.__args__[0], ) + cls.__metadata__

        try:
            res = cls.__args__
            if get_origin(cls) is Callable and res[0] is not Ellipsis:
                res = (list(res[:-1]), res[-1])
            return res
        except AttributeError:
            # This can happen if it's annotated w/o a subscript, e.g.
            #   my_union: Union
            return ()


    def _get_named_tuple_field_types(cls, raise_=True):
        """
        Note: Prior to PEP 526, only `_field_types` attribute was assigned.
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
    return type(cls) in TypedDictTypes


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


def get_args(cls):
    """
    Get type arguments with all substitutions performed.

    For unions, basic simplifications used by Union constructor are performed.
    Examples::
        get_args(Dict[str, int]) == (str, int)
        get_args(int) == ()
        get_args(Union[int, Union[T, int], str][int]) == (int, str)
        get_args(Union[int, Tuple[T, int]][str]) == (int, Tuple[str, int])
        get_args(Callable[[], T][int]) == ([], int)
    """
    return _get_args(cls)


# TODO refactor to use `typing.get_origin` when time permits.
def get_origin(cls, raise_=False):
    """
    Get the un-subscripted value of a type. If we're unable to retrieve this
    value, return type `cls` if `raise_` is false.

    This supports generic types, Callable, Tuple, Union, Literal, Final and
    ClassVar. Return None for unsupported types.

    Examples::

        get_origin(Literal[42]) is Literal
        get_origin(int) is int
        get_origin(ClassVar[int]) is ClassVar
        get_origin(Generic) is Generic
        get_origin(Generic[T]) is Generic
        get_origin(Union[T, int]) is Union
        get_origin(List[Tuple[T, T]][int]) == list

    :raise AttributeError: When the `raise_` flag is enabled, and we are
      unable to retrieve the un-subscripted value.

    """
    return _get_origin(cls, raise_=raise_)


def get_named_tuple_field_types(cls, raise_=True):
    """
    Get annotations for a :class:`typing.NamedTuple` sub-class.
    """
    return _get_named_tuple_field_types(cls, raise_)


def is_annotated(cls):
    """
    Detects a :class:`typing.Annotated` class.
    """
    return _is_annotated(cls)


def get_type_hints_with_extras(obj, **kwargs):
    """
    Generally the same as :func:`typing.get_type_hints`, but passes
    ``extras=True`` by default, so that we can also retrieve the arguments
    for :class:`typing.Annotated` types.

    """
    return _get_type_hints_with_extras(obj, **kwargs)
