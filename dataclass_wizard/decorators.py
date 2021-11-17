from functools import wraps
from typing import Any, Type, Callable, Union, TypeVar, cast

from .constants import SINGLE_ARG_ALIAS, IDENTITY
from .errors import ParseError


T = TypeVar('T')


# noinspection PyPep8Naming
class cached_class_property(object):
    """
    Descriptor decorator implementing a class-level, read-only property,
    which caches the attribute on-demand on the first use.

    Credits: https://stackoverflow.com/a/4037979/10237506
    """
    def __init__(self, func):
        self.__func__ = func
        self.__attr_name__ = func.__name__

    def __get__(self, instance, cls=None):
        """This method is only called the first time, to cache the value."""
        if cls is None:
            cls = type(instance)

        # Build the attribute.
        attr = self.__func__(cls)

        # Cache the value; hide ourselves.
        setattr(cls, self.__attr_name__, attr)

        return attr


def try_with_load(f):

    @wraps(f)
    def new_func(o: Any, ann_type: Type, *args, **kwargs):
        try:
            return f(o, ann_type, *args, **kwargs)

        except ParseError as e:
            # This means that a nested load hook raised an exception.
            # Therefore, to help with debugging we should print the name
            # of the outer load hook and the original object.
            e.kwargs['load_hook'] = f.__name__
            e.obj = o
            # Re-raise the original error
            raise

        except Exception as e:
            raise ParseError(e, o, ann_type, load_hook=f.__name__)

    return new_func


def discard_kwargs(f):

    @wraps(f)
    def new_func(*args, **_kwargs):
        return f(*args)

    return new_func


def _alias(default: Callable) -> Callable[[T], T]:
    """
    Decorator which re-assigns a function `_f` to point to `default` instead.
    Since global function calls in Python are somewhat expensive, this is
    mainly done to reduce a bit of overhead involved in the functions calls.

    For example, consider the below example::

        def f2(o):
            return o

        def f1(o):
            return f2(o)

    Calling function `f1` will incur some additional overhead, as opposed to
    simply calling `f2`.

    Now assume we wrap `f1` with the `_alias` decorator::

        def f2(o):
            return o

        @_alias(f2)
        def f1(o):
            ...

    This will essentially perform the assignment of `f1 = f2`, so calling
    `f1()` in this case has no additional function overhead, as opposed to
    just calling `f2()`.
    """

    def new_func(_f: T) -> T:
        return cast(T, default)

    return new_func


def _single_arg_alias(alias_func: Union[Callable, str] = None):
    """
    Decorator which wraps a function to set the :attr:`SINGLE_ARG_ALIAS` on
    a function `f`, which is an alias function that takes only one argument.
    This is useful mainly so that other functions can access this attribute,
    and can opt to call it instead of function `f`.
    """

    def new_func(f):
        setattr(f, SINGLE_ARG_ALIAS, alias_func)
        return f

    return new_func


def _identity(_f: Callable = None, id: Union[object, str] = None):
    """
    Decorator which wraps a function to set the :attr:`IDENTITY` on a function
    `f`, indicating that this is an identity function that returns its first
    argument. This is useful mainly so that other functions can access this
    attribute, and can opt to call it instead of function `f`.
    """

    def new_func(f):
        setattr(f, IDENTITY, id)
        return f

    return new_func(_f) if _f else new_func


def resolve_alias_func(f: Callable, _locals=None, raise_=False) -> Callable:
    """
    Resolve the underlying single-arg alias function for `f`, using the
    provided function locals (which will be a dict). If `f` does not have an
    associated alias function, we return `f` itself.

    :raises AttributeError: If `raise_` is true and `f` is not a single-arg
      alias function.
    """

    try:
        single_arg_alias_func = getattr(f, SINGLE_ARG_ALIAS)

    except AttributeError:
        if raise_:
            raise
        return f

    else:
        if isinstance(single_arg_alias_func, str) and _locals is not None:
            return _locals[single_arg_alias_func]

        return single_arg_alias_func
