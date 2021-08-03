from functools import wraps
from typing import Any, Type

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
