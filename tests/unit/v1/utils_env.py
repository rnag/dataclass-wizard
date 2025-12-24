import json
from collections.abc import Mapping
from typing import TYPE_CHECKING, Unpack, TypeVar

from dataclass_wizard.v1 import env_config


if TYPE_CHECKING:
    from dataclass_wizard.v1.env import EnvInit
    T = TypeVar('T')


def envsafe(mapping: Mapping, *, dumps=json.dumps) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in mapping.items():
        k = str(k)
        out[k] = v if isinstance(v, str) else dumps(v, separators=(",", ":"), sort_keys=True)
    return out


def from_env(cls: type[T], mapping: Mapping, **envcfg_kwargs: Unpack[EnvInit]) -> T:
    return cls(__env__=env_config(mapping=envsafe(mapping), **envcfg_kwargs))
