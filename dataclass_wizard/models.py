# noinspection PyProtectedMember
from dataclasses import MISSING, Field, _create_fn
from datetime import date, datetime, time
from typing import Union, Collection, Callable, Any, Type
from typing import cast, Optional

from .bases import META
from .constants import PY310_OR_ABOVE
from .type_def import DT, PyTypedDict
from .utils.type_conv import as_datetime, as_time, as_date


# Type for a string or a collection of strings.
_STR_COLLECTION = Union[str, Collection[str]]

# A date, time, datetime sub type, or None.
DT_OR_NONE = Optional[DT]


class Extras(PyTypedDict):
    """
    "Extra" config that can be used in the load / dump process.
    """
    config: META
    # noinspection PyTypedDict
    pattern: '_PatternedDT'


def json_key(*keys: str, all=False, dump=True):
    """
    Represents a mapping of one or more JSON key names for a dataclass field.

    This is only in *addition* to the default key transform; for example, a
    JSON key appearing as "myField", "MyField" or "my-field" will already map
    to a dataclass field "my_field" by default (assuming the key transform
    converts to snake case).

    The mapping to each JSON key name is case-sensitive, so passing "myfield"
    will not match a "myField" key in a JSON string or a Python dict object.

    :param keys: A list of one of more JSON keys to associate with the
      dataclass field.
    :param all: True to also associate the reverse mapping, i.e. from
      dataclass field to JSON key. If multiple JSON keys are passed in, it
      uses the first one provided in this case. This mapping is then used when
      `to_dict` or `to_json` is called, instead of the default key transform.
    :param dump: False to skip this field in the serialization process to
      JSON. By default, this field and its value is included.
    """

    return JSON(*keys, all=all, dump=dump)


def json_field(keys: _STR_COLLECTION, *,
               all=False, dump=True,
               default=MISSING, default_factory=MISSING,
               init=True, repr=True,
               hash=None, compare=True, metadata=None):
    """
    This is a helper function that sets the same defaults for keyword
    arguments as the ``dataclasses.field`` function. It can be thought of as
    an alias to ``dataclasses.field(...)``, but one which also represents
    a mapping of one or more JSON key names to a dataclass field.

    This is only in *addition* to the default key transform; for example, a
    JSON key appearing as "myField", "MyField" or "my-field" will already map
    to a dataclass field "my_field" by default (assuming the key transform
    converts to snake case).

    The mapping to each JSON key name is case-sensitive, so passing "myfield"
    will not match a "myField" key in a JSON string or a Python dict object.

    `keys` is a string, or a collection (list, tuple, etc.) of strings. It
    represents one of more JSON keys to associate with the dataclass field.

    When `all` is passed as True (default is False), it will also associate
    the reverse mapping, i.e. from dataclass field to JSON key. If multiple
    JSON keys are passed in, it uses the first one provided in this case.
    This mapping is then used when ``to_dict`` or ``to_json`` is called,
    instead of the default key transform.

    When `dump` is passed as False (default is True), this field will be
    skipped, or excluded, in the serialization process to JSON.
    """

    if default is not MISSING and default_factory is not MISSING:
        raise ValueError('cannot specify both default and default_factory')

    return JSONField(keys, all, dump, default, default_factory, init, repr,
                     hash, compare, metadata)


class JSON:
    """
    Represents one or more mappings of JSON keys.

    See the docs on the :func:`json_key` function for more info.
    """
    __slots__ = ('keys',
                 'all',
                 'dump')

    def __init__(self, *keys: str, all=False, dump=True):
        self.keys = keys
        self.all = all
        self.dump = dump


class JSONField(Field):
    """
    Alias to a :class:`dataclasses.Field`, but one which also represents a
    mapping of one or more JSON key names to a dataclass field.

    See the docs on the :func:`json_field` function for more info.
    """
    __slots__ = ('json', )

    # In Python 3.10, dataclasses adds a new parameter to the :class:`Field`
    # constructor: `kw_only`
    #
    # Ref: https://docs.python.org/3.10/library/dataclasses.html#dataclasses.dataclass
    if PY310_OR_ABOVE:
        def __init__(self, keys: _STR_COLLECTION, all: bool, dump: bool,
                     default, default_factory, init, repr, hash, compare,
                     metadata):

            super().__init__(default, default_factory, init, repr, hash,
                             compare, metadata, False)

            if isinstance(keys, str):
                keys = (keys,)

            self.json = JSON(*keys, all=all, dump=dump)

    else:
        def __init__(self, keys: _STR_COLLECTION, all: bool, dump: bool,
                     default, default_factory, init, repr, hash, compare,
                     metadata):

            super().__init__(default, default_factory, init, repr, hash,
                             compare, metadata)

            if isinstance(keys, str):
                keys = (keys, )

            self.json = JSON(*keys, all=all, dump=dump)


# noinspection PyPep8Naming
def Pattern(pattern: str):
    return _PatternedDT(pattern)


class _PatternBase:
    __slots__ = ()

    def __class_getitem__(cls, pattern: str):
        return _PatternedDT(pattern, cast(DT, cls.__base__))

    __getitem__ = __class_getitem__


class DatePattern(date, _PatternBase):
    __slots__ = ()


class TimePattern(time, _PatternBase):
    __slots__ = ()


class DateTimePattern(datetime, _PatternBase):
    __slots__ = ()


class _PatternedDT:
    __slots__ = ('cls', 'pattern')

    def __init__(self, pattern: str, cls: DT_OR_NONE = None):
        self.cls = cls
        self.pattern = pattern

    def get_transform_func(self):
        cls = self.cls

        body_lines = ['try:',
                      '  dt = datetime.strptime(date_string, pattern)']

        func_locals = {'datetime': datetime,
                       'pattern': self.pattern,
                       'cls': cls}

        default_load_func: Callable[[Any, Type[DT]], DT]

        if cls is datetime:
            default_load_func = as_datetime
            body_lines.append('  return dt')
        elif cls is date:
            default_load_func = as_date
            body_lines.append('  return dt.date()')
        elif cls is time:
            default_load_func = as_time
            body_lines.append('  return dt.time()')
        elif issubclass(cls, datetime):
            default_load_func = as_datetime
            func_locals['datetime'] = cls
            body_lines.append('  return dt')
        elif issubclass(cls, date):
            default_load_func = as_date
            body_lines.append('  return cls(dt.year, dt.month, dt.day)')
        elif issubclass(cls, time):
            default_load_func = as_time
            body_lines.append('  return cls(dt.hour, dt.minute, dt.second, '
                              'dt.microsecond, fold=dt.fold)')
        else:
            raise TypeError(f'Annotation for `Pattern` is of invalid type '
                            f'({cls}). Expected a type or subtype of: '
                            f'{DT.__constraints__}')

        body_lines.append('except ValueError as e:')
        body_lines.extend(['  try:',
                           '    return default_load_func(date_string, cls)',
                           '  except ValueError:',
                           '     raise e'])

        func_locals['default_load_func'] = default_load_func

        return _create_fn('pattern_to_dt',
                          ('date_string', ),
                          body_lines,
                          locals=func_locals,
                          return_type=DT)

    def __repr__(self):
        repr_val = [f'{k}={getattr(self, k)!r}' for k in self.__slots__]
        return f'{self.__class__.__name__}({", ".join(repr_val)})'
