from typing import Any
from weakref import WeakKeyDictionary

META_BY_DATACLASS: WeakKeyDictionary[type, type[Any]] = WeakKeyDictionary()

