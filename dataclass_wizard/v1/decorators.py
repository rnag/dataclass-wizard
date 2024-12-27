from functools import wraps
from typing import Callable

from .models import Extras, TypeInfo
from ..utils.function_builder import FunctionBuilder


def setup_recursive_safe_function(func: Callable) -> Callable:
    """
    A decorator to ensure recursion safety and setup FunctionBuilder
    for dynamic functions.

    Prevents infinite recursion for nested or recursive data structures
    (e.g., dataclasses, unions, or typed ``dict``s). Initializes a new
    `FunctionBuilder` instance and passes it to the decorated function
    via the context (`extras`).

    Parameters
    ----------
    func : Callable
        The function to be decorated, responsible for returning the
        generated function name.

    Returns
    -------
    Callable
        A wrapped function ensuring recursion safety and FunctionBuilder
        initialization.
    """
    @wraps(func)
    def wrapper(tp: TypeInfo, extras: Extras) -> str:
        """
        Ensures recursion safety and initializes FunctionBuilder.

        Parameters
        ----------
        tp : TypeInfo
            Metadata describing the type for the operation.
        extras : Extras
            Context containing auxiliary data, including recursion guards
            and FunctionBuilder.

        Returns
        -------
        str
            The generated function name with arguments for the given type.
        """
        cls = tp.origin

        # Retrieve the recursion guard from the context
        recursion_guard = extras['recursion_guard']

        # If no function is already generated for this type
        if (fn_name := recursion_guard.get(cls)) is None:
            # Retrieve and update the main FunctionBuilder
            main_fn_gen = extras['fn_gen']

            # Copy `extras` so as not to mutate it
            updated_extras = extras.copy()
            updated_extras['locals'] = {'cls': cls}
            updated_extras['fn_gen'] = new_fn_gen = FunctionBuilder()

            # Generate the function name
            fn_name = recursion_guard[cls] = func(tp, updated_extras)

            # Merge the new FunctionBuilder into the main one
            main_fn_gen |= new_fn_gen

        return f'{fn_name}({tp.v()})'

    return wrapper
