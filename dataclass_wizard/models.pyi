import json
from dataclasses import MISSING, Field
from datetime import date, datetime, time
from typing import (Collection, Callable,
                    Generic, Mapping, TypeAlias)
from typing import TypedDict, overload, Any, NotRequired

from .bases import META
from .decorators import cached_property
from .type_def import T, DT, Encoder, FileEncoder
from .utils.function_builder import FunctionBuilder
from .utils.object_path import PathPart, PathType


# Define a simple type (alias) for the `CatchAll` field
CatchAll: TypeAlias = Mapping | None

# Type for a string or a collection of strings.
_STR_COLLECTION: TypeAlias = str | Collection[str]


class Extras(TypedDict):
    """
    "Extra" config that can be used in the load / dump process.
    """
    config: NotRequired[META]
    cls: type
    cls_name: str
    fn_gen: FunctionBuilder
    locals: dict[str, Any]
    pattern: NotRequired[PatternedDT]


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
    ...


# noinspection PyPep8Naming
def KeyPath(keys: PathType | str, all: bool = True, dump: bool = True):
    """
    Represents a mapping of one or more "nested" key names in JSON
    for a dataclass field.

    This is only in *addition* to the default key transform; for example, a
    JSON key appearing as "myField", "MyField" or "my-field" will already map
    to a dataclass field "my_field" by default (assuming the key transform
    converts to snake case).

    The mapping to each JSON key name is case-sensitive, so passing "myfield"
    will not match a "myField" key in a JSON string or a Python dict object.

    :param keys: A list of one of more "nested" JSON keys to associate
      with the dataclass field.
    :param all: True to also associate the reverse mapping, i.e. from
      dataclass field to "nested" JSON key. If multiple JSON keys are passed in, it
      uses the first one provided in this case. This mapping is then used when
      `to_dict` or `to_json` is called, instead of the default key transform.
    :param dump: False to skip this field in the serialization process to
      JSON. By default, this field and its value is included.

    Example:

    >>> from typing import Annotated
    >>> my_str: Annotated[str, KeyPath('my."7".nested.path.-321')]
    >>> # where path.keys == ('my', '7', 'nested', 'path', -321)
    """
    ...


def env_field(keys: _STR_COLLECTION, *,
              all=False, dump=True,
              default=MISSING,
              default_factory: Callable[[], MISSING] = MISSING,
              init=True, repr=True,
              hash=None, compare=True, metadata=None):
    """
    This is a helper function that sets the same defaults for keyword
    arguments as the ``dataclasses.field`` function. It can be thought of as
    an alias to ``dataclasses.field(...)``, but one which also represents
    a mapping of one or more environment variable (env var) names to
    a dataclass field.

    This is only in *addition* to the default key transform; for example, an
    env var appearing as "myField", "MyField" or "my-field" will already map
    to a dataclass field "my_field" by default (assuming the key transform
    converts to snake case).

    `keys` is a string, or a collection (list, tuple, etc.) of strings. It
    represents one of more env vars to associate with the dataclass field.

    When `all` is passed as True (default is False), it will also associate
    the reverse mapping, i.e. from dataclass field to env var. If multiple
    env vars are passed in, it uses the first one provided in this case.
    This mapping is then used when ``to_dict`` or ``to_json`` is called,
    instead of the default key transform.

    When `dump` is passed as False (default is True), this field will be
    skipped, or excluded, in the serialization process to JSON.
    """
    ...


def json_field(keys: _STR_COLLECTION, *,
               all=False, dump=True,
               default=MISSING,
               default_factory: Callable[[], MISSING] = MISSING,
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
    ...


def path_field(keys: _STR_COLLECTION, *,
               all=True, dump=True,
               default=MISSING,
               default_factory: Callable[[], MISSING] = MISSING,
               init=True, repr=True,
               hash=None, compare=True, metadata=None):
    """
    Creates a dataclass field mapped to one or more nested JSON paths.

    This function is an alias for ``dataclasses.field(...)``, with additional
    logic for associating a field with one or more JSON key paths, including
    nested structures. It can be used to specify custom mappings between
    dataclass fields and complex, nested JSON key names.

    This mapping is **case-sensitive** and applies to the provided JSON keys
    or nested paths. For example, passing "myField" will not match "myfield"
    in JSON, and vice versa.

    `keys` represents one or more nested JSON keys (as strings or a collection of strings)
    to associate with the dataclass field. The keys can include paths like `a.b.c`
    or even more complex nested paths such as `a["nested"]["key"]`.

    Arguments:
        keys (_STR_COLLECTION): The JSON key(s) or nested path(s) to associate with the dataclass field.
        all (bool): If True (default), it also associates the reverse mapping
                    (from dataclass field to JSON path) for serialization.
                    This reverse mapping is used during `to_dict` or `to_json` instead
                    of the default key transform.
        dump (bool): If False (default is True), excludes this field from
                     serialization to JSON.
        default (Any): The default value for the field. Mutually exclusive with `default_factory`.
        default_factory (Callable[[], Any]): A callable to generate the default value.
                                             Mutually exclusive with `default`.
        init (bool): Include the field in the generated `__init__` method. Defaults to True.
        repr (bool): Include the field in the `__repr__` output. Defaults to True.
        hash (bool): Include the field in the `__hash__` method. Defaults to None.
        compare (bool): Include the field in comparison methods. Defaults to True.
        metadata (dict): Metadata to associate with the field. Defaults to None.

    Returns:
        JSONField: A dataclass field with logic for mapping to one or more nested JSON paths.

    Example:
        >>> from dataclasses import dataclass
        >>> @dataclass
        >>> class Example:
        >>>     my_str: str = path_field(['a.b.c.1', 'x.y["-1"].z'], default=42)
        >>> # Maps nested paths ('a', 'b', 'c', 1) and ('x', 'y', '-1', 'z')
        >>> # to the `my_str` attribute.
    """
    ...


def skip_if_field(condition: Condition, *,
                  default=MISSING,
                  default_factory: Callable[[], MISSING] = MISSING,
                  init=True, repr=True,
                  hash=None, compare=True, metadata=None,
                  kw_only: bool = MISSING):
    """
    Defines a dataclass field with a ``SkipIf`` condition.

    This function is a shortcut for ``dataclasses.field(...)``,
    adding metadata to specify a condition. If the condition
    evaluates to ``True``, the field is skipped during
    JSON serialization.

    Arguments:
        condition (Condition): The condition, if true skips serializing the field.
        default (Any): The default value for the field. Mutually exclusive with `default_factory`.
        default_factory (Callable[[], Any]): A callable to generate the default value.
                                             Mutually exclusive with `default`.
        init (bool): Include the field in the generated `__init__` method. Defaults to True.
        repr (bool): Include the field in the `__repr__` output. Defaults to True.
        hash (bool): Include the field in the `__hash__` method. Defaults to None.
        compare (bool): Include the field in comparison methods. Defaults to True.
        metadata (dict): Metadata to associate with the field. Defaults to None.
        kw_only (bool): If true, the field will become a keyword-only parameter to __init__().
    Returns:
        Field: A dataclass field with correct metadata set.

    Example:
        >>> from dataclasses import dataclass
        >>> @dataclass
        >>> class Example:
        >>>     my_str: str = skip_if_field(IS_NOT(True))
        >>> # Creates a condition which skips serializing `my_str`
        >>> # if its value `is not True`.
    """


class JSON:
    """
    Represents one or more mappings of JSON keys.

    See the docs on the :func:`json_key` function for more info.
    """
    __slots__ = ('keys',
                 'all',
                 'dump',
                 'path')

    keys: tuple[str, ...] | PathType
    all: bool
    dump: bool
    path: bool

    def __init__(self, *keys: str | PathPart, all=False, dump=True, path=False):
        ...


class JSONField(Field):
    """
    Alias to a :class:`dataclasses.Field`, but one which also represents a
    mapping of one or more JSON key names to a dataclass field.

    See the docs on the :func:`json_field` function for more info.
    """
    __slots__ = ('json', )

    json: JSON

    # In Python 3.10, dataclasses adds a new parameter to the :class:`Field`
    # constructor: `kw_only`
    #
    # Ref: https://docs.python.org/3.10/library/dataclasses.html#dataclasses.dataclass
    @overload
    def __init__(self, keys: _STR_COLLECTION, all: bool, dump: bool,
                 default, default_factory, init, repr, hash, compare,
                 metadata, path: bool = False):
        ...

    @overload
    def __init__(self, keys: _STR_COLLECTION, all: bool, dump: bool,
                 default, default_factory, init, repr, hash, compare,
                 metadata, path: bool = False):
        ...


# noinspection PyPep8Naming
def Pattern(pattern: str):
    """
    Represents a pattern (i.e. format string) for a date / time / datetime
    type or subtype. For example, a custom pattern like below::

        %d, %b, %Y %H:%M:%S.%f

    A sample usage of ``Pattern``, using a subclass of :class:`time`::

        time_field: Annotated[List[MyTime], Pattern('%I:%M %p')]

    :param pattern: A format string to be passed in to `datetime.strptime`
    """
    ...


class _PatternBase:
    """Base "subscriptable" pattern for date/time/datetime."""
    __slots__ = ()

    def __class_getitem__(cls, pattern: str) -> PatternedDT[date | time | datetime]:
        ...

    __getitem__ = _PatternBase.__class_getitem__


class DatePattern(date, _PatternBase):
    """
    An annotated type representing a date pattern (i.e. format string). Upon
    de-serialization, the resolved type will be a :class:`date` instead.

    See the docs on :func:`Pattern` for more info.
    """
    __slots__ = ()


class TimePattern(time, _PatternBase):
    """
    An annotated type representing a time pattern (i.e. format string). Upon
    de-serialization, the resolved type will be a :class:`time` instead.

    See the docs on :func:`Pattern` for more info.
    """
    __slots__ = ()


class DateTimePattern(datetime, _PatternBase):
    """
    An annotated type representing a datetime pattern (i.e. format string). Upon
    de-serialization, the resolved type will be a :class:`datetime` instead.

    See the docs on :func:`Pattern` for more info.
    """
    __slots__ = ()


class PatternedDT(Generic[DT]):
    """
    Base class for pattern matching using :meth:`datetime.strptime` when
    loading (de-serializing) a string to a date / time / datetime object.
    """

    # `cls` is the date/time/datetime type or subclass.
    # `pattern` is the format string to pass in to `datetime.strptime`.
    __slots__ = ('cls',
                 'pattern')

    cls: type[DT] | None
    pattern: str

    def __init__(self, pattern: str, cls: type[DT] | None = None):
        ...

    def get_transform_func(self) -> Callable[[str], DT]:
        """
        Build and return a load function which takes a `date_string` as an
        argument, and returns a new object of type :attr:`cls`.

        We try to parse the input string to a `cls` object in the following
        order:
            - In case it's an ISO-8601 format string, or a numeric timestamp,
              we first parse with the default load function (ex. as_datetime).
              We parse strings using the builtin :meth:`fromisoformat` method,
              as this is much faster than :meth:`datetime.strptime` - see link
              below for more details.
            - Next, we parse with :meth:`datetime.strptime` by passing in the
              :attr:`pattern` to match against. If the pattern is invalid, the
              method raises a ValueError, which is re-raised by our
              `Parser` implementation.

        Ref: https://stackoverflow.com/questions/13468126/a-faster-strptime

        :raises ValueError: If the input date string does not match the
          pre-defined pattern.
        """
        ...

    def __repr__(self):
        ...


class Container(list[T]):
    """Convenience wrapper around a collection of dataclass instances.

    For all intents and purposes, this should behave exactly as a `list`
    object.

    Usage:

        >>> from dataclass_wizard import Container, fromlist
        >>> from dataclasses import make_dataclass
        >>>
        >>> A = make_dataclass('A', [('f1', str), ('f2', int)])
        >>> list_of_a = fromlist(A, [{'f1': 'hello', 'f2': 1}, {'f1': 'world', 'f2': 2}])
        >>> c = Container[A](list_of_a)
        >>> print(c.prettify())

    """

    __slots__ = ('__dict__',
                 '__orig_class__')

    @cached_property
    def __model__(self) -> type[T]:
        """
        Given a declaration like Container[T], this returns the subscripted
        value of the generic type T.
        """
        ...

    def __str__(self):
        """
        Control the value displayed when ``print(self)`` is called.
        """
        ...

    def prettify(self, encoder: Encoder = json.dumps,
                 ensure_ascii=False,
                 **encoder_kwargs) -> str:
        """
        Convert the list of instances to a *prettified* JSON string.
        """
        ...

    def to_json(self, encoder: Encoder = json.dumps,
                **encoder_kwargs) -> str:
        """
        Convert the list of instances to a JSON string.
        """
        ...

    def to_json_file(self, file: str, mode: str = 'w',
                     encoder: FileEncoder = json.dump,
                     **encoder_kwargs) -> None:
        """
        Serializes the list of instances and writes it to a JSON file.
        """
        ...


class Condition:

    op: str         # Operator
    val: Any        # Value
    t_or_f: bool    # Truthy or falsy
    _wrapped: bool  # True if wrapped in `SkipIf()`

    def __init__(self, operator: str, value: Any):
        ...

    def __str__(self):
        ...

    def evaluate(self, other) -> bool:
        ...


# Aliases for conditions
# noinspection PyPep8Naming
def EQ(value: Any) -> Condition:
    """Create a condition for equality (==)."""


# noinspection PyPep8Naming
def NE(value: Any) -> Condition:
    """Create a condition for inequality (!=)."""


# noinspection PyPep8Naming
def LT(value: Any) -> Condition:
    """Create a condition for less than (<)."""


# noinspection PyPep8Naming
def LE(value: Any) -> Condition:
    """Create a condition for less than or equal to (<=)."""


# noinspection PyPep8Naming
def GT(value: Any) -> Condition:
    """Create a condition for greater than (>)."""


# noinspection PyPep8Naming
def GE(value: Any) -> Condition:
    """Create a condition for greater than or equal to (>=)."""


# noinspection PyPep8Naming
def IS(value: Any) -> Condition:
    """Create a condition for identity (is)."""


# noinspection PyPep8Naming
def IS_NOT(value: Any) -> Condition:
    """Create a condition for non-identity (is not)."""


# noinspection PyPep8Naming
def IS_TRUTHY() -> Condition:
    """Create a "truthy" condition for evaluation (if <var>)."""


# noinspection PyPep8Naming
def IS_FALSY() -> Condition:
    """Create a "falsy" condition for evaluation (if not <var>)."""


# noinspection PyPep8Naming
def SkipIf(condition: Condition) -> Condition:
    ...


SkipIfNone: Condition


def finalize_skip_if(skip_if: Condition,
                     operand_1: str,
                     conditional: str) -> str:
    ...


def get_skip_if_condition(skip_if: Condition,
                          _locals: dict[str, Any],
                          operand_2: str = None,
                          condition_i: int = None,
                          condition_var: str = '_skip_if_') -> 'str | bool':
    ...
