from dataclasses import dataclass, Field, InitVar
from typing import Callable, Mapping, dataclass_transform, TypedDict, NotRequired

from .loaders import LoadMixin as V1LoaderMixIn
from .models import Extras
from ..bases import AbstractEnvMeta, ENV_META
from ..bases_meta import BaseEnvWizardMeta
from ..type_def import Unpack, JSONObject, T


class EnvInit(TypedDict, total=False):
    mapping: NotRequired[Mapping[str, str]]
    file: NotRequired[str | list[str] | bool]
    prefix: NotRequired[str]
    secrets_dir: NotRequired[str | list[str]]


def env_config(**kw: Unpack[EnvInit]) -> EnvInit:
    return kw


@dataclass_transform(kw_only_default=True)
@dataclass()
class EnvWizard:
    __slots__ = ()
    __env__: InitVar[EnvInit | None] = None
    eve: EnvInit | None = None

    class Meta(BaseEnvWizardMeta):
        """
        Inner meta class that can be extended by sub-classes for additional
        customization with the environment load process.
        """
        __slots__ = ()
        __is_inner_meta__ = True
        def __init_subclass__(cls): ...

    def __init_subclass__(cls, debug: bool = False, **kwargs): ...


def load_func_for_dataclass(
        cls: type,
        extras: Extras | None = None,
        loader_cls=None,
        base_meta_cls: ENV_META = AbstractEnvMeta,
) -> Callable[[JSONObject], T] | None: ...

def _add_missing_var(missing_vars: dict | None, name, env_prefix, var_name, tp): ...

def generate_field_code(cls_loader: LoadMixin,
                        extras: Extras,
                        field: Field,
                        field_i: int) -> 'str | TypeInfo': ...

def re_raise(e, cls, o, fields, field, value): ...

class LoadMixin(V1LoaderMixIn): ...

def check_and_raise_missing_fields(
        _locals, o, cls,
        fields: tuple[Field, ...] | None): ...
