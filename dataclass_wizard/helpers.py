"""Miscellaneous / common helper functions"""

from dataclasses import MISSING


# create_fn: this implementation is copied from the `_create_fn()`
# implementation from the `dataclasses` module in Python 3.10
#
# noinspection PyShadowingBuiltins
def create_fn(name, args, body, *, globals=None, locals=None,
              return_type=MISSING):
    # Note that we mutate locals when exec() is called.  Caller
    # beware!  The only callers are internal to this module, so no
    # worries about external callers.
    if locals is None:
        locals = {}
    return_annotation = ''
    if return_type is not MISSING:
        locals['_return_type'] = return_type
        return_annotation = '->_return_type'
    args = ','.join(args)
    body = '\n'.join(f'  {b}' for b in body)

    # Compute the text of the entire function.
    txt = f' def {name}({args}){return_annotation}:\n{body}'

    local_vars = ', '.join(locals.keys())
    txt = f"def __create_fn__({local_vars}):\n{txt}\n return {name}"
    ns = {}
    exec(txt, globals, ns)
    return ns['__create_fn__'](**locals)


def type_name(obj: type) -> str:
    """Return the type or class name of an object"""
    from .utils.typing_compat import is_generic

    # for type generics like `dict[str, float]`, we want to return
    # the subscripted value as is, rather than simply accessing the
    # `__name__` property, which in this case would be `dict` instead.
    if is_generic(obj):
        return str(obj)

    return getattr(obj, '__qualname__', getattr(obj, '__name__', repr(obj)))
