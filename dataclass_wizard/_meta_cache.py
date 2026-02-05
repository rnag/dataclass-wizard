from __future__ import annotations

from weakref import WeakKeyDictionary

from ._bases import AbstractMeta
from ._type_def import META


META_BY_DATACLASS = WeakKeyDictionary()

# Injected at runtime by bases_meta.py
BASE_META_CLS = None


def set_base_meta_cls(base_meta_cls):
    global BASE_META_CLS
    BASE_META_CLS = base_meta_cls


def get_meta(cls, base_cls=AbstractMeta):
    """
    Retrieves the Meta config for the :class:`AbstractJSONWizard` subclass.

    This config is set when the inner :class:`Meta` is sub-classed.
    """
    return META_BY_DATACLASS.get(cls, base_cls)


def create_meta(cls, cls_name=None, **kwargs):
    """
    Create a Meta subclass for `cls` and store it in META_BY_DATACLASS.
    Requires `set_base_meta_cls` to have been called.

    WARNING: Only use if the Meta config is undefined,
      e.g. `get_meta` for the `cls` returns `base_cls`.
    """
    base = BASE_META_CLS
    if base is None:
        # Fail fast with a helpful error instead of mysterious circular-import states.
        raise RuntimeError(
            'Base meta class not initialized. '
            'Expected set_base_meta_cls(BaseJSONWizardMeta) to be called during import.'
        )

    cls_dict = {'__slots__': (), **kwargs}

    meta: META = type(   # type: ignore
        f'{(cls_name or cls.__name__)}Meta',
        (base, ),
        cls_dict,
    )

    META_BY_DATACLASS[cls] = meta
    return meta
