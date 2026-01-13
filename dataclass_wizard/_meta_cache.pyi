from typing import Any
from weakref import WeakKeyDictionary

META_INNER_BY_CLASS: WeakKeyDictionary[type, type[Any]] = WeakKeyDictionary()

