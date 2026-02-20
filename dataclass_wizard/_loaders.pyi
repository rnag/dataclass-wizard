from dataclasses import Field
from datetime import date, datetime, timezone
from types import EllipsisType
from typing import Callable, ClassVar, TypeVar

from _typeshed import Incomplete

from ._bases import AbstractMeta as AbstractMeta
from ._bases import BaseLoadHook as BaseLoadHook
from ._class_helper import (
    resolve_dataclass_field_to_alias_for_load as resolve_dataclass_field_to_alias_for_load,
)
from ._class_helper import set_class_loader as set_class_loader
from ._decorators import (
    process_patterned_date_time as process_patterned_date_time,
)
from ._decorators import (
    setup_recursive_safe_function as setup_recursive_safe_function,
)
from ._decorators import (
    setup_recursive_safe_function_for_generic as setup_recursive_safe_function_for_generic,
)
from ._meta_cache import create_meta as create_meta
from ._meta_cache import get_meta as get_meta
from ._models import Extras as Extras
from ._models import TypeInfo as TypeInfo
from ._type_conv import as_date as as_date
from ._type_conv import as_datetime as as_datetime
from ._type_conv import as_int as as_int
from ._type_conv import as_time as as_time
from ._type_conv import as_timedelta as as_timedelta
from ._type_def import JSONObject
from ._type_def import T as T
from ._type_utils import create_new_class as create_new_class
from ._type_utils import is_subclass_safe as is_subclass_safe
from .enums import KeyAction as KeyAction
from .enums import KeyCase as KeyCase
from .errors import JSONWizardError as JSONWizardError
from .errors import MissingData as MissingData
from .errors import MissingFields as MissingFields
from .errors import ParseError as ParseError
from .errors import UnknownKeysError as UnknownKeysError
from .utils._dataclass_compat import dataclass_fields as dataclass_fields
from .utils._dataclass_compat import (
    dataclass_init_field_names as dataclass_init_field_names,
)
from .utils._dataclass_compat import (
    dataclass_init_fields as dataclass_init_fields,
)
from .utils._dataclass_compat import (
    dataclass_kw_only_init_field_names as dataclass_kw_only_init_field_names,
)
from .utils._dataclass_compat import set_new_attribute as set_new_attribute
from .utils._function_builder import FunctionBuilder as FunctionBuilder
from .utils._object_path import safe_get as safe_get
from .utils._string_conv import possible_json_keys as possible_json_keys
from .utils._typing_compat import (
    eval_forward_ref_if_needed as eval_forward_ref_if_needed,
)
from .utils._typing_compat import (
    get_keys_for_typed_dict as get_keys_for_typed_dict,
)
from .utils._typing_compat import get_origin_v2 as get_origin_v2
from .utils._typing_compat import is_annotated as is_annotated
from .utils._typing_compat import is_typed_dict as is_typed_dict
from .utils._typing_compat import (
    is_typed_dict_type_qualifier as is_typed_dict_type_qualifier,
)
from .utils._typing_compat import is_union as is_union

LEAF_TYPES: frozenset
UTC: timezone
TRUTHY_VALUES: frozenset
CLASS_TO_LOADER: dict
CATCH_ALL: str
TAG: str
PY311_OR_ABOVE: bool
PACKAGE_NAME: str
def get_default_load_hooks(loader: type[L] = ...) -> dict[type, Callable]: ...
_LOAD_HOOKS: str

L = TypeVar('L', bound=LoadMixin)

class LoadMixin(BaseLoadHook):
    transform_json_field: ClassVar[Callable[[str], str] | None | EllipsisType] = ...
    __HOOKS__: ClassVar[dict[type, Callable]]
    @classmethod
    def __init_subclass__(cls, _setup_defaults: bool = True, **kwargs): ...
    @staticmethod
    def load_fallback(tp: TypeInfo, extras: Extras): ...
    @staticmethod
    def is_none(tp: TypeInfo, extras: Extras) -> str: ...
    @classmethod
    def load_to_str(cls, tp: TypeInfo, extras: Extras): ...
    @staticmethod
    def load_to_int(tp: TypeInfo, extras: Extras): ...
    @staticmethod
    def load_to_float(tp: TypeInfo, extras: Extras): ...
    @staticmethod
    def load_to_bool(tp: TypeInfo, extras: Extras): ...
    @staticmethod
    def load_to_bytes(tp: TypeInfo, extras: Extras): ...
    @classmethod
    def load_to_bytearray(cls, tp: TypeInfo, extras: Extras): ...
    @staticmethod
    def load_to_none(tp: TypeInfo, extras: Extras): ...
    @staticmethod
    def load_to_enum(tp: TypeInfo, extras: Extras): ...
    @staticmethod
    def load_to_uuid(tp: TypeInfo, extras: Extras): ...
    @classmethod
    def load_to_iterable(cls, tp: TypeInfo, extras: Extras): ...
    @classmethod
    def load_to_tuple(cls, tp: TypeInfo, extras: Extras): ...
    @classmethod
    def load_to_named_tuple(cls, tp: TypeInfo, extras: Extras): ...
    @classmethod
    def _load_to_named_tuple_fn(cls, _cls, tp: TypeInfo, extras: Extras): ...
    @classmethod
    def load_to_named_tuple_untyped(cls, tp: TypeInfo, extras: Extras): ...
    @classmethod
    def _build_dict_comp(cls, tp, v, i_next, k_next, v_next, kt, vt, extras): ...
    @classmethod
    def load_to_dict(cls, tp: TypeInfo, extras: Extras): ...
    @classmethod
    def load_to_defaultdict(cls, tp: TypeInfo, extras: Extras): ...
    @classmethod
    def load_to_typed_dict(cls, tp: TypeInfo, extras: Extras): ...
    @classmethod
    def _load_to_typed_dict_fn(cls, _cls, tp: TypeInfo, extras: Extras): ...
    @classmethod
    def load_to_union(cls, _cls, tp: TypeInfo, extras: Extras): ...
    @staticmethod
    def load_to_literal(tp: TypeInfo, extras: Extras, _cls: Incomplete | None = ...): ...
    @staticmethod
    def load_to_decimal(tp: TypeInfo, extras: Extras): ...
    @staticmethod
    def load_to_path(tp: TypeInfo, extras: Extras): ...
    @classmethod
    def load_to_date(cls, tp: TypeInfo, extras: Extras): ...
    @classmethod
    def load_to_datetime(cls, tp: TypeInfo, extras: Extras): ...
    @staticmethod
    def load_to_time(tp: TypeInfo, extras: Extras): ...
    @staticmethod
    def _load_to_date(tp: TypeInfo, extras: Extras, cls: type[date] | type[datetime]): ...
    @staticmethod
    def load_to_timedelta(tp: TypeInfo, extras: Extras): ...
    @staticmethod
    def load_to_dataclass(tp: TypeInfo, extras: Extras, _cls: Incomplete | None = ...): ...
    @classmethod
    def load_dispatcher_for_annotation(cls, tp, extras): ...
def setup_default_loader(cls: type[LoadMixin] = ...): ...
def check_and_raise_missing_fields(_locals, o, cls, fields: tuple[Field, ...] | None, **kwargs): ...
def load_func_for_dataclass(cls: type, extras: Extras | None = ..., loader_cls: type[LoadMixin] = ..., base_meta_cls: type = ...) -> Callable[[JSONObject], T] | None: ...
def generate_field_code(cls_loader: LoadMixin, extras: Extras, field: Field, field_i: int, var_name: Incomplete | None = ...) -> str | TypeInfo: ...
def re_raise(e, cls, o, fields, field, value): ...
def get_loader(class_or_instance: Incomplete | None = ..., create: bool = ..., base_cls: type[L] = ...) -> type[L]: ...
def fromdict(cls: type[T], d: JSONObject) -> T: ...
def fromlist(cls: type[T], list_of_dict: list[JSONObject]) -> list[T]: ...
