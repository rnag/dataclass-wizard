"""
Ideally should be in the `bases` module, however we'll run into a Circular
Import scenario if we move it there, since the `loaders` and `dumpers` modules
both import directly from `bases`.

"""
from dataclasses import MISSING
from datetime import tzinfo
from typing import Sequence, Callable, Any, Literal, TypeAlias, TypeVar, Mapping

from ._path_util import EnvFilePaths, SecretsDirs
from .bases import AbstractMeta, META, AbstractEnvMeta, V1TypeToHook
from .constants import TAG
from .enums import KeyAction, KeyCase, DateTimeTo, EnvPrecedence, EnvKeyStrategy
from .loaders import LoadMixin
from .models import Condition
from .models import TypeInfo, Extras
from .type_def import E, T


ALLOWED_MODES = Literal['runtime', 'codegen']

# global flag to determine if debug mode was ever enabled
_debug_was_enabled = False

HookFn = Callable[..., Any]

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
             debug: bool | int | str = MISSING,
             recursive: bool = True,
             tag: str = MISSING,
             tag_key: str = TAG,
             auto_assign_tags: bool = MISSING,
             type_to_hook: V1TypeToHook = MISSING,
             pre_decoder: V1PreDecoder = MISSING,
             case: KeyCase | str | None = MISSING,
             field_to_alias: Mapping[str, str | Sequence[str]] = MISSING,
             on_unknown_key: KeyAction | str | None = KeyAction.IGNORE,
             unsafe_parse_dataclass_in_union: bool = MISSING,
             namedtuple_as_dict: bool = MISSING,
             coerce_none_to_empty_str: bool = MISSING,
             leaf_handling: Literal['exact', 'issubclass'] = MISSING) -> T | META:
    ...


# noinspection PyPep8Naming
def DumpMeta(*,
             debug: bool | int | str = MISSING,
             recursive: bool = True,
             tag: str = MISSING,
             skip_defaults: bool = MISSING,
             skip_if: Condition = MISSING,
             skip_defaults_if: Condition = MISSING,
             type_to_hook: V1TypeToHook = MISSING,
             case: KeyCase | str | None = MISSING,
             field_to_alias: Mapping[str, str | Sequence[str]] = MISSING,
             dump_date_time_as: DateTimeTo | str = MISSING,
             assume_naive_datetime_tz: tzinfo | None = MISSING,
             namedtuple_as_dict: bool = MISSING,
             leaf_handling: Literal['exact', 'issubclass'] = MISSING) -> T | META:
    ...


# noinspection PyPep8Naming
def EnvMeta(*,
            debug: bool | int | str = MISSING,
            recursive: bool = True,
            env_file: EnvFilePaths = MISSING,
            env_prefix: str = MISSING,
            secrets_dir: SecretsDirs = MISSING,
            skip_defaults: bool = MISSING,
            skip_if: Condition = MISSING,
            skip_defaults_if: Condition = MISSING,
            tag: str = MISSING,
            tag_key: str = TAG,
            auto_assign_tags: bool = MISSING,
            type_to_load_hook: V1TypeToHook = MISSING,
            type_to_dump_hook: V1TypeToHook = MISSING,
            pre_decoder: V1PreDecoder = MISSING,
            load_case: EnvKeyStrategy | str = MISSING,
            dump_case: KeyCase | str = MISSING,
            env_precedence: EnvPrecedence = MISSING,
            field_to_env_load: Mapping[str, str | Sequence[str]] = MISSING,
            field_to_alias_dump: Mapping[str, str | Sequence[str]] = MISSING,
            # on_unknown_key: KeyAction | str | None = KeyAction.IGNORE,
            unsafe_parse_dataclass_in_union: bool = MISSING,
            dump_date_time_as: DateTimeTo | str = MISSING,
            assume_naive_datetime_tz: tzinfo | None = MISSING,
            namedtuple_as_dict: bool = MISSING,
            coerce_none_to_empty_str: bool = MISSING,
            leaf_handling: Literal['exact', 'issubclass'] = MISSING) -> META:
    ...
