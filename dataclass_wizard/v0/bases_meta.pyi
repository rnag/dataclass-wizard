"""
Ideally should be in the `bases` module, however we'll run into a Circular
Import scenario if we move it there, since the `loaders` and `dumpers` modules
both import directly from `bases`.

"""
from dataclasses import MISSING
from datetime import tzinfo
from os import PathLike
from typing import Sequence, Callable, Any, Literal, TypeAlias, TypeVar, Mapping

from .bases import AbstractMeta, META, AbstractEnvMeta, V1TypeToHook
from .constants import TAG
from .enums import DateTimeTo, LetterCase, LetterCasePriority
from .models import Condition
from .type_def import E, T
from .loaders import LoadMixin


# global flag to determine if debug mode was ever enabled
_debug_was_enabled = False

SecretsDir = str | PathLike[str]
SecretsDirs = SecretsDir | Sequence[SecretsDir] | None

EnvFilePath = str | PathLike[str]
EnvFilePaths = bool | EnvFilePath | Sequence[EnvFilePath] | None

V1HookFn = Callable[..., Any]

L = TypeVar('L', bound=LoadMixin)


def register_type(cls, tp: type, *,
                  load: 'V1HookFn | None' = None,
                  dump: 'V1HookFn | None' = None) -> None: ...


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
             auto_assign_tags: bool = MISSING) -> T | META:
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
             skip_defaults_if: Condition = MISSING) -> T | META:
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
            auto_assign_tags: bool = MISSING) -> META:
    ...
