from __future__ import annotations

import json

from collections import Counter
from collections.abc import Mapping
from typing import TYPE_CHECKING, TypeVar

from dataclass_wizard.v1 import env_config


if TYPE_CHECKING:
    from dataclass_wizard.v1._env import EnvInit
    T = TypeVar('T')


def envsafe(mapping: Mapping, *, dumps=json.dumps) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in mapping.items():
        k = str(k)
        out[k] = v if isinstance(v, str) else dumps(v, separators=(",", ":"), sort_keys=True, default=str)
    return out


def from_env(cls: type[T], mapping: Mapping=None, env_cfg: EnvInit=None, **init_kwargs) -> T:
    env_map = envsafe(mapping or {})
    return cls(__env__=env_config(mapping=env_map, **(env_cfg or {})), **init_kwargs)


def assert_unordered_equal(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        assert a.keys() == b.keys()
        for k in a:
            assert_unordered_equal(a[k], b[k])
        return

    if isinstance(a, list) and isinstance(b, list):
        # compare as multisets, recursively
        def freeze(x):
            if isinstance(x, dict):
                return "dict", tuple(sorted((k, freeze(v)) for k, v in x.items()))
            if isinstance(x, list):
                # treat nested lists as unordered too
                return "list", tuple(sorted(freeze(v) for v in x))
            return "atom", x

        assert Counter(map(freeze, a)) == Counter(map(freeze, b))
        return

    assert a == b
