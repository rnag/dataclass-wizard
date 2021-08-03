__all__ = [
    'PyForwardRef',
    'PyLiteral',
    'PyTypedDict',
    'NoneType',
    'ExplicitNullType',
    'ExplicitNull',
    'NUMBERS',
    'T',
    'M',
    'N',
    'S'
]

from typing import TypeVar, Mapping, Sequence

from .constants import PY36, PY38_OR_ABOVE
from .decorators import discard_kwargs


# Type check for numeric types - needed because `bool` is technically
# a Number.
NUMBERS = int, float

# Generic type
T = TypeVar('T')

# Mapping type
M = TypeVar('M', bound=Mapping)

# Numeric type
N = TypeVar('N', int, float, complex)

# Sequence type
S = TypeVar('S', bound=Sequence)

# The class of the `None` singleton, cached for re-usability
NoneType = type(None)


if PY38_OR_ABOVE:
    from typing import ForwardRef as PyForwardRef
    from typing import Literal as PyLiteral
    from typing import TypedDict as PyTypedDict
else:
    from typing_extensions import Literal as PyLiteral
    from typing_extensions import TypedDict as PyTypedDict
    if PY36:
        from typing import _ForwardRef as PyForwardRef
        # Need to wrap the constructor to discard arguments like `is_argument`
        PyForwardRef.__init__ = discard_kwargs(PyForwardRef.__init__)
    else:
        from typing import ForwardRef as PyForwardRef


# Create our own "nullish" type for explicit type assertions
class ExplicitNullType:

    def __bool__(self):
        return False

    def __repr__(self):
        return self.__class__.__qualname__


ExplicitNull = ExplicitNullType()
