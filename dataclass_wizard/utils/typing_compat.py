"""
Utility module for checking generic types provided by the `typing` library.
"""

__all__ = [
    'is_literal',
    'is_union',
    'get_origin',
    'get_origin_v2',
    'is_typed_dict_type_qualifier',
    'get_args',
    'get_keys_for_typed_dict',
    'is_typed_dict',
    'is_generic',
    'is_annotated',
    'eval_forward_ref',
    'eval_forward_ref_if_needed',
]

import functools
import sys
import typing
# noinspection PyUnresolvedReferences,PyProtectedMember
from typing import Literal, Union, _AnnotatedAlias

from .string_conv import repl_or_with_union
from ..constants import PY310_OR_ABOVE, PY313_OR_ABOVE
from ..type_def import (FREF,
                        PyRequired,
                        PyNotRequired,
                        PyReadOnly,
                        PyForwardRef)


_TYPED_DICT_TYPE_QUALIFIERS = frozenset(
    {PyRequired, PyNotRequired, PyReadOnly}
)


def get_keys_for_typed_dict(cls):
    """
    Given a :class:`TypedDict` sub-class, returns a pair of
    (required_keys, optional_keys)
    """
    return cls.__required_keys__, cls.__optional_keys__


def _is_annotated(cls):
    return isinstance(cls, _AnnotatedAlias)


# TODO Remove
def is_literal(cls) -> bool:
    try:
        return cls.__origin__ is Literal
    except AttributeError:
        return False

# Ref:
#   https://typing.readthedocs.io/en/latest/spec/typeddict.html#required-and-notrequired
#   https://typing.readthedocs.io/en/latest/spec/glossary.html#term-type-qualifier
def is_typed_dict_type_qualifier(cls) -> bool:
    return cls in _TYPED_DICT_TYPE_QUALIFIERS


# Ref:
#   https://github.com/python/typing/blob/master/typing_extensions/src_py3/typing_extensions.py#L2111
if PY310_OR_ABOVE:  # pragma: no cover
    from types import GenericAlias, UnionType
    _get_args = typing.get_args

    _BASE_GENERIC_TYPES = (
        typing._GenericAlias,
        typing._SpecialForm,
        GenericAlias,
        UnionType,
    )

    _UNION_TYPES = frozenset({
        UnionType,
        Union,
    })

    _TYPING_LOCALS = None

    def _process_forward_annotation(base_type):
        return PyForwardRef(base_type, is_argument=False)

    def is_union(cls) -> bool:
        return cls in _UNION_TYPES

    def get_origin_v2(cls):
        if type(cls) is UnionType:
            return UnionType

        return getattr(cls, '__origin__', cls)

    def _get_origin(cls, raise_=False):
        if isinstance(cls, UnionType):
            return Union

        try:
            return cls.__origin__
        except AttributeError:
            if raise_:
                raise
            return cls

else:  # pragma: no cover
    from typing_extensions import get_args as _get_args

    _BASE_GENERIC_TYPES = (
        typing._GenericAlias,
        typing._SpecialForm,
    )

    # PEP 585 is introduced in Python 3.9
    # PEP 604 (Allows writing union types as `X | Y`) is introduced
    #   in Python 3.10
    _TYPING_LOCALS = {'Union': Union}

    def _process_forward_annotation(base_type):
        return PyForwardRef(
            repl_or_with_union(base_type), is_argument=False)

    def is_union(cls) -> bool:
        return cls is Union

    def get_origin_v2(cls):
        return getattr(cls, '__origin__', cls)

    def _get_origin(cls, raise_=False):
        try:
            return cls.__origin__
        except AttributeError:
            if raise_:
                raise
            return cls


try:
    # noinspection PyProtectedMember,PyUnresolvedReferences
    from typing_extensions import _TYPEDDICT_TYPES

except ImportError:
    from typing import is_typeddict as is_typed_dict

else:
    def is_typed_dict(cls: type) -> bool:
        """
        Checks if `cls` is a sub-class of ``TypedDict``
        """
        return isinstance(cls, _TYPEDDICT_TYPES)


def is_generic(cls):
    """
    Detects any kind of generic, for example `List` or `List[int]`. This
    includes "special" types like Union, Any ,and Tuple - anything that's
    subscriptable, basically.

    https://stackoverflow.com/a/52664522/10237506
    """
    return isinstance(cls, _BASE_GENERIC_TYPES)


get_args = _get_args
get_args.__doc__ = """
Get type arguments with all substitutions performed.

For unions, basic simplifications used by Union constructor are performed.
Examples::
    get_args(Dict[str, int]) == (str, int)
    get_args(int) == ()
    get_args(Union[int, Union[T, int], str][int]) == (int, str)
    get_args(Union[int, Tuple[T, int]][str]) == (int, Tuple[str, int])
    get_args(Callable[[], T][int]) == ([], int)\
"""

# TODO refactor to use `typing.get_origin` when time permits.
get_origin = _get_origin
get_origin.__doc__ = """
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
  unable to retrieve the un-subscripted value.\
"""

is_annotated = _is_annotated
is_annotated.__doc__ = """Detects a :class:`typing.Annotated` class."""


if PY313_OR_ABOVE:
    # noinspection PyProtectedMember,PyUnresolvedReferences
    _eval_type = functools.partial(typing._eval_type, type_params=())
else:
    # noinspection PyProtectedMember,PyUnresolvedReferences
    _eval_type = typing._eval_type


def eval_forward_ref(base_type: FREF,
                     cls: type):
    """
    Evaluate a forward reference using the class globals, and return the
    underlying type reference.
    """

    if isinstance(base_type, str):
        base_type = _process_forward_annotation(base_type)

    # Evaluate the ForwardRef here
    base_globals = sys.modules[cls.__module__].__dict__

    return _eval_type(base_type, base_globals, _TYPING_LOCALS)


_ForwardRefTypes = frozenset(FREF.__constraints__)


def eval_forward_ref_if_needed(base_type: Union[type, FREF],
                               base_cls: type):
    """
    If needed, evaluate a forward reference using the class globals, and
    return the underlying type reference.
    """

    if type(base_type) in _ForwardRefTypes:
        # Evaluate the forward reference here.
        base_type = eval_forward_ref(base_type, base_cls)

    return base_type
