from typing import Any
from weakref import WeakKeyDictionary

from ._bases import AbstractMeta, META
from ._type_def import T

META_BY_DATACLASS: WeakKeyDictionary[type, META] = WeakKeyDictionary()
BASE_META_CLS: type | None = None

def set_base_meta_cls(base_meta_cls: type) -> None: ...

def get_meta(cls: type, base_cls: T = AbstractMeta) -> T | META:
    """
    Retrieves the Meta config for the :class:`AbstractJSONWizard` subclass.

    This config is set when the inner :class:`Meta` is sub-classed.
    """

def create_meta(cls: type, cls_name: str | None = None, **kwargs) -> META:
    """
    Sets the Meta config for the :class:`AbstractJSONWizard` subclass.

    WARNING: Only use if the Meta config is undefined,
      e.g. `get_meta` for the `cls` returns `base_cls`.

    """
