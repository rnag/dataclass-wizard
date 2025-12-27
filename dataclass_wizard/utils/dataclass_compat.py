"""
Pulling some functions removed in recent versions of Python into the module for continued compatibility.
All function names and bodies are left exactly as they were prior to being removed.
"""

from dataclasses import MISSING, is_dataclass, fields, dataclass
from types import FunctionType

from ..constants import PY310_OR_ABOVE


def _set_qualname(cls, value):
    # Removed in Python 3.13
    # Original: `dataclasses._set_qualname`
    # Ensure that the functions returned from _create_fn uses the proper
    # __qualname__ (the class they belong to).
    if isinstance(value, FunctionType):
        value.__qualname__ = f"{cls.__qualname__}.{value.__name__}"
    return value


def _set_new_attribute(cls, name, value, force=False):
    # Removed in Python 3.13
    # Original: `dataclasses._set_new_attribute`
    # Never overwrites an existing attribute.  Returns True if the
    # attribute already exists.
    if force or name not in cls.__dict__:
        _set_qualname(cls, value)
        setattr(cls, name, value)
        return False
    return True


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


def _dataclass_needs_refresh(cls) -> bool:
    if not is_dataclass(cls):
        return True

    # dataclass fields currently registered
    dc_fields = {f.name for f in fields(cls)}
    # annotated fields declared on the class (ignore ClassVar/InitVar nuance)
    ann = getattr(cls, '__annotations__', {}) or {}
    annotated = set(ann.keys())

    # If class declares annotated fields not present in dataclass fields,
    # the dataclass metadata is stale.
    return not annotated.issubset(dc_fields)


if PY310_OR_ABOVE:
    def _apply_env_wizard_dataclass(cls, dc_kwargs):
        # noinspection PyArgumentList
        return dataclass(
            cls,
            init=False,
            kw_only=True,
            **dc_kwargs,
        )
else:  # Python 3.9: no `kw_only`
    # noinspection PyArgumentList
    def _apply_env_wizard_dataclass(cls, dc_kwargs):
        return dataclass(
            cls,
            init=False,
            **dc_kwargs,
        )
