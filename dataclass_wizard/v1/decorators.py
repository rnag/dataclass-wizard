from __future__ import annotations

from dataclasses import MISSING
from functools import wraps
from typing import TYPE_CHECKING, Callable, Union, cast

from ..type_def import DT
from ..utils.function_builder import FunctionBuilder


if TYPE_CHECKING:  # pragma: no cover
    from .models import Extras, TypeInfo


def process_patterned_date_time(func: Callable) -> Callable:
    """
    Decorator for processing patterned date and time data.

    If the 'pattern' key exists in the `extras` dictionary, it updates
    the base and origin of the type information and processes the
    pattern before calling the original function.

    Supports both class methods and static methods.

    Args:
        func (Callable): The function to decorate, either a class method
        or static method.

    Returns:
        Callable: The wrapped function with pattern processing applied.
    """

    # Determine if the function is a class method
    # noinspection PyUnresolvedReferences
    is_class_method = func.__code__.co_argcount == 3

    if is_class_method:

        @wraps(func)
        def class_method_wrapper(cls, tp: TypeInfo, extras: Extras):
            # Process pattern if it exists in extras
            if (pb := extras.get('pattern')) is not None:
                pb.base = cast(type[DT], tp.origin)
                tp.origin = cast(type, pb)
                return pb.load_to_pattern(tp, extras)

            # Fallback to the original method
            return func(cls, tp, extras)

        return class_method_wrapper
    else:

        @wraps(func)
        def static_method_wrapper(tp: TypeInfo, extras: Extras):
            # Process pattern if it exists in extras
            if (pb := extras.get('pattern')) is not None:
                pb.base = cast(type[DT], tp.origin)
                tp.origin = cast(type, pb)
                return pb.load_to_pattern(tp, extras)

            # Fallback to the original method
            return func(tp, extras)

        return static_method_wrapper


def setup_recursive_safe_function(
    func: Callable = None,
    *,
    fn_name: Union[str, None] = None,
    is_generic: bool = False,
    add_cls: bool = True,
    prefix: str = 'load',
) -> Callable:
    """
    A decorator to ensure recursion safety and facilitate dynamic function generation
    with `FunctionBuilder`, supporting both generic and non-generic types.

    The decorated function can define the logic for dynamically generated functions.
    If `fn_name` is provided, the decorator assumes that the function generation
    context (e.g., `with fn_gen.function(...)`) has already been handled externally
    and will not apply it again.

    :param func: The function to decorate. If None, the decorator is applied with arguments.
    :type func: Callable, optional
    :param fn_name: A format string for dynamically generating function names, or None.
    :type fn_name: str, optional
    :param is_generic: Whether the function deals with generic types.
    :type is_generic: bool, optional
    :param add_cls: Whether the class should be added to the function locals
      for `FunctionBuilder`.
    :type add_cls: bool, optional
    :return: The decorated function with recursion safety and dynamic function generation.
    :rtype: Callable
    """

    if func is None:
        return lambda f: setup_recursive_safe_function(
            f,
            fn_name=fn_name,
            is_generic=is_generic,
            add_cls=add_cls,
            prefix=prefix,
        )

    def _wrapper_logic(tp: TypeInfo, extras: Extras, _cls=None) -> str:
        """
        Shared logic for both class and regular methods. Ensures recursion safety
        and integrates `FunctionBuilder` to dynamically create functions.

        :param tp: The type or generic type being processed.
        :param extras: A context dictionary containing auxiliary information like
                       recursion guards and function builders.
        :type extras: dict
        :param _cls: The class context for class methods. Defaults to None.
        :return: The generated function call expression as a string.
        :rtype: str
        """
        cls = tp.args if is_generic else tp.origin
        recursion_guard = extras['recursion_guard']

        if (_fn_name := recursion_guard.get(cls)) is None:
            cls_name = extras['cls_name']
            tp_name = func.__name__.split('_', 2)[-1]

            # Generate the function name
            if fn_name:
                _fn_name = fn_name.format(cls_name=tp.name)
            else:
                _fn_name = (
                    f'_{prefix}_{cls_name}_{tp_name}_{tp.field_i}' if is_generic
                    else f'_{prefix}_{cls_name}_{tp_name}_{tp.name}'
                )

            recursion_guard[cls] = _fn_name

            # Retrieve the main FunctionBuilder
            main_fn_gen = extras['fn_gen']

            # Prepare a new FunctionBuilder for this function
            updated_extras = extras.copy()
            updated_extras['locals'] = _locals = {'cls': cls} if add_cls else {}
            updated_extras['fn_gen'] = new_fn_gen = FunctionBuilder()

            # Apply the decorated function logic
            if fn_name:
                # Assume `with fn_gen.function(...)` is already handled
                func(_cls, tp, updated_extras) if _cls else func(tp, updated_extras)
            else:
                # Apply `with fn_gen.function(...)` explicitly
                with new_fn_gen.function(_fn_name, ['v1'], MISSING, _locals):
                    func(_cls, tp, updated_extras) if _cls else func(tp, updated_extras)

            # Merge the new FunctionBuilder into the main one
            main_fn_gen |= new_fn_gen

        return f'{_fn_name}({tp.v()})'

    # Determine if the function is a class method
    # noinspection PyUnresolvedReferences
    is_class_method = func.__code__.co_argcount == 3

    if is_class_method:
        def wrapper_class_method(_cls, tp, extras) -> str:
            """
            Wrapper logic for class methods. Passes the class context to `_wrapper_logic`.

            :param _cls: The class instance.
            :param tp: The type or generic type being processed.
            :param extras: A context dictionary with auxiliary information.
            :type extras: dict
            :return: The generated function call expression as a string.
            :rtype: str
            """
            return _wrapper_logic(tp, extras, _cls)

        wrapper = wraps(func)(wrapper_class_method)
    else:
        wrapper = wraps(func)(_wrapper_logic)

    return wrapper


def setup_recursive_safe_function_for_generic(func: Callable, prefix='load') -> Callable:
    """
    A helper decorator to handle generic types using
    `setup_recursive_safe_function`.

    Parameters
    ----------
    func : Callable
        The function to be decorated, responsible for returning the
        generated function name.

    Returns
    -------
    Callable
        A wrapped function ensuring recursion safety for generic types.
    """
    return setup_recursive_safe_function(func, is_generic=True, prefix=prefix)
