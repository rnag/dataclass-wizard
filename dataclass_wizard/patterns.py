__all__ = [
    # Abstract Pattern
    'Pattern',
    'AwarePattern',
    'UTCPattern',
    # "Naive" Date/Time Patterns
    'DatePattern',
    'DateTimePattern',
    'TimePattern',
    # Timezone "Aware" Date/Time Patterns
    'AwareDateTimePattern',
    'AwareTimePattern',
    # UTC Date/Time Patterns
    'UTCDateTimePattern',
    'UTCTimePattern',
]

import hashlib
import sys
from datetime import tzinfo, datetime, date, time
from typing import cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ._decorators import setup_recursive_safe_function
from ._models_date import UTC
from ._type_conv import as_datetime, as_date, as_time
from .constants import PY311_OR_ABOVE


def get_zoneinfo(key: str) -> ZoneInfo:
    try:
        return ZoneInfo(key)
    except ZoneInfoNotFoundError:
        if sys.platform.startswith('win'):
            try:
                import tzdata  # noqa: F401
            except Exception:
                raise ZoneInfoNotFoundError(
                    f'No time zone found with key {key!r}. '
                    'On Windows, install tzdata or install Dataclass Wizard with the tz extra:\n'
                    '    pip install dataclass-wizard[tz]'
                ) from None
            else:
                return ZoneInfo(key)
        raise


class PatternBase:
    __dcw_pattern__ = True
    __slots__ = ('base',
                 'patterns',
                 'tz_info',
                 '_repr')

    def __init__(self, base, patterns=None, tz_info=None):
        self.base = base
        if patterns is not None:
            self.patterns = patterns
        if tz_info is not None:
            self.tz_info = tz_info

    def with_tz(self, tz_info: tzinfo):  # pragma: no cover
        self.tz_info = tz_info
        return self

    def __getitem__(self, patterns):
        if (tz_info := getattr(self, 'tz_info', None)) is ...:
            # expect time zone as first argument
            tz_info, *patterns = patterns
            if isinstance(tz_info, str):
                tz_info = get_zoneinfo(tz_info)
        else:
            patterns = (patterns, ) if patterns.__class__ is str else patterns

        return PatternBase(
            self.base,
            patterns,
            tz_info,
        )

    def __call__(self, *patterns):
        return self.__getitem__(patterns)

    @setup_recursive_safe_function(add_cls=False)
    def load_to_pattern(self, tp, extras):
        v = tp.v()

        pb = cast(PatternBase, tp.origin)
        patterns = pb.patterns
        tz_info = getattr(pb, 'tz_info', None)
        __base__ = pb.base

        tn = __base__.__name__

        fn_gen = extras['fn_gen']
        _locals = extras['locals']

        is_datetime \
            = is_date \
            = is_time \
            = is_subclass_date \
            = is_subclass_time \
            = is_subclass_datetime = False

        if tz_info is not None:
            _locals['__tz'] = tz_info
            has_tz = True
            tz_part = '.replace(tzinfo=__tz)'
        else:
            has_tz = False
            tz_part = ''

        if __base__ is datetime:
            is_datetime = True
        elif __base__ is date:
            is_date = True
        elif __base__ is time:
            is_time = True
            _locals['cls'] = time
        elif issubclass(__base__, datetime):
            is_datetime = is_subclass_datetime = True
        elif issubclass(__base__, date):
            is_date = is_subclass_date = True
            _locals['cls'] = __base__
        elif issubclass(__base__, time):
            is_time = is_subclass_time = True
            _locals['cls'] = __base__

        _fromisoformat = f'__{tn}_fromisoformat'
        _fromtimestamp = f'__{tn}_fromtimestamp'

        name_to_func = {
            _fromisoformat: __base__.fromisoformat,
        }
        if is_subclass_datetime:
            _strptime = f'__{tn}_strptime'
            name_to_func[_strptime] = __base__.strptime
        else:
            _strptime = f'__datetime_strptime'
            name_to_func[_strptime] = datetime.strptime

        if is_datetime:
            _as_func = '__as_datetime'
            _as_func_args = f'{v}, {_fromtimestamp}, __tz' if has_tz else f'{v}, {_fromtimestamp}'
            name_to_func[_as_func] = as_datetime
            # `datetime` has a `fromtimestamp` method
            name_to_func[_fromtimestamp] = __base__.fromtimestamp
            end_part = ''
        elif is_date:
            _as_func = '__as_date'
            _as_func_args = f'{v}, {_fromtimestamp}'
            name_to_func[_as_func] = as_date
            # `date` has a `fromtimestamp` method
            name_to_func[_fromtimestamp] = __base__.fromtimestamp
            end_part = '.date()'
        else:
            _as_func = '__as_time'
            _as_func_args = f'{v}, cls'
            name_to_func[_as_func] = as_time
            end_part = '.timetz()' if has_tz else '.time()'

        tp.ensure_in_locals(extras, **name_to_func)

        if PY311_OR_ABOVE:
            _parse_iso_string = f'{_fromisoformat}({v}){tz_part}'
            errors_to_except = (TypeError, )
        else:  # pragma: no cover
            _parse_iso_string = f"{_fromisoformat}({v}.replace('Z', '+00:00', 1)){tz_part}"
            errors_to_except = (AttributeError, TypeError)
        # temp fix for Python 3.11+, since `time.fromisoformat` is updated
        # to support more formats, such as "-" and "+" in strings.
        if (is_time and
                any('-' in s or '+' in s for s in patterns)):

            for p in patterns:
                # Try to parse with `datetime.strptime` first
                with fn_gen.try_():
                    if is_subclass_time:
                        tz_arg = '__tz, ' if has_tz else ''

                        fn_gen.add_line(f'__dt = {_strptime}({v}, {p!r})')
                        fn_gen.add_line('return cls('
                                        '__dt.hour, '
                                        '__dt.minute, '
                                        '__dt.second, '
                                        '__dt.microsecond, '
                                        f'{tz_arg}fold=__dt.fold)')
                    else:
                        fn_gen.add_line(f'return {_strptime}({v}, {p!r}){tz_part}{end_part}')
                with fn_gen.except_(Exception):
                    fn_gen.add_line('pass')
            # If that doesn't work, fallback to `time.fromisoformat`
            with fn_gen.try_():
                fn_gen.add_line(f'return {_parse_iso_string}')
            with fn_gen.except_multi(*errors_to_except):
                fn_gen.add_line(f'return {_as_func}({_as_func_args})')
            with fn_gen.except_(ValueError):
                fn_gen.add_line('pass')
        # Optimized parsing logic (default)
        else:
            # Try to parse with `{base_type}.fromisoformat` first
            with fn_gen.try_():
                fn_gen.add_line(f'return {_parse_iso_string}')
            with fn_gen.except_multi(*errors_to_except):
                fn_gen.add_line(f'return {_as_func}({_as_func_args})')
            with fn_gen.except_(ValueError):
                # If that doesn't work, fallback to `datetime.strptime`
                for p in patterns:
                    with fn_gen.try_():
                        if is_subclass_date:
                            fn_gen.add_line(f'__dt = {_strptime}({v}, {p!r})')
                            fn_gen.add_line('return cls('
                                            '__dt.year, '
                                            '__dt.month, '
                                            '__dt.day)')
                        elif is_subclass_time:
                            fn_gen.add_line(f'__dt = {_strptime}({v}, {p!r})')
                            tz_arg = '__tz, ' if has_tz else ''

                            fn_gen.add_line('return cls('
                                            '__dt.hour, '
                                            '__dt.minute, '
                                            '__dt.second, '
                                            '__dt.microsecond, '
                                            f'{tz_arg}fold=__dt.fold)')
                        else:
                            fn_gen.add_line(f'return {_strptime}({v}, {p!r}){tz_part}{end_part}')
                    with fn_gen.except_(Exception):
                        fn_gen.add_line('pass')
        # Raise a helpful error if we are unable to parse
        # the date string with the provided patterns.
        fn_gen.add_line(
            f'raise ValueError(f"Unable to parse the string \'{{{v}}}\' '
            f'with the provided patterns: {patterns!r}")')

    def __repr__(self):
        # Short path: Temporary state / placeholder
        if self.base is ...:
            return '...'

        if (_repr := getattr(self, '_repr', None)) is not None:
            return _repr

        # Create a stable hash of the patterns
        # noinspection PyTypeChecker
        pat = hashlib.md5(str(self.patterns).encode('utf-8')).hexdigest()

        # Directly use the hash as part of the identifier
        self._repr = _repr = f'{self.base.__name__}_{pat}'

        return _repr


# noinspection PyTypeChecker
Pattern = PatternBase(...)
# noinspection PyTypeChecker
AwarePattern = PatternBase(..., tz_info=...)
# noinspection PyTypeChecker
UTCPattern = PatternBase(..., tz_info=UTC)
# noinspection PyTypeChecker
DatePattern = PatternBase(date)
# noinspection PyTypeChecker
DateTimePattern = PatternBase(datetime)
# noinspection PyTypeChecker
TimePattern = PatternBase(time)
# noinspection PyTypeChecker
AwareDateTimePattern = PatternBase(datetime, tz_info=...)
# noinspection PyTypeChecker
AwareTimePattern = PatternBase(time, tz_info=...)
# noinspection PyTypeChecker
UTCDateTimePattern = PatternBase(datetime, tz_info=UTC)
# noinspection PyTypeChecker
UTCTimePattern = PatternBase(time, tz_info=UTC)
