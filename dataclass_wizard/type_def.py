__all__ = [
    'PyForwardRef',
    'PyLiteral',
    'PyDeque',
    'PyTypedDicts',
    'FrozenKeys',
    'DefFactory',
    'NoneType',
    'ExplicitNullType',
    'ExplicitNull',
    'NUMBERS',
    'T',
    'E',
    'U',
    'M',
    'NT',
    'DD',
    'N',
    'S',
    'LT',
    'LSQ'
]

from collections import deque
from enum import Enum
from typing import (
    Type, TypeVar, Sequence, Mapping,
    List, DefaultDict, FrozenSet, NamedTuple, Callable
)
from uuid import UUID

from .constants import PY36, PY38_OR_ABOVE
from .decorators import discard_kwargs


# Type check for numeric types - needed because `bool` is technically
# a Number.
NUMBERS = int, float

# Generic type
T = TypeVar('T')

# Enum subclass type
E = TypeVar('E', bound=Enum)

# UUID subclass type
U = TypeVar('U', bound=UUID)

# Mapping type
M = TypeVar('M', bound=Mapping)

# NamedTuple type
NT = TypeVar('NT', bound=NamedTuple)

# DefaultDict type
DD = TypeVar('DD', bound=DefaultDict)

# Numeric type
N = TypeVar('N', int, float, complex)

# Sequence type
S = TypeVar('S', bound=Sequence)

# List or Tuple type
LT = TypeVar('LT', list, tuple)

# List, Set, or Deque (Double ended queue) type
LSQ = TypeVar('LSQ', list, set, frozenset, deque)

# A fixed set of key names
FrozenKeys = FrozenSet[str]

# Default factory type, assuming a no-args constructor
DefFactory = Callable[[], T]

# The class of the `None` singleton, cached for re-usability
NoneType = type(None)

# For Python 3.8+, we need to use both `TypedDict` implementations (from both
# the `typing` and `typing_extensions` modules). Because it's not clear which
# version users might choose to use. And they might choose to use either, due
# to the issues mentioned below (comment taken from `typing_extensions`):
#
#   The standard library TypedDict in Python 3.8 does not store runtime information
#   about which (if any) keys are optional.  See https://bugs.python.org/issue38834
#   The standard library TypedDict in Python 3.9.0/1 does not honour the "total"
#   keyword with old-style TypedDict().  See https://bugs.python.org/issue42059
PyTypedDicts: List[Type['TypedDict']] = []


if PY38_OR_ABOVE:
    from typing import ForwardRef as PyForwardRef
    from typing import Literal as PyLiteral
    from typing import TypedDict
    from typing import Deque as PyDeque

    PyTypedDicts.append(TypedDict)
    # Python 3.8+ users might import from either `typing` or
    # `typing_extensions`, so check for both types.
    try:
        # noinspection PyUnresolvedReferences
        from typing_extensions import TypedDict as PyTypedDict
        PyTypedDicts.append(PyTypedDict)
    except ImportError:
        pass
else:
    from typing_extensions import Literal as PyLiteral
    from typing_extensions import TypedDict as PyTypedDict
    # Seems like `Deque` was only introduced to `typing` in 3.6.1, so Python
    # 3.6.0 won't have it; to be safe, we'll instead import from the
    # `typing_extensions` module here.
    from typing_extensions import Deque as PyDeque

    PyTypedDicts.append(PyTypedDict)

    if PY36:
        from typing import _ForwardRef as PyForwardRef
        # Need to wrap the constructor to discard arguments like `is_argument`
        PyForwardRef.__init__ = discard_kwargs(PyForwardRef.__init__)
    else:
        from typing import ForwardRef as PyForwardRef


# Create our own "nullish" type for explicit type assertions
class ExplicitNullType:
    __slots__ = ()

    def __bool__(self):
        return False

    def __repr__(self):
        return self.__class__.__qualname__


ExplicitNull = ExplicitNullType()
