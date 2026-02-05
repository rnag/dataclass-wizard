"""
Ideally should be in the `bases` module, however we'll run into a Circular
Import scenario if we move it there, since the `loaders` and `dumpers` modules
both import directly from `bases`.

"""
from datetime import tzinfo
from typing import Sequence, Callable, Any, Literal, TypeAlias, TypeVar, Mapping

from ._path_util import EnvFilePaths, SecretsDirs
from ._bases import AbstractMeta, AbstractEnvMeta, TypeToHook
from .constants import TAG
from .enums import KeyAction, KeyCase, DateTimeTo, EnvPrecedence, EnvKeyStrategy
from ._loaders import LoadMixin
from .models import Condition
from .models import TypeInfo, Extras
from ._type_def import META, ENV_META, E, T


ALLOWED_MODES = Literal['runtime', 'codegen']

# global flag to determine if debug mode was ever enabled
_debug_was_enabled = False

HookFn = Callable[..., Any]

L = TypeVar('L', bound=LoadMixin)

# (cls, container_tp, tp, extras) -> new_tp
PreDecoder: TypeAlias = Callable[[L, type | None, TypeInfo, Extras], TypeInfo]


def register_type(cls, tp: type, *,
                  load: HookFn | None = None,
                  dump: HookFn | None = None,
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
             debug: bool | int | str = ...,
             recursive: bool = True,
             tag: str = ...,
             tag_key: str = TAG,
             auto_assign_tags: bool = ...,
             type_to_hook: TypeToHook = ...,
             pre_decoder: PreDecoder = ...,
             case: KeyCase | str | None = ...,
             field_to_alias: Mapping[str, str | Sequence[str]] = ...,
             on_unknown_key: KeyAction | str | None = KeyAction.IGNORE,
             unsafe_parse_dataclass_in_union: bool = ...,
             namedtuple_as_dict: bool = ...,
             coerce_none_to_empty_str: bool = ...,
             leaf_handling: Literal['exact', 'issubclass'] = ...) -> META:
    ...


# noinspection PyPep8Naming
def DumpMeta(*,
             debug: bool | int | str = ...,
             recursive: bool = True,
             tag: str = ...,
             skip_defaults: bool = ...,
             skip_if: Condition = ...,
             skip_defaults_if: Condition = ...,
             type_to_hook: TypeToHook = ...,
             case: KeyCase | str | None = ...,
             field_to_alias: Mapping[str, str | Sequence[str]] = ...,
             dump_date_time_as: DateTimeTo | str = ...,
             assume_naive_datetime_tz: tzinfo | None = ...,
             namedtuple_as_dict: bool = ...,
             leaf_handling: Literal['exact', 'issubclass'] = ...) -> META:
    ...


# noinspection PyPep8Naming
def EnvMeta(*,
            debug: bool | int | str = ...,
            recursive: bool = True,
            env_file: EnvFilePaths = ...,
            env_prefix: str = ...,
            secrets_dir: SecretsDirs = ...,
            skip_defaults: bool = ...,
            skip_if: Condition = ...,
            skip_defaults_if: Condition = ...,
            tag: str = ...,
            tag_key: str = TAG,
            auto_assign_tags: bool = ...,
            type_to_load_hook: TypeToHook = ...,
            type_to_dump_hook: TypeToHook = ...,
            pre_decoder: PreDecoder = ...,
            load_case: EnvKeyStrategy | str = ...,
            dump_case: KeyCase | str = ...,
            env_precedence: EnvPrecedence = ...,
            field_to_env_load: Mapping[str, str | Sequence[str]] = ...,
            field_to_alias_dump: Mapping[str, str | Sequence[str]] = ...,
            # on_unknown_key: KeyAction | str | None = KeyAction.IGNORE,
            unsafe_parse_dataclass_in_union: bool = ...,
            dump_date_time_as: DateTimeTo | str = ...,
            assume_naive_datetime_tz: tzinfo | None = ...,
            namedtuple_as_dict: bool = ...,
            coerce_none_to_empty_str: bool = ...,
            leaf_handling: Literal['exact', 'issubclass'] = ...) -> ENV_META:
    ...
