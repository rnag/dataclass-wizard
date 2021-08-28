from functools import wraps
from typing import Any, Type, Callable, Union

from .constants import PASS_THROUGH
from .errors import ParseError


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


def default_func(default: Callable):
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

    Now assume we wrap `f1` with the `default_func` decorator::

        def f2(o):
            return o

        @default_func(f2)
        def f1(o):
            ...

    This will essentially perform the assignment of `f1 = f2`, so calling
    `f2()` in this case has no additional function overhead, as opposed to
    just calling `f1()`.
    """

    def new_func(_f):
        return default

    return new_func


def pass_through(pass_thru_func: Union[Callable, str] = None):
    """
    Decorator which wraps a function to set the :attr:`PASS_THROUGH` on
    a function `f`. This is useful mainly so that other functions can access
    this attribute, and can opt to call it instead of function `f`.
    """

    def new_func(f):
        setattr(f, PASS_THROUGH, pass_thru_func)
        return f

    return new_func


def resolve_load_func(f: Callable, _locals=None, raise_=False) -> Callable:
    """
    Resolve the underlying passed-through function for `f`, using the provided
    function locals (which will be a dict).

    :raises AttributeError: If `raise_` is true and `f` is not a pass-through
      function.
    """

    try:
        pass_through_func = getattr(f, PASS_THROUGH)

    except AttributeError:
        if raise_:
            raise
        return f

    else:
        if isinstance(pass_through_func, str) and _locals is not None:
            return _locals[pass_through_func]

        return pass_through_func
