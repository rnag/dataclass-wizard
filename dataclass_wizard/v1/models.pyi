from dataclasses import MISSING, Field as _Field, dataclass
from datetime import datetime, date, time
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

    def __init__(self, base, patterns=None): ...

    @overload
    def __getitem__(self, key: type[DT]) -> type[DT]: ...
    def __getitem__(self, key: tuple[type[DT], *tuple[str, ...]]) -> type[DT]: ...

    def load_to_pattern(self, tp: TypeInfo, extras: Extras): ...


Pattern = PatternBase(Any)
class DatePattern(date, Generic[T]): ...
class TimePattern(time, Generic[T]): ...
class DateTimePattern(datetime, Generic[T]): ...


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

    Args:
        all (PathType | str): One or more nested JSON paths to associate with
            the dataclass field (e.g., ``a.b.c`` or ``a["nested"]["key"]``).
        load (PathType | str | None): Path(s) to use for deserialization.
            Defaults to ``all`` if not specified.
        dump (PathType | str | None): Path(s) to use for serialization.
            Defaults to ``all`` if not specified.
        skip (bool): If True, the field is excluded during serialization. Defaults to False.
        default (Any): Default value for the field. Cannot be used with ``default_factory``.
        default_factory (Callable[[], Any]): A callable to generate the default value.
            Cannot be used with ``default``.
        init (bool): Whether the field is included in the generated ``__init__`` method. Defaults to True.
        repr (bool): Whether the field appears in the ``__repr__`` output. Defaults to True.
        hash (bool): Whether the field is included in the ``__hash__`` method. Defaults to None.
        compare (bool): Whether the field is included in comparison methods. Defaults to True.
        metadata (dict): Additional metadata for the field. Defaults to None.
        kw_only (bool): If True, the field is keyword-only. Defaults to False.

    Returns:
        Field: A dataclass field with additional mapping to one or more nested JSON paths.

    Examples:

        **Example 1** -- Mapping multiple nested paths to a field:

            >>> from dataclasses import dataclass
            >>> from dataclass_wizard.v1 import AliasPath
            >>> @dataclass
            >>> class Example:
            >>>     my_str: str = AliasPath('a.b.c.1', 'x.y["-1"].z', default="default_value")
            >>> # Maps nested paths ('a', 'b', 'c', 1) and ('x', 'y', '-1', 'z')
            >>> # to the `my_str` attribute. '-1' is treated as a literal string key,
            >>> # not an index, for the second path.

        **Example 2** -- Using ``Annotated``:

            >>> from typing import Annotated
            >>> my_str: Annotated[str, AliasPath('my."7".nested.path.-321')]
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
    support for associating a field with one or more JSON keys. It can be used
    to customize serialization and deserialization behavior, including handling
    keys with varying cases or alternative names.

    The mapping is case-sensitive, meaning that JSON keys must match exactly
    (e.g., "myField" will not match "myfield"). If multiple keys are provided,
    the first one is used as the default for serialization.

    Args:
        all (str): One or more JSON key names to associate with the dataclass field.
        load (str | Sequence[str] | None): Key(s) to use for deserialization.
            Defaults to ``all`` if not specified.
        dump (str | None): Key to use for serialization. Defaults to the first key in ``all``.
        skip (bool): If True, the field is excluded during serialization. Defaults to False.
        default (Any): Default value for the field. Cannot be used with ``default_factory``.
        default_factory (Callable[[], Any]): A callable to generate the default value.
            Cannot be used with `default`.
        init (bool): Whether the field is included in the generated ``__init__`` method. Defaults to True.
        repr (bool): Whether the field appears in the ``__repr__`` output. Defaults to True.
        hash (bool): Whether the field is included in the ``__hash__`` method. Defaults to None.
        compare (bool): Whether the field is included in comparison methods. Defaults to True.
        metadata (dict): Additional metadata for the field. Defaults to None.
        kw_only (bool): If True, the field is keyword-only. Defaults to False.

    Returns:
        Field: A dataclass field with additional mappings to one or more JSON keys.

    Examples:
        **Example 1**: Mapping multiple key names to a field.

        >>> from dataclasses import dataclass
        >>> from dataclass_wizard.v1 import Alias
        >>> @dataclass
        >>> class Example:
        >>>     my_field: str = Alias('key1', 'key2', default="default_value")

        **Example 2**: Skipping a field during serialization.

        >>> from dataclass_wizard.v1 import Alias
        >>> my_field: str = Alias('key', skip=True)
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

    See the docs on the :func:`json_field` function for more info.
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
