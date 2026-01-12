from _typeshed import DataclassInstance
from dataclasses import MISSING, Field
from typing import Any, MutableMapping, Callable, Mapping, TypeVar, overload, Literal
from weakref import WeakKeyDictionary

_T = TypeVar('_T')

# A cached mapping of dataclass to the list of fields, as returned by
# `dataclasses.fields()`.
FIELDS: WeakKeyDictionary[type, tuple[Field[Any], ...]] = WeakKeyDictionary()
# A cached mapping of dataclass to whether
# any field has a `default` or `default_factory`
SEEN_DEFAULT: WeakKeyDictionary[type, bool] = WeakKeyDictionary()

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
def dataclass_needs_refresh(cls: type[DataclassInstance] | type[Any]) -> bool: ...
def apply_env_wizard_dataclass(cls: type[_T], dc_kwargs: Mapping[str, Any]) -> type[_T]: ...

def dataclass_fields(cls: type) -> tuple[Field, ...]:
    """
    Cache the `dataclasses.fields()` call for each class, as overall that
    ends up around 5x faster than making a fresh call each time.

    """

@overload
def dataclass_init_fields(cls: type, as_list: Literal[True] = False) -> list[Field]:
    """Get only the dataclass fields that would be passed into the constructor."""


@overload
def dataclass_init_fields(cls: type, as_list: Literal[False] = False) -> tuple[Field]:
    """Get only the dataclass fields that would be passed into the constructor."""


def dataclass_field_names(cls: type) -> tuple[str, ...]:
    """Get the names of all dataclass fields"""


def dataclass_init_field_names(cls: type) -> tuple[str, ...]:
    """Get the names of all __init__() dataclass fields"""


def dataclass_kw_only_init_field_names(cls: type) -> set[str]:
    """Get the names of all "KEYWORD-ONLY" dataclass fields"""


def dataclass_field_to_default(cls: type) -> dict[str, Any]:
    """Get default values for the (optional) dataclass fields."""
