from typing import Any, TypeVar, Callable
from weakref import WeakKeyDictionary

from ._type_def import T

K = TypeVar('K')
V = TypeVar('V')

def per_cls(
    cache: WeakKeyDictionary[type, V],
    cls: type,
    factory: Callable[[], dict[K, V]] = dict,
) -> dict[K, V]: ...

def is_builtin(o: Any) -> bool:
    """Check if an object/singleton/class is a builtin in Python."""


def create_new_class(
        class_or_instance, bases: tuple[T, ...],
        suffix: str | None = None, attr_dict=None) -> T:
    """
    Create (dynamically) and return a new class that sub-classes from a list
    of `bases`.
    """


def get_class_name(class_or_instance) -> str:
    """Return the fully qualified name of a class."""


def get_outer_class_name(inner_cls, default=None, raise_: bool = True) -> str:
    """
    Attempt to return the fully qualified name of the outer (enclosing) class,
    given a reference to the inner class.

    If any errors occur - such as when `inner_cls` is not a real inner
    class - then an error will be raised if `raise_` is true, and if not
    we will return `default` instead.

    """


def get_class(obj: Any) -> type:
    """Get the class for an object `obj`"""


def is_subclass(obj: Any, base_cls: type) -> bool:
    """Check if `obj` is a sub-class of `base_cls`"""


def is_subclass_safe(cls, class_or_tuple) -> bool:
    """Check if `obj` is a sub-class of `base_cls` (safer version)"""
