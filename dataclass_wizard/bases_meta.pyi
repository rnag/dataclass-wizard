"""
Ideally should be in the `bases` module, however we'll run into a Circular
Import scenario if we move it there, since the `loaders` and `dumpers` modules
both import directly from `bases`.

"""
from dataclasses import MISSING
from datetime import tzinfo
from typing import Sequence, Callable, Any, Literal, TypeAlias, TypeVar, Mapping

from .bases import AbstractMeta, META, AbstractEnvMeta, V1TypeToHook
from .constants import TAG
from .enums import DateTimeTo, LetterCase, LetterCasePriority
from .models import Condition
from .type_def import E, T
from .v1 import LoadMixin
from .v1.enums import KeyAction, KeyCase, DateTimeTo as V1DateTimeTo, EnvPrecedence, EnvKeyStrategy
from .v1.models import TypeInfo, Extras
from .v1._path_util import EnvFilePaths, SecretsDirs

ALLOWED_MODES = Literal['runtime', 'v1_codegen']

# global flag to determine if debug mode was ever enabled
_debug_was_enabled = False

V1HookFn = Callable[..., Any]

L = TypeVar('L', bound=LoadMixin)

# (cls, container_tp, tp, extras) -> new_tp
V1PreDecoder: TypeAlias = Callable[[L, type | None, TypeInfo, Extras], TypeInfo]


def register_type(cls, tp: type, *,
                  load: 'V1HookFn | None' = None,
                  dump: 'V1HookFn | None' = None,
                  mode: str | None = None) -> None: ...


def _enable_debug_mode_if_needed(cls_loader, possible_lvl: bool | int | str):
    ...


def _as_enum_safe(cls: type, name: str, base_type: type[E]) -> E | None:
    ...


class BaseJSONWizardMeta(AbstractMeta):

    __slots__ = ()

    @classmethod
    def _init_subclass(cls):
        ...

    @classmethod
    def bind_to(cls, dataclass: type, create=True, is_default=True,
                base_loader=None, base_dumper=None):
        ...


class BaseEnvWizardMeta(AbstractEnvMeta):

    __slots__ = ()

    @classmethod
    def _init_subclass(cls):
        ...

    @classmethod
    def bind_to(cls, env_class: type, create=True, is_default=True):
        ...


# noinspection PyPep8Naming
def LoadMeta(*,
             debug_enabled: 'bool | int | str' = MISSING,
             recursive: bool = True,
             # -- BEGIN Deprecated Fields --
             recursive_classes: bool = MISSING,
             raise_on_unknown_json_key: bool = MISSING,
             json_key_to_field: dict[str, str] = MISSING,
             key_transform: LetterCase | str = MISSING,
             # -- END Deprecated Fields --
             tag: str = MISSING,
             tag_key: str = TAG,
             auto_assign_tags: bool = MISSING,
             v1: bool = MISSING,
             v1_debug: bool | int | str = False,
             v1_type_to_hook: V1TypeToHook = MISSING,
             v1_pre_decoder: V1PreDecoder = MISSING,
             v1_case: KeyCase | str | None = MISSING,
             v1_field_to_alias: Mapping[str, str | Sequence[str]] = MISSING,
             v1_on_unknown_key: KeyAction | str | None = KeyAction.IGNORE,
             v1_unsafe_parse_dataclass_in_union: bool = MISSING,
             v1_namedtuple_as_dict: bool = MISSING,
             v1_coerce_none_to_empty_str: bool = MISSING,
             v1_leaf_handling: Literal['exact', 'issubclass'] = MISSING) -> T | META:
    ...


# noinspection PyPep8Naming
def DumpMeta(*,
             debug_enabled: 'bool | int | str' = MISSING,
             recursive: bool = True,
             # -- BEGIN Deprecated Fields --
             marshal_date_time_as: DateTimeTo | str = MISSING,
             key_transform: LetterCase | str = MISSING,
             # -- END Deprecated Fields --
             tag: str = MISSING,
             skip_defaults: bool = MISSING,
             skip_if: Condition = MISSING,
             skip_defaults_if: Condition = MISSING,
             v1: bool = MISSING,
             v1_debug: bool | int | str = False,
             v1_type_to_hook: V1TypeToHook = MISSING,
             v1_case: KeyCase | str | None = MISSING,
             v1_field_to_alias: Mapping[str, str | Sequence[str]] = MISSING,
             v1_dump_date_time_as: V1DateTimeTo | str = MISSING,
             v1_assume_naive_datetime_tz: tzinfo | None = MISSING,
             v1_namedtuple_as_dict: bool = MISSING,
             v1_leaf_handling: Literal['exact', 'issubclass'] = MISSING) -> T | META:
    ...


# noinspection PyPep8Naming
def EnvMeta(*, debug_enabled: 'bool | int | str' = MISSING,
            recursive: bool = True,
            env_file: EnvFilePaths = MISSING,
            env_prefix: str = MISSING,
            secrets_dir: SecretsDirs = MISSING,
            # -- BEGIN Deprecated Fields --
            field_to_env_var: dict[str, str] = MISSING,
            key_lookup_with_load: LetterCasePriority | str = LetterCasePriority.SCREAMING_SNAKE,
            key_transform_with_dump: LetterCase | str = LetterCase.SNAKE,
            # -- END Deprecated Fields --
            skip_defaults: bool = MISSING,
            skip_if: Condition = MISSING,
            skip_defaults_if: Condition = MISSING,
            tag: str = MISSING,
            tag_key: str = TAG,
            auto_assign_tags: bool = MISSING,
            v1: bool = MISSING,
            v1_debug: bool | int | str = False,
            v1_type_to_load_hook: V1TypeToHook = MISSING,
            v1_type_to_dump_hook: V1TypeToHook = MISSING,
            v1_pre_decoder: V1PreDecoder = MISSING,
            v1_load_case: EnvKeyStrategy | str = MISSING,
            v1_dump_case: LetterCase | str = MISSING,
            v1_env_precedence: EnvPrecedence = MISSING,
            v1_field_to_env_load: Mapping[str, str | Sequence[str]] = MISSING,
            v1_field_to_alias_dump: Mapping[str, str | Sequence[str]] = MISSING,
            # v1_on_unknown_key: KeyAction | str | None = KeyAction.IGNORE,
            v1_unsafe_parse_dataclass_in_union: bool = MISSING,
            v1_dump_date_time_as: V1DateTimeTo | str = MISSING,
            v1_assume_naive_datetime_tz: tzinfo | None = MISSING,
            v1_namedtuple_as_dict: bool = MISSING,
            v1_coerce_none_to_empty_str: bool = MISSING,
            v1_leaf_handling: Literal['exact', 'issubclass'] = MISSING) -> META:
    ...
