def type_name(obj: type) -> str:
    """Return the type or class name of an object"""
    return getattr(obj, '__qualname__', getattr(obj, '__name__', repr(obj)))
