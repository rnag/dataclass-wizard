from typing import TypeVar

_KT = TypeVar('_KT')
_VT = TypeVar('_VT')

class NestedDict(dict):
    def __getitem__(self, key: _KT) -> _VT: ...
