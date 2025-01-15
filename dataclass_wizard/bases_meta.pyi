"""
Ideally should be in the `bases` module, however we'll run into a Circular
Import scenario if we move it there, since the `loaders` and `dumpers` modules
both import directly from `bases`.

"""
from dataclasses import MISSING
from typing import Sequence

from .bases import AbstractMeta, META, AbstractEnvMeta
from .constants import TAG
from .enums import DateTimeTo, LetterCase, LetterCasePriority
from .v1.enums import KeyAction, KeyCase
from .models import Condition
from .type_def import E, EnvFileType


# global flag to determine if debug mode was ever enabled
_debug_was_enabled = False


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
                base_loader=None):
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
def LoadMeta(*, debug_enabled: 'bool | int | str' = MISSING,
             recursive: bool = True,
             recursive_classes: bool = MISSING,
             raise_on_unknown_json_key: bool = MISSING,
             json_key_to_field: dict[str, str] = MISSING,
             key_transform: LetterCase | str = MISSING,
             tag: str = MISSING,
             tag_key: str = TAG,
             auto_assign_tags: bool = MISSING,
             v1: bool = MISSING,
             v1_debug: bool | int | str = False,
             v1_key_case: KeyCase | str | None = MISSING,
             v1_field_to_alias: dict[str, str | Sequence[str]] = MISSING,
             v1_on_unknown_key: KeyAction | str | None = KeyAction.IGNORE,
             v1_unsafe_parse_dataclass_in_union: bool = MISSING) -> META:
    ...


# noinspection PyPep8Naming
def DumpMeta(*, debug_enabled: 'bool | int | str' = MISSING,
             recursive: bool = True,
             marshal_date_time_as: DateTimeTo | str = MISSING,
             key_transform: LetterCase | str = MISSING,
             tag: str = MISSING,
             skip_defaults: bool = MISSING,
             skip_if: Condition = MISSING,
             skip_defaults_if: Condition = MISSING,
             ) -> META:
    ...


# noinspection PyPep8Naming
def EnvMeta(*, debug_enabled: 'bool | int | str' = MISSING,
             env_file: EnvFileType = MISSING,
             env_prefix: str = MISSING,
             secrets_dir: 'EnvFileType | Sequence[EnvFileType]' = MISSING,
             field_to_env_var: dict[str, str] = MISSING,
             key_lookup_with_load: LetterCasePriority | str = LetterCasePriority.SCREAMING_SNAKE,
             key_transform_with_dump: LetterCase | str = LetterCase.SNAKE,
             # marshal_date_time_as: DateTimeTo | str = MISSING,
             skip_defaults: bool = MISSING,
             skip_if: Condition = MISSING,
             skip_defaults_if: Condition = MISSING,
             ) -> META:
    ...
