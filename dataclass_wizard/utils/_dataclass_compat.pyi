from dataclasses import MISSING
from typing import Any, MutableMapping, Callable, Mapping, TypeVar

_T = TypeVar('_T')

def set_qualname(cls: type[Any], value: Any) -> Any: ...
def set_new_attribute(cls: type[Any], name: str, value: Any, force: bool = False) -> bool: ...
def create_fn(
    name: str,
    args: list[str],
    body: list[str],
    *,
    globals: MutableMapping[str, Any] | None = ...,
    locals: MutableMapping[str, Any] | None = ...,
    return_type: Any = MISSING,
) -> Callable[..., Any]: ...
def dataclass_needs_refresh(cls: type[Any]) -> bool: ...
def apply_env_wizard_dataclass(cls: type[_T], dc_kwargs: Mapping[str, Any]) -> type[_T]: ...
