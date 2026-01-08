import types
from typing import Any, MutableMapping

class LazyLoader(types.ModuleType):
    def __init__(
        self,
        parent_module_globals: MutableMapping[str, Any],
        name: str,
        extra: str | None = ...,
        local_name: str | None = ...,
        warning: str | None = ...,
    ) -> None: ...
    def load(self) -> types.ModuleType: ...
    def __getattr__(self, item: str) -> Any: ...
    def __dir__(self) -> list[str]: ...
