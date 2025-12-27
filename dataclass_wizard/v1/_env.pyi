import json
from dataclasses import dataclass, Field, InitVar
from typing import (Callable, Mapping, dataclass_transform, TypedDict,
                    NotRequired, TypeVar, ClassVar, Collection, AnyStr)

from .loaders import LoadMixin as V1LoadMixIn
from .models import Extras
from ..bases import AbstractEnvMeta, ENV_META
from ..bases_meta import BaseEnvWizardMeta, V1HookFn
from ..type_def import Unpack, JSONObject, T, Encoder

E_ = TypeVar('E_', bound=EnvWizard)
E = type[E_]


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

    class Meta(BaseEnvWizardMeta):
        """
        Inner meta class that can be extended by sub-classes for additional
        customization with the environment load process.
        """
        __slots__ = ()
        __is_inner_meta__ = True
        def __init_subclass__(cls): ...

    __field_names__: ClassVar[tuple[str, ...]]

    def __init_subclass__(cls,
                          debug: bool = False,
                          _apply_dataclass=True,
                          **dc_kwargs): ...

    @classmethod
    def register_type(cls, tp: type, *,
                      load: V1HookFn | None = None,
                      dump: V1HookFn | None = None,
                      mode: str | None = None) -> None:
        ...

    def raw_dict(self: E_) -> JSONObject: ...

    def to_dict(self: E_,
                *,
                dict_factory=dict,
                exclude: Collection[str] | None = None,
                skip_defaults: bool | None = None,
                ) -> JSONObject:
        """
        Converts the dataclass instance to a Python dictionary object that is
        JSON serializable.

        Example usage:

          class C(EnvWizard):
              x: int
              y: int
              z: bool = True

          c = C(1, 2, True)
          assert c.to_dict(skip_defaults=True) == {'x': 1, 'y': 2}

        If given, 'dict_factory' will be used instead of built-in dict.
        The function applies recursively to field values that are
        dataclass instances. This will also look into built-in containers:
        tuples, lists, and dicts.
        """
        # alias: asdict(self)
        ...

    def to_json(self: E_, *,
                encoder: Encoder = json.dumps,
                **encoder_kwargs) -> AnyStr:
        """
        Converts the dataclass instance to a JSON `string` representation.
        """
        ...

def load_func_for_dataclass(
        cls: E,
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

class LoadMixin(V1LoadMixIn): ...
