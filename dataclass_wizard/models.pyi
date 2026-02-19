# noinspection PyProtectedMember
from dataclasses import MISSING, Field as _Field, _MISSING_TYPE
from typing import Sequence, TypeAlias, Mapping, Literal
from typing import overload, Any

from ._type_def import DefFactory, T
from .conditions import Condition
from .utils._object_path import PathType

# Define a simple type (alias) for the `CatchAll` field
CatchAll: TypeAlias = Mapping | None

# noinspection PyPep8Naming
def AliasPath(*all: PathType | str,
              load: PathType | str | None = None,
              dump: PathType | str | None = None,
              skip: bool = False,
              default: Any = MISSING,
              default_factory: DefFactory[T] | Literal[_MISSING_TYPE.MISSING] = MISSING,
              init: bool = True,
              repr: bool = True,
              hash: bool | None = None,
              compare: bool = True,
              metadata: Mapping[Any, Any] | None = None,
              kw_only: bool = False) -> Field:
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

        from dataclass_wizard import AliasPath, fromdict

        @dataclass
        class Example:
            my_str: str = AliasPath('a.b.c.1', 'x.y["-1"].z', default="default_value")

        # Maps nested paths ('a', 'b', 'c', 1) and ('x', 'y', '-1', 'z')
        # to the `my_str` attribute. '-1' is treated as a literal string key,
        # not an index, for the second path.

        print(fromdict(Example, {'x': {'y': {'-1': {'z': 'some_value'}}}}))
        #> Example(my_str='some_value')

    **Example 2** -- Using Annotated::

        from dataclasses import dataclass
        from typing import Annotated

        from dataclass_wizard import AliasPath, JSONWizard

        @dataclass
        class Example(JSONWizard):
            my_str: Annotated[str, AliasPath('my."7".nested.path.-321')]


        ex = Example.from_dict({'my': {'7': {'nested': {'path': {-321: 'Test'}}}}})
        print(ex)  #> Example(my_str='Test')
    """


# noinspection PyPep8Naming
def Alias(*all: str,
          load: str | Sequence[str] | None = None,
          dump: str | None = None,
          env: str | Sequence[str] | None = None,
          skip: bool = False,
          default=MISSING,
          default_factory: DefFactory[T] | Literal[_MISSING_TYPE.MISSING] = MISSING,
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
    :param env: Environment variable(s) to use for deserialization.
    :type env: str | Sequence[str] | None
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

        from dataclass_wizard import Alias, fromdict

        @dataclass
        class Example:
            my_field: str = Alias('key1', 'key2', default="default_value")

        print(fromdict(Example, {'key2': 'a value!'}))
        #> Example(my_field='a value!')

    **Example 2** -- Skipping a field during serialization::

        from dataclasses import dataclass

        from dataclass_wizard import Alias, JSONWizard

        @dataclass
        class Example(JSONWizard):
            my_field: str = Alias('key', skip=True)

        ex = Example.from_dict({'key': 'some value'})
        print(ex)                  #> Example(my_field='a value!')
        assert ex.to_dict() == {}  #> True
    """


# noinspection PyPep8Naming
def Env(*load: str,
        default=MISSING,
        default_factory: DefFactory[T] | Literal[_MISSING_TYPE.MISSING] = MISSING,
        init=True, repr=True,
        hash=None, compare=True, metadata=None, kw_only=False):
    """
    Maps one or more Environment Variable names to a dataclass field.

    This function acts as an alias for ``dataclasses.field(...)``, with additional
    support for associating a field with one or more env vars. It customizes
    serialization and deserialization behavior, including handling env vars with
    varying cases or alternative names.

    The mapping is case-sensitive; env vars must match exactly (e.g., ``myField``
    will not match ``myfield``).

    :param load: Env vars(s) to use for deserialization.
    :type load: str
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

        from dataclass_wizard import Alias, fromdict

        @dataclass
        class Example:
            my_field: str = Alias('key1', 'key2', default="default_value")

        print(fromdict(Example, {'key2': 'a value!'}))
        #> Example(my_field='a value!')

    **Example 2** -- Skipping a field during serialization::

        from dataclasses import dataclass

        from dataclass_wizard import Alias, JSONWizard

        @dataclass
        class Example(JSONWizard):
            my_field: str = Alias('key', skip=True)

        ex = Example.from_dict({'key': 'some value'})
        print(ex)                  #> Example(my_field='a value!')
        assert ex.to_dict() == {}  #> True
    """


def skip_if_field(condition: Condition, *,
                  default=MISSING,
                  default_factory: DefFactory[T] | Literal[_MISSING_TYPE.MISSING] = MISSING,
                  init=True, repr=True,
                  hash=None, compare=True, metadata=None,
                  kw_only: bool | Literal[_MISSING_TYPE.MISSING] = MISSING):
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
        >>> from dataclass_wizard.conditions import IS_NOT
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
                 'env_vars',
                 'skip',
                 'path')

    load_alias: str | None
    dump_alias: str | None
    env_vars: str | None
    skip: bool
    path: PathType | None

    # In Python 3.14, dataclasses adds a new parameter to the :class:`Field`
    # constructor: `doc`
    #
    # Ref: https://docs.python.org/3.14/library/dataclasses.html#dataclasses.field
    @overload
    def __init__(self,
                 load_alias: str | None,
                 dump_alias: str | None,
                 env_vars: str | None,
                 skip: bool,
                 path: PathType | None,
                 default, default_factory, init, repr, hash, compare,
                 metadata, kw_only, doc):
        ...

    # In Python 3.10, dataclasses adds a new parameter to the :class:`Field`
    # constructor: `kw_only`
    #
    # Ref: https://docs.python.org/3.10/library/dataclasses.html#dataclasses.dataclass
    @overload
    def __init__(self,
                 load_alias: str | None,
                 dump_alias: str | None,
                 env_vars: str | None,
                 skip: bool,
                 path: PathType | None,
                 default, default_factory, init, repr, hash, compare,
                 metadata, kw_only):
        ...

    @overload
    def __init__(self,
                 load_alias: str | None,
                 dump_alias: str | None,
                 env_vars: str | None,
                 skip: bool,
                 path: PathType | None,
                 default, default_factory, init, repr, hash, compare,
                 metadata):
        ...
