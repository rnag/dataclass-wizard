"""
Pulling some functions removed in recent versions of Python into the module for continued compatibility.
All function names and bodies are left exactly as they were prior to being removed.
"""

from dataclasses import MISSING
from types import FunctionType


def _set_qualname(cls, value):
    # Removed in Python 3.13
    # Original: `dataclasses._set_qualname`
    # Ensure that the functions returned from _create_fn uses the proper
    # __qualname__ (the class they belong to).
    if isinstance(value, FunctionType):
        value.__qualname__ = f"{cls.__qualname__}.{value.__name__}"
    return value


def _set_new_attribute(cls, name, value):
    # Removed in Python 3.13
    # Original: `dataclasses._set_new_attribute`
    # Never overwrites an existing attribute.  Returns True if the
    # attribute already exists.
    if name in cls.__dict__:
        return True
    _set_qualname(cls, value)
    setattr(cls, name, value)
    return False


def _create_fn(name, args, body, *, globals=None, locals=None,
               return_type=MISSING):
    # Removed in Python 3.13
    # Original: `dataclasses._create_fn`
    # Note that we may mutate locals. Callers beware!
    # The only callers are internal to this module, so no
    # worries about external callers.
    if locals is None:
        locals = {}
    return_annotation = ''
    if return_type is not MISSING:
        locals['__dataclass_return_type__'] = return_type
        return_annotation = '->__dataclass_return_type__'
    args = ','.join(args)
    body = '\n'.join(f'  {b}' for b in body)

    # Compute the text of the entire function.
    txt = f' def {name}({args}){return_annotation}:\n{body}'

    # Free variables in exec are resolved in the global namespace.
    # The global namespace we have is user-provided, so we can't modify it for
    # our purposes. So we put the things we need into locals and introduce a
    # scope to allow the function we're creating to close over them.
    local_vars = ', '.join(locals.keys())
    txt = f"def __create_fn__({local_vars}):\n{txt}\n return {name}"
    ns = {}
    exec(txt, globals, ns)
    return ns['__create_fn__'](**locals)
