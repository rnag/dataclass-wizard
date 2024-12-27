from dataclasses import MISSING, Field as _Field, dataclass
from typing import (Collection, Callable,
                    Mapping)
from typing import TypedDict, overload, Any, NotRequired, Self

from ..bases import META
from ..models import Condition
from ..type_def import DefFactory
from ..utils.function_builder import FunctionBuilder
from ..utils.object_path import PathType


# Define a simple type (alias) for the `CatchAll` field
CatchAll = Mapping | None

# Type for a string or a collection of strings.
_STR_COLLECTION = str | Collection[str]


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
    config: NotRequired[META]
    cls: type
    cls_name: str
    fn_gen: FunctionBuilder
    locals: dict[str, Any]
    pattern: NotRequired[PatternedDT]
    recursion_guard: dict[type, str]


# noinspection PyPep8Naming
def AliasPath(all: PathType | str | None = None, *,
              load : PathType | str | None = None,
              dump : PathType | str | None = None,
              skip: bool = False,
              default=MISSING,
              default_factory: Callable[[], MISSING] = MISSING,
              init=True, repr=True,
              hash=None, compare=True, metadata=None, kw_only=False):
    """
    Creates a dataclass field mapped to one or more nested JSON paths.

    This function is an alias for ``dataclasses.field(...)``, with additional
    logic for associating a field with one or more JSON key paths, including
    nested structures. It can be used to specify custom mappings between
    dataclass fields and complex, nested JSON key names.

    This mapping is **case-sensitive** and applies to the provided JSON keys
    or nested paths. For example, passing "myField" will not match "myfield"
    in JSON, and vice versa.

    `all` represents one or more nested JSON keys (as strings or a collection of strings)
    to associate with the dataclass field. The keys can include paths like `a.b.c`
    or even more complex nested paths such as `a["nested"]["key"]`.

    Arguments:
        all (_STR_COLLECTION): The JSON key(s) or nested path(s) to associate with the dataclass field.
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

    Example #1:
        >>> from dataclasses import dataclass
        >>> @dataclass
        >>> class Example:
        >>>     my_str: str = AliasPath(['a.b.c.1', 'x.y["-1"].z'], default=42)
        >>> # Maps nested paths ('a', 'b', 'c', 1) and ('x', 'y', '-1', 'z')
        >>> # to the `my_str` attribute.

    Example #2:

    >>> from typing import Annotated
    >>> my_str: Annotated[str, AliasPath('my."7".nested.path.-321')]
    >>> # where path.keys == ('my', '7', 'nested', 'path', -321)
    """


# noinspection PyPep8Naming
def Alias(all: str | None = None, *,
          load: str | None = None,
          dump: str | None = None,
          skip: bool = False,
          path: PathType | str | None = None,
          default=MISSING,
          default_factory: Callable[[], MISSING] = MISSING,
          init=True, repr=True,
          hash=None, compare=True, metadata=None, kw_only=False):
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
                 path: PathType, default, default_factory, init, repr, hash, compare,
                 metadata, kw_only):
        ...

    @overload
    def __init__(self, alias: str | None,
                 load_alias: str | None,
                 dump_alias: str | None,
                 skip: bool,
                 path: PathType, default, default_factory, init, repr, hash, compare,
                 metadata):
        ...
