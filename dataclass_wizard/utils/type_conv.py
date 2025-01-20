__all__ = ['as_bool',
           'as_int',
           'as_int_v1',
           'as_str',
           'as_list',
           'as_dict',
           'as_enum',
           'as_datetime_v1',
           'as_date_v1',
           'as_time_v1',
           'as_datetime',
           'as_date',
           'as_time',
           'as_timedelta',
           'date_to_timestamp',
           'TRUTHY_VALUES',
           ]

import json
from collections.abc import Callable
from datetime import datetime, time, date, timedelta, timezone, tzinfo
from numbers import Number
from typing import Union, Type, AnyStr, Optional, Iterable, Any

from ..errors import ParseError
from ..lazy_imports import pytimeparse
from ..type_def import E, N, NUMBERS

# What values are considered "truthy" when converting to a boolean type.
# noinspection SpellCheckingInspection
TRUTHY_VALUES = frozenset({'true', 't', 'yes', 'y', 'on', '1'})


# TODO Remove: Unused in V1
def as_bool(o: Union[str, bool, N]):
    """
    Return `o` if already a boolean, otherwise return the boolean value
    for `o`.
    """
    if (t := type(o)) is bool:
        return o

    if t is str:
        return o.lower() in TRUTHY_VALUES

    return o == 1


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


def as_int(o: Union[str, int, float, bool, None], base_type=int,
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

    if t is str:
        # Check if the string represents a float value, e.g. '2.7'

        # TODO uncomment once we update to v1
        # if '.' in o:
        #     if (float_value := float(o)).is_integer():
        #         return base_type(float_value)
        #     raise ValueError(f"Cannot cast string float with fractional part: {value}")

        if o:
            if '.' in o:
                return base_type(round(float(o)))
            # Assume direct integer string
            return base_type(o)
        return default

    if t is float:
        # TODO uncomment once we update to v1
        # if o.is_integer():
        #     return base_type(o)
        # raise ValueError(f"Cannot cast float with fractional part: {o}")
        return base_type(round(o))

    if t is bool:
        raise TypeError(f'as_int: Incorrect type, object={o!r}, type={t}')

    try:
        return base_type(o)

    except (TypeError, ValueError):

        if not o:
            return default

        if raise_:
            raise

        return default


# TODO Remove: Unused in V1
def as_str(o: Union[str, None], base_type=str):
    """
    Return `o` if already a str, otherwise return the string value for `o`.
    If `o` is None, return an empty string instead.
    """
    return '' if o is None else base_type(o)


def as_list(o: Union[str, Iterable], sep=','):
    """
    Return `o` if already a list. If `o` is a string, split it on `sep` and
    return the list result.

    """
    if isinstance(o, str):
        if o.lstrip().startswith('['):
            return json.loads(o)
        else:
            return [e.strip() for e in o.split(sep)]

    return o


def as_dict(o: Union[str, Iterable], kv_sep='=', sep=','):
    """
    Return `o` if already a dict. If `o` is a string, split it on `sep` and
    then split each result by `kv_sep`, and return the dict result.

    """
    if isinstance(o, str):
        if o.lstrip().startswith('{'):
            return json.loads(o)
        else:
            # noinspection PyTypeChecker
            return dict(map(str.strip, pair.split(kv_sep, 1))
                        for pair in o.split(sep))

    return o


def as_enum(o: Union[AnyStr, N],
            base_type: Type[E],
            lookup_func=lambda base_type, o: base_type[o],
            transform_func=lambda o: o.upper().replace(' ', '_'),
            raise_=True
            ) -> Optional[E]:
    """
    Return `o` if it's already an :class:`Enum` of type `base_type`. If `o` is
    None or an empty string, return None.

    Otherwise, attempt to convert the object `o` to a :type:`base_type` using
    the below logic:

        * If `o` is a string, we'll put it through our `transform_func` before
          a lookup. The default one upper-cases the string and replaces spaces
          with underscores, since that's typically how we define `Enum` names.

        * Then, convert to a :type:`base_type` using the `lookup_func`. The
          one looks up by the Enum ``name`` field.

    :raises ParseError: If the lookup for the Enum member fails, and the
      `raise_` flag is enabled.

    """
    if isinstance(o, base_type):
        return o

    if o is None:
        return o

    if o == '':
        return None

    key = transform_func(o) if isinstance(o, str) else o

    try:
        return lookup_func(base_type, key)

    except KeyError:

        if raise_:
            from inspect import getsource

            enum_cls_name = getattr(base_type, '__qualname__', base_type)
            valid_values = getattr(base_type, '_member_names_', None)
            # TODO this is to get the source code for the lambda function.
            #   Might need to refactor into a helper func when time allows.
            lookup_func_src = getsource(lookup_func).strip('\n, ').split(
                'lookup_func=', 1)[-1]

            e = ValueError(
                f'as_enum: Unable to convert value to type {enum_cls_name!r}')

            raise ParseError(e, o, base_type,
                             valid_values=valid_values,
                             lookup_key=key,
                             lookup_func=lookup_func_src)

        else:
            return None


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
               __from_timestamp: Callable[[float], date]):
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
        return __from_timestamp(o)

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


# TODO Remove: Unused in V1
def as_datetime(o: Union[str, Number, datetime],
                base_type=datetime, default=None, raise_=True):
    """
    Attempt to convert an object `o` to a :class:`datetime` object using the
    below logic.

        * ``str``: convert datetime strings (in ISO format) via the built-in
          ``fromisoformat`` method.
        * ``Number`` (int or float): Convert a numeric timestamp via the
            built-in ``fromtimestamp`` method, and return a UTC datetime.
        * ``datetime``: Return object `o` if it's already of this type or
            sub-type.

    Otherwise, if we're unable to convert the value of `o` to a
    :class:`datetime` as expected, raise an error if the `raise_` parameter
    is true; if not, return `default` instead.

    """
    # noinspection PyBroadException
    try:
        # We can assume that `o` is a string, as generally this will be the
        # case. Also, :func:`fromisoformat` does an instance check separately.
        return base_type.fromisoformat(o.replace('Z', '+00:00', 1))

    except Exception:

        t = type(o)

        if t is str:
            # Minor performance fix: if it's a string, we don't need to run
            # the other type checks.
            if raise_:
                raise

        # Check `type` explicitly, because `bool` is a sub-class of `int`
        elif t in NUMBERS:
            # noinspection PyTypeChecker
            return base_type.fromtimestamp(o, tz=timezone.utc)

        elif t is base_type:
            return o

        if raise_:
            raise TypeError(f'Unsupported type, value={o!r}, type={t}')

        return default


# TODO Remove: Unused in V1
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
    # noinspection PyBroadException
    try:
        # We can assume that `o` is a string, as generally this will be the
        # case. Also, :func:`fromisoformat` does an instance check separately.
        return base_type.fromisoformat(o)

    except Exception:

        t = type(o)

        if t is str:
            # Minor performance fix: if it's a string, we don't need to run
            # the other type checks.
            if raise_:
                raise

        # Check `type` explicitly, because `bool` is a sub-class of `int`
        elif t in NUMBERS:
            # noinspection PyTypeChecker
            return base_type.fromtimestamp(o)

        elif t is base_type:
            return o

        if raise_:
            raise TypeError(f'Unsupported type, value={o!r}, type={t}')

        return default


# TODO Remove: Unused in V1
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
    # noinspection PyBroadException
    try:
        # We can assume that `o` is a string, as generally this will be the
        # case. Also, :func:`fromisoformat` does an instance check separately.
        return base_type.fromisoformat(o.replace('Z', '+00:00', 1))

    except Exception:

        t = type(o)

        if t is str:
            # Minor performance fix: if it's a string, we don't need to run
            # the other type checks.
            if raise_:
                raise

        elif t is base_type:
            return o

        if raise_:
            raise TypeError(f'Unsupported type, value={o!r}, type={t}')

        return default


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


def date_to_timestamp(d: date) -> int:
    """
    Retrieves the epoch timestamp of a :class:`date` object, as an `int`

    https://stackoverflow.com/a/15661036/10237506
    """
    dt = datetime.combine(d, time.min)
    return round(dt.timestamp())
