from collections.abc import Collection
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    NotRequired,
    Self,
    TypeAlias,
    TypedDict,
)

from ._type_def import META, DefFactory, T
from .conditions import Condition
from .patterns import PatternBase
from .utils._function_builder import FunctionBuilder

# Type for a string or a collection of strings.
_STR_COLLECTION: TypeAlias = str | Collection[str]
LEAF_TYPES: frozenset[type]
LEAF_TYPES_NO_BYTES: frozenset[type]
SEQUENCE_ORIGINS: frozenset[type]
MAPPING_ORIGINS: frozenset[type]

@dataclass(order=True)
class TypeInfo:
    # type origin (ex. `List[str]` -> `List`)
    origin: type
    # type arguments (ex. `Dict[str, int]` -> `(str, int)`)
    args: tuple[type, ...] | None = None
    # name of type origin (ex. `List[str]` -> 'list')
    name: str | None = None
    # index of iteration, *only* unique within the scope of a field assignment!
    i: int = 1
    # index of field within the dataclass, *guaranteed* to be unique.
    field_i: int = 1
    # prefix of value in assignment (prepended to `i`),
    # defaults to 'v' if not specified.
    prefix: str = 'v'
    # index / indices of assignment (ex. `2, 0 -> v1[2][0]`, *or* a string `"key" -> v4["key"]`)
    index: int | str | tuple[int | str, ...] | None = None
    # explicit value name (overrides prefix + index)
    val_name: str | None = None
    # indicates if we are currently in Optional,
    # e.g. `typing.Optional[...]` *or* `typing.Union[T, ...*T2, None]`
    in_optional: bool = False

    def replace(self, **changes) -> TypeInfo: ...
    @staticmethod
    def ensure_in_locals(extras: Extras, *tps: Callable | type, **name_to_tp: Callable[..., Any] | object) -> list[str]: ...
    def type_name(self, extras: Extras,
                  *, bound: type | None = None) -> str: ...
    def v(self) -> str: ...
    def v_for_def(self) -> str: ...
    def v_and_next(self) -> tuple[str, str, int]: ...
    def v_and_next_k_v(self) -> tuple[str, str, str, int]: ...
    def multi_wrap(self, extras, prefix='', *result, force=False) -> list[str]: ...
    def wrap(self, result: str,
             extras: Extras,
             force=False,
             prefix='',
             *, bound: type | None = None) -> Self: ...
    def wrap_builtin(self, bound: type, result: str, extras: Extras) -> Self: ...
    def wrap_dd(self, default_factory: DefFactory[T], result: str, extras: Extras) -> Self: ...
    def _wrap_inner(self, extras: Extras,
                    tp: type | DefFactory | None = None,
                    prefix: str = '',
                    is_builtin: bool = False,
                    force=False,
                    bound: type | None = None) -> str | None: ...


class Extras(TypedDict):
    """
    "Extra" config that can be used in the load / dump process.
    """
    config: META
    cls: type
    cls_name: str
    fn_gen: FunctionBuilder
    locals: dict[str, Any]
    pattern: NotRequired[PatternBase]
    recursion_guard: dict[Any, str]


def ensure_type_ref(extras: Extras, tp: type, *,
                    name: str | None = None,
                    prefix: str = '',
                    is_builtin: bool = False) -> str: ...

def finalize_skip_if(skip_if: Condition,
                     operand_1: str,
                     conditional: str) -> str:
    ...


def get_skip_if_condition(skip_if: Condition,
                          _locals: dict[str, Any],
                          operand_2: str | None = None,
                          condition_i: int | None = None,
                          condition_var: str = '_skip_if_') -> str | bool:
    ...
