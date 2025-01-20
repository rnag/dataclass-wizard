from dataclasses import MISSING, Field as _Field, dataclass
from datetime import datetime, date, time, tzinfo
from typing import (Collection, Callable,
                    Mapping, Generic, Sequence)
from typing import TypedDict, overload, Any, NotRequired, Self

from ..bases import META
from ..models import Condition
from ..type_def import DefFactory, DT, T
from ..utils.function_builder import FunctionBuilder
from ..utils.object_path import PathType


# Define a simple type (alias) for the `CatchAll` field
CatchAll = Mapping | None

# Type for a string or a collection of strings.
type _STR_COLLECTION = str | Collection[str]


@dataclass(order=True)
class TypeInfo:
    __slots__ = ...
    # type origin (ex. `List[str]` -> `List`)
    origin: type
    # type arguments (ex. `Dict[str, int]` -> `(str, int)`)
    args: tuple[type, ...] | None = None
    # name of type origin (ex. `List[str]` -> 'list')
    name: str | None = None
    # index of iteration, *only* unique within the scope of a field assignment!
    i: int = 1
    # index of field within the dataclass, *guaranteed* to be unique.
    field_i: int = 1
    # prefix of value in assignment (prepended to `i`),
    # defaults to 'v' if not specified.
    prefix: str = 'v'
    # index of assignment (ex. `2 -> v1[2]`, *or* a string `"key" -> v4["key"]`)
    index: int | None = None
    # indicates if we are currently in Optional,
    # e.g. `typing.Optional[...]` *or* `typing.Union[T, ...*T2, None]`
    in_optional: bool = False

    def replace(self, **changes) -> TypeInfo: ...
    @staticmethod
    def ensure_in_locals(extras: Extras, *tps: Callable, **name_to_tp: Callable[..., Any]) -> None: ...
    def type_name(self, extras: Extras,
                  *, bound: type | None = None) -> str: ...
    def v(self) -> str: ...
    def v_and_next(self) -> tuple[str, str, int]: ...
    def v_and_next_k_v(self) -> tuple[str, str, str, int]: ...
    def multi_wrap(self, extras, prefix='', *result, force=False) -> list[str]: ...
    def wrap(self, result: str,
             extras: Extras,
             force=False,
             prefix='',
             *, bound: type | None = None) -> Self: ...
    def wrap_builtin(self, bound: type, result: str, extras: Extras) -> Self: ...
    def wrap_dd(self, default_factory: DefFactory, result: str, extras: Extras) -> Self: ...
    def _wrap_inner(self, extras: Extras,
                    tp: type | DefFactory | None = None,
                    prefix: str = '',
                    is_builtin: bool = False,
                    force=False,
                    bound: type | None = None) -> str | None: ...

class Extras(TypedDict):
    """
    "Extra" config that can be used in the load / dump process.
    """
    config: META
    cls: type
    cls_name: str
    fn_gen: FunctionBuilder
    locals: dict[str, Any]
    pattern: NotRequired[PatternBase]
    recursion_guard: dict[type, str]


class PatternBase:

    # base type for pattern, a type (or subtype) of `DT`
    base: type[DT]

    # a sequence of custom (non-ISO format) date string patterns
    patterns: tuple[str, ...]

    tz_info: tzinfo | Ellipsis

    def __init__(self, base: type[DT],
                 patterns: tuple[str, ...] = None,
                 tz_info: tzinfo | Ellipsis | None = None): ...

    def with_tz(self, tz_info: tzinfo | Ellipsis) -> Self: ...

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
    >>> from dataclass_wizard import LoadMeta
    >>> from dataclass_wizard.v1 import Pattern
    >>> @dataclass
    ... class MyClass:
    ...     my_date_field: Annotated[date, Pattern('%m-%d-%y')]
    >>> LoadMeta(v1=True).bind_to(MyClass)
    """
    __class_getitem__ = __getitem__ = __init__
    # noinspection PyInitNewSignature
    def __init__(self, pattern): ...


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
    >>> from dataclass_wizard import LoadMeta
    >>> from dataclass_wizard.v1 import AwarePattern
    >>> @dataclass
    ... class MyClass:
    ...     my_time_field: Annotated[list[time], AwarePattern('US/Eastern', '%H:%M:%S')]
    >>> LoadMeta(v1=True).bind_to(MyClass)
    """
    __class_getitem__ = __getitem__ = __init__
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
    >>> from dataclass_wizard import LoadMeta
    >>> from dataclass_wizard.v1 import UTCPattern
    >>> @dataclass
    ... class MyClass:
    ...     my_utc_field: Annotated[datetime, UTCPattern('%Y-%m-%d %H:%M:%S')]
    >>> LoadMeta(v1=True).bind_to(MyClass)
    """
    __class_getitem__ = __getitem__ = __init__
    # noinspection PyInitNewSignature
    def __init__(self, pattern): ...


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
    >>> from dataclass_wizard import LoadMeta
    >>> from dataclass_wizard.v1 import AwareTimePattern
    >>> @dataclass
    ... class MyClass:
    ...     my_aware_dt_field: AwareTimePattern['Europe/London', '%H:%M:%Z']
    >>> LoadMeta(v1=True).bind_to(MyClass)
    """
    __getitem__ = __init__
    # noinspection PyInitNewSignature
    def __init__(self, timezone, pattern): ...


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
    >>> from dataclass_wizard import LoadMeta
    >>> from dataclass_wizard.v1 import AwareDateTimePattern
    >>> @dataclass
    ... class MyClass:
    ...     my_aware_dt_field: AwareDateTimePattern['Asia/Tokyo', '%m-%Y-%H:%M-%Z']
    >>> LoadMeta(v1=True).bind_to(MyClass)
    """
    __getitem__ = __init__
    # noinspection PyInitNewSignature
    def __init__(self, timezone, pattern): ...


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
    >>> from dataclass_wizard import LoadMeta
    >>> from dataclass_wizard.v1 import DatePattern
    >>> @dataclass
    ... class MyClass:
    ...     my_date_field: DatePattern['%Y/%m/%d']
    >>> LoadMeta(v1=True).bind_to(MyClass)
    """
    __getitem__ = __init__
    # noinspection PyInitNewSignature
    def __init__(self, pattern): ...


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
    >>> from dataclass_wizard import LoadMeta
    >>> from dataclass_wizard.v1 import TimePattern
    >>> @dataclass
    ... class MyClass:
    ...     my_time_field: TimePattern['%H:%M:%S']
    >>> LoadMeta(v1=True).bind_to(MyClass)
    """
    __getitem__ = __init__
    # noinspection PyInitNewSignature
    def __init__(self, pattern): ...


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
    >>> from dataclass_wizard import LoadMeta
    >>> from dataclass_wizard.v1 import DateTimePattern
    >>> @dataclass
    ... class MyClass:
    ...     my_time_field: DateTimePattern['%d, %b, %Y %I:%M:%S %p']
    >>> LoadMeta(v1=True).bind_to(MyClass)
    """
    __getitem__ = __init__
    # noinspection PyInitNewSignature
    def __init__(self, pattern): ...


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
    >>> from dataclass_wizard import LoadMeta
    >>> from dataclass_wizard.v1 import UTCTimePattern
    >>> @dataclass
    ... class MyClass:
    ...     my_utc_time_field: UTCTimePattern['%H:%M:%S']
    >>> LoadMeta(v1=True).bind_to(MyClass)
    """
    __getitem__ = __init__
    # noinspection PyInitNewSignature
    def __init__(self, pattern): ...


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
    >>> from dataclass_wizard import LoadMeta
    >>> from dataclass_wizard.v1 import UTCDateTimePattern
    >>> @dataclass
    ... class MyClass:
    ...     my_utc_datetime_field: UTCDateTimePattern['%Y-%m-%d %H:%M:%S']
    >>> LoadMeta(v1=True).bind_to(MyClass)
    """
    __getitem__ = __init__
    # noinspection PyInitNewSignature
    def __init__(self, pattern): ...


# noinspection PyPep8Naming
def AliasPath(*all: PathType | str,
              load: PathType | str | None = None,
              dump: PathType | str | None = None,
              skip: bool = False,
              default=MISSING,
              default_factory: Callable[[], MISSING] = MISSING,
              init=True, repr=True,
              hash=None, compare=True, metadata=None, kw_only=False):
    """
    Creates a dataclass field mapped to one or more nested JSON paths.

    This function acts as an alias for ``dataclasses.field(...)``, with additional
    functionality to associate a field with one or more nested JSON paths,
    including complex or deeply nested structures.

    The mapping is case-sensitive, meaning that JSON keys must match exactly
    (e.g., "myField" will not match "myfield"). Nested paths can include dot
    notations or bracketed syntax for accessing specific indices or keys.

    :param all: One or more nested JSON paths to associate with
        the dataclass field (e.g., ``a.b.c`` or ``a["nested"]["key"]``).
    :type all: PathType | str
    :param load: Path(s) to use for deserialization. Defaults to ``all`` if not specified.
    :type load: PathType | str | None
    :param dump: Path(s) to use for serialization. Defaults to ``all`` if not specified.
    :type dump: PathType | str | None
    :param skip: If True, the field is excluded during serialization. Defaults to False.
    :type skip: bool
    :param default: Default value for the field. Cannot be used with ``default_factory``.
    :type default: Any
    :param default_factory: A callable to generate the default value. Cannot be used with ``default``.
    :type default_factory: Callable[[], Any]
    :param init: Whether the field is included in the generated ``__init__`` method. Defaults to True.
    :type init: bool
    :param repr: Whether the field appears in the ``__repr__`` output. Defaults to True.
    :type repr: bool
    :param hash: Whether the field is included in the ``__hash__`` method. Defaults to None.
    :type hash: bool
    :param compare: Whether the field is included in comparison methods. Defaults to True.
    :type compare: bool
    :param metadata: Additional metadata for the field. Defaults to None.
    :type metadata: dict
    :param kw_only: If True, the field is keyword-only. Defaults to False.
    :type kw_only: bool
    :return: A dataclass field with additional mapping to one or more nested JSON paths.
    :rtype: Field

    **Examples**

    **Example 1** -- Mapping multiple nested paths to a field::

        from dataclasses import dataclass

        from dataclass_wizard import fromdict, LoadMeta
        from dataclass_wizard.v1 import AliasPath

        @dataclass
        class Example:
            my_str: str = AliasPath('a.b.c.1', 'x.y["-1"].z', default="default_value")

        LoadMeta(v1=True).bind_to(Example)

        # Maps nested paths ('a', 'b', 'c', 1) and ('x', 'y', '-1', 'z')
        # to the `my_str` attribute. '-1' is treated as a literal string key,
        # not an index, for the second path.

        print(fromdict(Example, {'x': {'y': {'-1': {'z': 'some_value'}}}}))
        #> Example(my_str='some_value')

    **Example 2** -- Using Annotated::

        from dataclasses import dataclass
        from typing import Annotated

        from dataclass_wizard import JSONPyWizard
        from dataclass_wizard.v1 import AliasPath

        @dataclass
        class Example(JSONPyWizard):
            class _(JSONPyWizard.Meta):
                v1 = True

            my_str: Annotated[str, AliasPath('my."7".nested.path.-321')]


        ex = Example.from_dict({'my': {'7': {'nested': {'path': {-321: 'Test'}}}}})
        print(ex)  #> Example(my_str='Test')
    """


# noinspection PyPep8Naming
def Alias(*all: str,
          load: str | Sequence[str] | None = None,
          dump: str | None = None,
          skip: bool = False,
          default=MISSING,
          default_factory: Callable[[], MISSING] = MISSING,
          init=True, repr=True,
          hash=None, compare=True, metadata=None, kw_only=False):
    """
    Maps one or more JSON key names to a dataclass field.

    This function acts as an alias for ``dataclasses.field(...)``, with additional
    support for associating a field with one or more JSON keys. It customizes
    serialization and deserialization behavior, including handling keys with
    varying cases or alternative names.

    The mapping is case-sensitive; JSON keys must match exactly (e.g., ``myField``
    will not match ``myfield``). If multiple keys are provided, the first one
    is used as the default for serialization.

    :param all: One or more JSON key names to associate with the dataclass field.
    :type all: str
    :param load: Key(s) to use for deserialization. Defaults to ``all`` if not specified.
    :type load: str | Sequence[str] | None
    :param dump: Key to use for serialization. Defaults to the first key in ``all``.
    :type dump: str | None
    :param skip: If ``True``, the field is excluded during serialization. Defaults to ``False``.
    :type skip: bool
    :param default: Default value for the field. Cannot be used with ``default_factory``.
    :type default: Any
    :param default_factory: Callable to generate the default value. Cannot be used with ``default``.
    :type default_factory: Callable[[], Any]
    :param init: Whether the field is included in the generated ``__init__`` method. Defaults to ``True``.
    :type init: bool
    :param repr: Whether the field appears in the ``__repr__`` output. Defaults to ``True``.
    :type repr: bool
    :param hash: Whether the field is included in the ``__hash__`` method. Defaults to ``None``.
    :type hash: bool
    :param compare: Whether the field is included in comparison methods. Defaults to ``True``.
    :type compare: bool
    :param metadata: Additional metadata for the field. Defaults to ``None``.
    :type metadata: dict
    :param kw_only: If ``True``, the field is keyword-only. Defaults to ``False``.
    :type kw_only: bool
    :return: A dataclass field with additional mappings to one or more JSON keys.
    :rtype: Field

    **Examples**

    **Example 1** -- Mapping multiple key names to a field::

        from dataclasses import dataclass

        from dataclass_wizard import LoadMeta, fromdict
        from dataclass_wizard.v1 import Alias

        @dataclass
        class Example:
            my_field: str = Alias('key1', 'key2', default="default_value")

        LoadMeta(v1=True).bind_to(Example)

        print(fromdict(Example, {'key2': 'a value!'}))
        #> Example(my_field='a value!')

    **Example 2** -- Skipping a field during serialization::

        from dataclasses import dataclass

        from dataclass_wizard import JSONPyWizard
        from dataclass_wizard.v1 import Alias

        @dataclass
        class Example(JSONPyWizard):
            class _(JSONPyWizard.Meta):
                v1 = True

            my_field: str = Alias('key', skip=True)

        ex = Example.from_dict({'key': 'some value'})
        print(ex)                  #> Example(my_field='a value!')
        assert ex.to_dict() == {}  #> True
    """


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


class Field(_Field):
    """
    Alias to a :class:`dataclasses.Field`, but one which also represents a
    mapping of one or more JSON key names to a dataclass field.

    See the docs on the :func:`Alias` and :func:`AliasPath` for more info.
    """
    __slots__ = ('load_alias',
                 'dump_alias',
                 'skip',
                 'path')

    load_alias: str | None
    dump_alias: str | None
    # keys: tuple[str, ...] | PathType
    skip: bool
    path: PathType | None

    # In Python 3.10, dataclasses adds a new parameter to the :class:`Field`
    # constructor: `kw_only`
    #
    # Ref: https://docs.python.org/3.10/library/dataclasses.html#dataclasses.dataclass
    @overload
    def __init__(self,
                 load_alias: str | None,
                 dump_alias: str | None,
                 skip: bool,
                 path: PathType | None,
                 default, default_factory, init, repr, hash, compare,
                 metadata, kw_only):
        ...

    @overload
    def __init__(self,
                 load_alias: str | None,
                 dump_alias: str | None,
                 skip: bool,
                 path: PathType | None,
                 default, default_factory, init, repr, hash, compare,
                 metadata):
        ...
