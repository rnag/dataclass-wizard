"""
JSON Helper Utilities - *only* internally used in ``errors.py``,
i.e. for rendering exceptions.

.. NOTE::
    This module should not be imported anywhere at the *top-level*
    of another library module!

"""
__all__ = [
    'safe_dumps',
]

from dataclasses import is_dataclass
from datetime import datetime, time, date
from enum import Enum
from json import dumps, JSONEncoder
from typing import Any
from uuid import UUID

from ..dumpers import asdict


class SafeEncoder(JSONEncoder):
    """
    A Customized JSON Encoder, which copies core logic in the
    `dumpers` module to support serialization of more complex
    Python types, such as `datetime` and `Enum`.
    """

    def default(self, o: Any) -> Any:
        """Default function, copies the core (minimal) logic from `dumpers.py`."""

        if is_dataclass(o):
            return asdict(o)

        if isinstance(o, Enum):
            return o.value

        if isinstance(o, UUID):
            return o.hex

        if isinstance(o, (datetime, time)):
            return o.isoformat().replace('+00:00', 'Z', 1)

        if isinstance(o, date):
            return o.isoformat()

        # anything else (Decimal, timedelta, etc.)
        return str(o)


def safe_dumps(o, cls=SafeEncoder, **kwargs):
    return dumps(o, cls=cls, **kwargs)
