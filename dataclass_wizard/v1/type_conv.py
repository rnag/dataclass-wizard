from __future__ import annotations

__all__ = ['TRUTHY_VALUES',
           'as_int_v1',
           'as_datetime_v1',
           'as_date_v1',
           'as_time_v1',
           'as_timedelta',
           'datetime_to_timestamp',
           'as_collection_v1',
           'as_list_v1',
           'as_dict_v1',
           ]

import csv

from collections.abc import Callable
from datetime import datetime, time, date, timedelta, timezone, tzinfo
from json import loads, JSONDecodeError
from typing import Union, Any

from ..lazy_imports import pytimeparse
from ..type_def import N, NUMBERS
from ..v1.models import ZERO, UTC


# What values are considered "truthy" when converting to a boolean type.
# noinspection SpellCheckingInspection
TRUTHY_VALUES = frozenset({'true', 't', 'yes', 'y', 'on', '1'})


def as_int_v1(o: Union[float, bool],
              tp: type,
              base_type=int):
    """
    Attempt to convert `o` to an int.

    This assumes the following checks already happen:
        - `tp is base_type`
        - `tp is str and '.' in o and float(o).is_integer()`
        - `tp is str and '.' in o and not float(o).is_integer()` --> IMPLIED
        - `tp is str and '.' not in o`

    If `o` cannot be converted to an int, raise an error.

    :raises TypeError: If `o` is a `bool` (which is an `int` subclass)
    :raises ValueError: When `o` cannot be converted to an `int`
    """
    # Commenting this out, because `int(o)` already raises an error
    # for float strings with a fractional part.
    # if tp is str:  # The string represents a float value with fractional part, e.g. '2.7'
    #     raise ValueError(f"Cannot cast string float with fractional part: {o}") from None

    if tp is float:
        if o.is_integer():
            return base_type(o)
        raise ValueError(f"Cannot cast float with fractional part: {o}") from None

    if tp is bool:
        raise TypeError(f'as_int: Incorrect type, object={o!r}, type={tp}') from None

    try:
        return base_type(o)

    except (TypeError, ValueError):
        raise


def as_datetime_v1(o: Union[int, float, datetime],
                   __from_timestamp: Callable[[float, tzinfo], datetime],
                   __tz=None):
    """
    V1: Attempt to convert an object `o` to a :class:`datetime` object using the
    below logic.

        * ``Number`` (int or float): Convert a numeric timestamp via the
            built-in ``fromtimestamp`` method, and return a UTC datetime.
        * ``base_type``: Return object `o` if it's already of this type.

    Note: It is assumed that `o` is not a ``str`` (in ISO format), as
    de-serialization in ``v1`` already checks for this.

    Otherwise, if we're unable to convert the value of `o` to a
    :class:`datetime` as expected, raise an error.

    """
    try:
        # We can assume that `o` is a number, as generally this will be the
        # case.
        return __from_timestamp(o, __tz)

    except Exception:
        # Note: the `__self__` attribute refers to the class bound
        # to the class method `fromtimestamp`.
        #
        # See: https://stackoverflow.com/a/41258933/10237506
        #
        # noinspection PyUnresolvedReferences
        if o.__class__ is __from_timestamp.__self__:
            return o

        # Check `type` explicitly, because `bool` is a sub-class of `int`
        if o.__class__ not in NUMBERS:
            raise TypeError(f'Unsupported type, value={o!r}, type={type(o)}')

        raise


def as_date_v1(o: Union[int, float, date],
               __from_timestamp: Callable[[float, tzinfo], datetime],
               __tz=None,
               __cls=date):
    """
    V1: Attempt to convert an object `o` to a :class:`date` object using the
    below logic.

        * ``Number`` (int or float): Convert a numeric timestamp via the
            built-in ``fromtimestamp`` method, and return a date.
        * ``base_type``: Return object `o` if it's already of this type.

    Note: It is assumed that `o` is not a ``str`` (in ISO format), as
    de-serialization in ``v1`` already checks for this.

    Otherwise, if we're unable to convert the value of `o` to a
    :class:`date` as expected, raise an error.

    """
    try:
        # We can assume that `o` is a number, as generally this will be the
        # case.
        return __from_timestamp(o, __tz).date()

    except Exception:
        # Note: the `__self__` attribute refers to the class bound
        # to the class method `fromtimestamp`.
        #
        # See: https://stackoverflow.com/a/41258933/10237506
        #
        # noinspection PyUnresolvedReferences
        if o.__class__ is __cls:
            return o

        # Check `type` explicitly, because `bool` is a sub-class of `int`
        if o.__class__ not in NUMBERS:
            raise TypeError(f'Unsupported type, value={o!r}, type={type(o)}')

        raise

# Fix for: https://github.com/rnag/dataclass-wizard/issues/206
#
# def as_date_v1_utc(o: Union[int, float, date],
#                    __base_cls=date,
#                    __tz=UTC,
#                    __dt_from_timestamp: Callable[[float], datetime] = datetime.fromtimestamp):
#     """
#     V1: Attempt to convert an object `o` to a :class:`date` object using the
#     below logic.
#
#         * ``Number`` (int or float): Convert a numeric timestamp via the
#             built-in ``fromtimestamp`` method, and return a date.
#         * ``base_type``: Return object `o` if it's already of this type.
#
#     Note: It is assumed that `o` is not a ``str`` (in ISO format), as
#     de-serialization in ``v1`` already checks for this.
#
#     Otherwise, if we're unable to convert the value of `o` to a
#     :class:`date` as expected, raise an error.
#
#     """
#     try:
#         # We can assume that `o` is a number, as generally this will be the
#         # case.
#         # noinspection PyArgumentList
#         return __dt_from_timestamp(o, __tz).date()
#
#     except Exception:
#         # Note: the `__self__` attribute refers to the class bound
#         # to the class method `fromtimestamp`.
#         #
#         # See: https://stackoverflow.com/a/41258933/10237506
#         #
#         # noinspection PyUnresolvedReferences
#         if o.__class__ is __base_cls:
#             return o
#
#         # Check `type` explicitly, because `bool` is a sub-class of `int`
#         if o.__class__ not in NUMBERS:
#             raise TypeError(f'Unsupported type, value={o!r}, type={type(o)}')
#
#         raise


def as_time_v1(o: Union[time, Any], base_type: type[time]):
    """
    V1: Attempt to convert an object `o` to a :class:`time` object using the
    below logic.

        * ``base_type``: Return object `o` if it's already of this type.

    Note: It is assumed that `o` is not a ``str`` (in ISO format), as
    de-serialization in ``v1`` already checks for this.

    Otherwise, if we're unable to convert the value of `o` to a
    :class:`time` as expected, raise an error.

    """
    if o.__class__ is base_type:
        return o

    raise TypeError(f'Unsupported type, value={o!r}, type={type(o)}')


def as_timedelta(o: Union[str, N, timedelta],
                 base_type=timedelta, default=None, raise_=True):
    """
    Attempt to convert an object `o` to a :class:`timedelta` object using the
    below logic.

        * ``str``: If the string is in a numeric form like "1.23", we convert
          it to a ``float`` and assume it's in seconds. Otherwise, we convert
          strings via the ``pytimeparse.parse`` function.
        * ``int`` or ``float``: A numeric value is assumed to be in seconds.
          In this case, it is passed in to the constructor like
          ``timedelta(seconds=...)``
        * ``timedelta``: Return object `o` if it's already of this type or
            sub-type.

    Otherwise, if we're unable to convert the value of `o` to a
    :class:`timedelta` as expected, raise an error if the `raise_` parameter
    is true; if not, return `default` instead.

    """

    t = type(o)

    if t is str:
        # Check if the string represents a numeric value like "1.23"
        # Ref: https://stackoverflow.com/a/23639915/10237506
        if o.replace('.', '', 1).isdigit():
            seconds = float(o)
        else:
            # Otherwise, parse strings using `pytimeparse`
            seconds = pytimeparse.parse(o)

    # Check `type` explicitly, because `bool` is a sub-class of `int`
    elif t in NUMBERS:
        seconds = o

    elif t is base_type:
        return o

    elif raise_:
        raise TypeError(f'Unsupported type, value={o!r}, type={t}')

    else:
        return default

    try:
        return timedelta(seconds=seconds)

    except TypeError:
        raise ValueError(f'Invalid value for timedelta, value={o!r}')


def datetime_to_timestamp(dt: datetime, assume_naive_tz: timezone) -> int:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=assume_naive_tz)

    if dt.utcoffset() == ZERO:
        return int(dt.timestamp())

    return int(dt.astimezone(UTC).timestamp())


def _looks_like_json(s: str, stripped=False) -> bool:
    # Fast/cheap heuristic; avoids json.loads on most env strings
    if not stripped:
        s = s.lstrip()
        return bool(s) and s[0] in '[{'

    return s[0] in '[{'


def _csv_split(s: str, sep: str) -> list[str]:
    # csv handles quoting and escaped quotes well
    # Note: csv expects 1-char delimiter; enforce at Meta level.
    row = next(csv.reader([s], delimiter=sep, skipinitialspace=True))
    return row


def as_collection_v1(
    v: Any,
    *,
    strip: bool = True,
) -> Any:
    """
    If v is a str:
      - If it looks like JSON array or dictionary: parse JSON (must be valid)
    Otherwise return v unchanged.
    """
    if not isinstance(v, str):
        return v

    s = v.strip() if strip else v
    if not s:
        return []

    if _looks_like_json(s, strip):
        try:
            out = loads(s)
        except JSONDecodeError as e:
            raise ValueError(f'Invalid JSON for collection value: {s!r}') from e
        if not isinstance(out, (list, dict)):
            raise ValueError(f'Expected JSON array or dictionary for value, got {type(out).__name__}')
        return out

    return s


def as_list_v1(
    v: Any,
    *,
    sep: str = ",",
    strip: bool = True,
    drop_empty: bool = True,
    json_enabled: bool = True,
) -> Any:
    """
    If v is a str:
      - If it looks like JSON array and json_enabled: parse JSON (must be valid)
      - Else parse a delimited list; supports quotes via csv when needed
    Otherwise return v unchanged.
    """
    if not isinstance(v, str):
        return v

    s = v.strip() if strip else v
    if not s:
        return [] if drop_empty else ['']

    if json_enabled and _looks_like_json(s, strip):
        try:
            out = loads(s)
        except JSONDecodeError as e:
            raise ValueError(f'Invalid JSON for list value: {s!r}') from e
        if not isinstance(out, list):
            raise ValueError(f'Expected JSON array for list value, got {type(out).__name__}')
        return out

    # Fast path: no quotes -> split() is much faster than csv
    if '"' not in s and "'" not in s:
        parts = s.split(sep)
    else:
        if len(sep) != 1:
            raise ValueError('sep must be a single character when quoted parsing is needed')
        parts = _csv_split(s, sep)

    if strip:
        parts = [p.strip() for p in parts]
    if drop_empty:
        parts = [p for p in parts if p != '']
    return parts


def as_dict_v1(
    v: Any,
    *,
    sep: str = ",",
    kv_sep: str = "=",
    strip: bool = True,
    drop_empty: bool = True,
    json_enabled: bool = True,
    allow_bare_keys: bool = False,
) -> Any:
    """
    If v is a str:
      - If it looks like JSON object and json_enabled: parse JSON (must be valid)
      - Else parse "k=v, k2=v2" style; supports quotes around keys/values
    Otherwise return v unchanged.

    Notes:
      - Duplicate keys: last one wins (simple + predictable).
      - If allow_bare_keys=True, allow "FLAG" -> {"FLAG": ""} (or None)
    """
    if not isinstance(v, str):
        return v

    s = v.strip() if strip else v
    if not s:
        return {}

    if json_enabled and _looks_like_json(s, strip):
        try:
            out = loads(s)
        except JSONDecodeError as e:
            raise ValueError(f'Invalid JSON for dict value: {s!r}') from e
        if not isinstance(out, dict):
            raise ValueError(f'Expected JSON object for dict value, got {type(out).__name__}')
        return out

    # Split into pairs (with quoting support when needed)
    if '"' not in s and "'" not in s:
        pairs = s.split(sep)
    else:
        if len(sep) != 1:
            raise ValueError('sep must be a single character when quoted parsing is needed')
        pairs = _csv_split(s, sep)

    out: dict[str, str] = {}
    for pair in pairs:
        if strip:
            pair = pair.strip()
        if drop_empty and not pair:
            continue

        if kv_sep in pair:
            k, val = pair.split(kv_sep, 1)
            if strip:
                k = k.strip()
                val = val.strip()
            if drop_empty and not k:
                continue
            out[k] = val
        else:
            if not allow_bare_keys:
                raise ValueError(f'Invalid dict token (missing {kv_sep!r}): {pair!r}')
            k = pair.strip() if strip else pair
            if drop_empty and not k:
                continue
            out[k] = ''
    return out
