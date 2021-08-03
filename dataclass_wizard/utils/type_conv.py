__all__ = ['as_bool',
           'as_int',
           'as_str',
           'as_list',
           'as_datetime',
           'as_date',
           'as_time',
           'date_to_timestamp']

from datetime import datetime, time, date
from numbers import Number
from typing import Union, List

from ..type_def import N, NUMBERS


# What values are considered "truthy" when converted to a boolean type.
# noinspection SpellCheckingInspection
_TRUTHY_VALUES = ('TRUE', 'T', 'YES', 'Y', '1')


def as_bool(o: Union[str, bool, N]):
    """
    Return `o` if already a boolean, otherwise return the boolean value
    for `o`.
    """
    if isinstance(o, bool):
        return o

    if not isinstance(o, str):
        o = str(o)

    return o.upper() in _TRUTHY_VALUES


def as_int(o: Union[str, int, bool, None], base_type=int,
           default=0, raise_=True):
    """
    Return `o` if already a int, otherwise return the int value for a
    string. If `o` is None or an empty string, return `default` instead.

    If `o` cannot be converted to an int, raise an error if `raise_` is true,
    other return `default` instead.

    :raises TypeError: If `o` is a `bool` (which is an `int` sub-class)
    :raises ValueError: When `o` cannot be converted to an `int`, and the
      `raise_` parameter is true
    """
    t = type(o)

    if t is base_type:
        return o

    if t is bool:
        raise TypeError(f'as_int: Incorrect type, object={o!r}, type={t}')

    if not o:
        return default

    try:
        return base_type(o)
    except ValueError:
        if raise_:
            raise
        return default


def as_str(o: Union[str, None], base_type=str, raise_=True):
    """
    Return `o` if already a str, otherwise return the string value for `o`.
    If `o` is None or an empty string, return `default` instead.

    If `o` cannot be converted to an str, raise an error if `raise_` is true,
    other return `default` instead.

    """
    if isinstance(o, base_type):
        return o

    if o is None:
        return base_type()

    try:
        return base_type(o)
    except ValueError:
        if raise_:
            raise
        return base_type()


def as_list(o: Union[str, List[str]], sep=','):
    """
    Return `o` if already a list. If `o` is None or an empty string,
    return an empty list. Otherwise, split the string on `sep` and
    return the list result.

    """
    if not o:
        return []

    if isinstance(o, list):
        return o

    return o.split(sep)


def as_datetime(o: Union[str, Number, datetime],
                base_type=datetime, default=None, raise_=True):
    """
    Attempt to convert an object `o` to a :class:`datetime` object using the
    below logic.

        * ``str``: convert datetime strings (in ISO format) via the built-in
          ``fromisoformat`` method.
        * ``Number`` (int or float): Convert a numeric timestamp via the
            built-in ``fromtimestamp`` method.
        * ``datetime``: Return object `o` if it's already of this type or
            sub-type.

    Otherwise, if we're unable to convert the value of `o` to a
    :class:`datetime` as expected, raise an error if the `raise_` parameter
    is true; if not, return `default` instead.

    """
    try:
        # We can assume that `o` is a string, as generally this will be the
        # case. Also, :func:`fromisoformat` does an instance check separately.
        return base_type.fromisoformat(o.replace('Z', '+00:00', 1))

    except (TypeError, AttributeError):

        # Check `type` explicitly, because `bool` is a sub-class of `int`
        if type(o) in NUMBERS:
            # noinspection PyTypeChecker
            return base_type.fromtimestamp(o)

        if isinstance(o, base_type):
            return o

        if raise_:
            raise TypeError(f'Unsupported type, value={o!r}, type={type(o)}')

        return default


def as_date(o: Union[str, Number, date],
            base_type=date, default=None, raise_=True):
    """
    Attempt to convert an object `o` to a :class:`date` object using the
    below logic.

        * ``str``: convert date strings (in ISO format) via the built-in
          ``fromisoformat`` method.
        * ``Number`` (int or float): Convert a numeric timestamp via the
            built-in ``fromtimestamp`` method.
        * ``date``: Return object `o` if it's already of this type or
            sub-type.

    Otherwise, if we're unable to convert the value of `o` to a
    :class:`date` as expected, raise an error if the `raise_` parameter
    is true; if not, return `default` instead.

    """
    try:
        # We can assume that `o` is a string, as generally this will be the
        # case. Also, :func:`fromisoformat` does an instance check separately.
        return base_type.fromisoformat(o)

    except (TypeError, AttributeError):

        # Check `type` explicitly, because `bool` is a sub-class of `int`
        if type(o) in NUMBERS:
            # noinspection PyTypeChecker
            return base_type.fromtimestamp(o)

        if isinstance(o, base_type):
            return o

        if raise_:
            raise TypeError(f'Unsupported type, value={o!r}, type={type(o)}')

        return default


def as_time(o: Union[str, time], base_type=time, default=None, raise_=True):
    """
    Attempt to convert an object `o` to a :class:`time` object using the
    below logic.

        * ``str``: convert time strings (in ISO format) via the built-in
          ``fromisoformat`` method.
        * ``time``: Return object `o` if it's already of this type or
            sub-type.

    Otherwise, if we're unable to convert the value of `o` to a
    :class:`time` as expected, raise an error if the `raise_` parameter
    is true; if not, return `default` instead.

    """
    try:
        # We can assume that `o` is a string, as generally this will be the
        # case. Also, :func:`fromisoformat` does an instance check separately.
        return base_type.fromisoformat(o.replace('Z', '+00:00', 1))

    except (TypeError, AttributeError):

        if isinstance(o, base_type):
            return o

        if raise_:
            raise TypeError(f'Unsupported type, value={o!r}, type={type(o)}')

        return default


def date_to_timestamp(d: date) -> int:
    """
    Retrieves the epoch timestamp of a :class:`date` object, as an `int`

    https://stackoverflow.com/a/15661036/10237506
    """
    dt = datetime.combine(d, time.min)
    return round(dt.timestamp())
