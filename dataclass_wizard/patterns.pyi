from datetime import datetime, date, time, tzinfo
from types import EllipsisType
from typing import (Generic)
from typing import Self

from ._type_def import DT, T
from .models import TypeInfo, Extras


class PatternBase(Generic[DT]):

    # base type for pattern, a type (or subtype) of `DT`
    base: type[DT]

    # a sequence of custom (non-ISO format) date string patterns
    patterns: tuple[str, ...]

    tz_info: tzinfo | EllipsisType

    def __init__(self, base: type[DT],
                 patterns: tuple[str, ...] | None = None,
                 tz_info: tzinfo | EllipsisType | None = None): ...

    def with_tz(self, tz_info: tzinfo | EllipsisType) -> Self: ...

    def __getitem__(self, patterns: tuple[str, ...]) -> type[DT]: ...

    def __call__(self, *patterns: str) -> type[DT]: ...

    def load_to_pattern(self, tp: TypeInfo, extras: Extras): ...


class Pattern(PatternBase):
    """
    Base class for custom patterns used in date, time, or datetime parsing.

    Parameters
    ----------
    pattern : str
        The string pattern used for parsing, e.g., '%m-%d-%y'.

    Examples
    --------
    Using Pattern with `Annotated` inside a dataclass:

    >>> from typing import Annotated
    >>> from datetime import date
    >>> from dataclasses import dataclass
    >>> from dataclass_wizard.patterns import Pattern
    >>> @dataclass
    ... class MyClass:
    ...     my_date_field: Annotated[date, Pattern('%m-%d-%y')]
    """
    # noinspection PyInitNewSignature
    def __init__(self, pattern): ...
    __class_getitem__ = __getitem__ = __init__


class AwarePattern(PatternBase):
    """
    Pattern class for timezone-aware parsing of time and datetime objects.

    Parameters
    ----------
    timezone : str
        The timezone to use, e.g., 'US/Eastern'.
    pattern : str
        The string pattern used for parsing, e.g., '%H:%M:%S'.

    Examples
    --------
    Using AwarePattern with `Annotated` inside a dataclass:

    >>> from typing import Annotated
    >>> from datetime import time
    >>> from dataclasses import dataclass
    >>> from dataclass_wizard.patterns import AwarePattern
    >>> @dataclass
    ... class MyClass:
    ...     my_time_field: Annotated[list[time], AwarePattern('US/Eastern', '%H:%M:%S')]
    """
    # noinspection PyInitNewSignature
    def __init__(self, timezone, pattern): ...


class UTCPattern(PatternBase):
    """
    Pattern class for UTC parsing of time and datetime objects.

    Parameters
    ----------
    pattern : str
        The string pattern used for parsing, e.g., '%Y-%m-%d %H:%M:%S'.

    Examples
    --------
    Using UTCPattern with `Annotated` inside a dataclass:

    >>> from typing import Annotated
    >>> from datetime import datetime
    >>> from dataclasses import dataclass
    >>> from dataclass_wizard.patterns import UTCPattern
    >>> @dataclass
    ... class MyClass:
    ...     my_utc_field: Annotated[datetime, UTCPattern('%Y-%m-%d %H:%M:%S')]
    """
    # noinspection PyInitNewSignature
    def __init__(self, pattern): ...
    __class_getitem__ = __getitem__ = __init__


class AwareTimePattern(time, Generic[T]):
    """
    Pattern class for timezone-aware parsing of time objects.

    Parameters
    ----------
    timezone : str
        The timezone to use, e.g., 'Europe/London'.
    pattern : str
        The string pattern used for parsing, e.g., '%H:%M:%Z'.

    Examples
    --------
    Using ``AwareTimePattern`` inside a dataclass:

    >>> from dataclasses import dataclass
    >>> from dataclass_wizard.patterns import AwareTimePattern
    >>> @dataclass
    ... class MyClass:
    ...     my_aware_dt_field: AwareTimePattern['Europe/London', '%H:%M:%Z']
    """
    # noinspection PyInitNewSignature
    def __init__(self, timezone, pattern): ...
    __getitem__ = __init__


class AwareDateTimePattern(datetime, Generic[T]):
    """
    Pattern class for timezone-aware parsing of datetime objects.

    Parameters
    ----------
    timezone : str
        The timezone to use, e.g., 'Asia/Tokyo'.
    pattern : str
        The string pattern used for parsing, e.g., '%m-%Y-%H:%M-%Z'.

    Examples
    --------
    Using ``AwareDateTimePattern`` inside a dataclass:

    >>> from dataclasses import dataclass
    >>> from dataclass_wizard.patterns import AwareDateTimePattern
    >>> @dataclass
    ... class MyClass:
    ...     my_aware_dt_field: AwareDateTimePattern['Asia/Tokyo', '%m-%Y-%H:%M-%Z']
    """
    # noinspection PyInitNewSignature
    def __init__(self, timezone, pattern): ...
    __getitem__ = __init__


class DatePattern(date, Generic[T]):
    """
    An annotated type representing a date pattern (i.e. format string). Upon
    de-serialization, the resolved type will be a ``date`` instead.

    Parameters
    ----------
    pattern : str
        The string pattern used for parsing, e.g., '%Y/%m/%d'.

    Examples
    --------
    Using ``DatePattern`` inside a dataclass:

    >>> from dataclasses import dataclass
    >>> from dataclass_wizard.patterns import DatePattern
    >>> @dataclass
    ... class MyClass:
    ...     my_date_field: DatePattern['%Y/%m/%d']
    """
    # noinspection PyInitNewSignature
    def __init__(self, pattern): ...
    __getitem__ = __init__


class TimePattern(time, Generic[T]):
    """
    An annotated type representing a time pattern (i.e. format string). Upon
    de-serialization, the resolved type will be a ``time`` instead.

    Parameters
    ----------
    pattern : str
        The string pattern used for parsing, e.g., '%H:%M:%S'.

    Examples
    --------
    Using ``TimePattern`` inside a dataclass:

    >>> from dataclasses import dataclass
    >>> from dataclass_wizard.patterns import TimePattern
    >>> @dataclass
    ... class MyClass:
    ...     my_time_field: TimePattern['%H:%M:%S']
    """
    # noinspection PyInitNewSignature
    def __init__(self, pattern): ...
    __getitem__ = __init__


class DateTimePattern(datetime, Generic[T]):
    """
    An annotated type representing a datetime pattern (i.e. format string). Upon
    de-serialization, the resolved type will be a ``datetime`` instead.

    Parameters
    ----------
    pattern : str
        The string pattern used for parsing, e.g., '%d, %b, %Y %I:%M:%S %p'.

    Examples
    --------
    Using DateTimePattern with `Annotated` inside a dataclass:

    >>> from dataclasses import dataclass
    >>> from dataclass_wizard.patterns import DateTimePattern
    >>> @dataclass
    ... class MyClass:
    ...     my_time_field: DateTimePattern['%d, %b, %Y %I:%M:%S %p']
    """
    # noinspection PyInitNewSignature
    def __init__(self, pattern): ...
    __getitem__ = __init__


class UTCTimePattern(time, Generic[T]):
    """
    Pattern class for UTC parsing of time objects.

    Parameters
    ----------
    pattern : str
        The string pattern used for parsing, e.g., '%H:%M:%S'.

    Examples
    --------
    Using ``UTCTimePattern`` inside a dataclass:

    >>> from dataclasses import dataclass
    >>> from dataclass_wizard.patterns import UTCTimePattern
    >>> @dataclass
    ... class MyClass:
    ...     my_utc_time_field: UTCTimePattern['%H:%M:%S']
    """
    # noinspection PyInitNewSignature
    def __init__(self, pattern): ...
    __getitem__ = __init__


class UTCDateTimePattern(datetime, Generic[T]):
    """
    Pattern class for UTC parsing of datetime objects.

    Parameters
    ----------
    pattern : str
        The string pattern used for parsing, e.g., '%Y-%m-%d %H:%M:%S'.

    Examples
    --------
    Using ``UTCDateTimePattern`` inside a dataclass:

    >>> from dataclasses import dataclass
    >>> from dataclass_wizard.patterns import UTCDateTimePattern
    >>> @dataclass
    ... class MyClass:
    ...     my_utc_datetime_field: UTCDateTimePattern['%Y-%m-%d %H:%M:%S']
    """
    # noinspection PyInitNewSignature
    def __init__(self, pattern): ...
    __getitem__ = __init__
