def type_name(obj: type) -> str:
    """Return the type or class name of an object"""
    from ..utils.typing_compat import is_generic

    # for type generics like `dict[str, float]`, we want to return
    # the subscripted value as is, rather than simply accessing the
    # `__name__` property, which in this case would be `dict` instead.
    if is_generic(obj):
        return str(obj)

    return getattr(obj, '__qualname__', getattr(obj, '__name__', repr(obj)))
