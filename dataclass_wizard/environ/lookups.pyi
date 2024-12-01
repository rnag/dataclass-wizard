from dataclasses import MISSING
from typing import ClassVar

from ..decorators import cached_class_property
from ..type_def import StrCollection, EnvFileType


type _MISSING_TYPE = type(MISSING)
type STR_OR_MISSING = str | _MISSING_TYPE
type STR_OR_NONE = str | None

# Type of `os.environ` or `DotEnv` dict
Environ = dict[str, STR_OR_NONE]

# Type of (unique) environment variable names
EnvVars = set[str]


environ: Environ


# noinspection PyMethodParameters
class Env:

    __slots__ = ()

    _accessed_cleaned_to_env: ClassVar[bool] = False

    var_names: EnvVars

    @classmethod
    def load_environ(cls, force_reload=False) -> None: ...

    @classmethod
    def reload(cls, env: dict | None = None): ...

    @classmethod
    def secret_values(cls, dirs: EnvFileType) -> Environ: ...

    @classmethod
    def update_with_secret_values(cls, dirs: EnvFileType): ...

    @classmethod
    def dotenv_values(cls, files: EnvFileType) -> Environ: ...

    @classmethod
    def update_with_dotenv(cls, files: EnvFileType = '.env',
                           dotenv_values=None): ...

    # noinspection PyDunderSlots,PyUnresolvedReferences
    @cached_class_property
    def cleaned_to_env(cls) -> Environ: ...


def clean(s: str) -> str: ...
def try_cleaned(key: str) -> STR_OR_MISSING: ...
def lookup_exact(var: StrCollection) -> STR_OR_MISSING: ...
def with_screaming_snake_case(field_name: str) -> STR_OR_MISSING: ...
def with_snake_case(field_name: str) -> STR_OR_MISSING: ...
def with_pascal_or_camel_case(field_name: str) -> STR_OR_MISSING: ...
