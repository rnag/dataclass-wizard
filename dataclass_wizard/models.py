from dataclasses import MISSING, Field as _Field
from typing import NewType, Mapping

from ._type_def import ExplicitNull
from .constants import PY310_OR_ABOVE, PY314_OR_ABOVE
from .utils._object_path import split_object_path


# Define a simple type (alias) for the `CatchAll` field
#
# The `type` statement is introduced in Python 3.12
# Ref: https://docs.python.org/3.12/reference/simple_stmts.html#type
#
# TODO: uncomment following usage of `type` statement
#   once we drop support for Python 3.9 - 3.11
# if PY312_OR_ABOVE:
#     type CatchAll = Mapping
CatchAll = NewType('CatchAll', Mapping)


def _normalize_alias_path_args(all_paths, load, dump):
    """Normalize `AliasPath` arguments and canonicalize path values."""
    if load is not None:
        all_paths = load
        load = None
        dump = ExplicitNull

    elif dump is not None:
        all_paths = dump
        dump = None
        load = ExplicitNull

    if isinstance(all_paths, str):
        all_paths = (split_object_path(all_paths),)
    else:
        all_paths = tuple([
            split_object_path(a) if isinstance(a, str) else a
            for a in all_paths
        ])

    return all_paths, load, dump


def _normalize_alias_args(default, default_factory, all_aliases, load, dump, env):
    """Normalize `Alias` arguments and canonicalize alias values."""

    if default is not MISSING and default_factory is not MISSING:
        raise ValueError('cannot specify both default and default_factory')

    if all_aliases:
        load = dump = all_aliases

    elif load is not None and isinstance(load, str):
        load = (load,)

    elif env is not None:
        if isinstance(env, str):
            env = (env,)
        elif env is True:
            env = load

    return all_aliases, load, dump, env


# Instances of Field are only ever created from within this module,
# and only from the field() function, although Field instances are
# exposed externally as (conceptually) read-only objects.
#
# name and type are filled in after the fact, not in __init__.
# They're not known at the time this class is instantiated, but it's
# convenient if they're available later.

# noinspection PyPep8Naming,PyShadowingBuiltins
def Env(*load,
        default=MISSING,
        default_factory=MISSING,
        init=True, repr=True,
        hash=None, compare=True, metadata=None,
        **field_kwargs):

    # noinspection PyTypeChecker
    return Alias(
        env=load,
        default=default,
        default_factory=default_factory,
        init=init,
        repr=repr,
        hash=hash,
        compare=compare,
        metadata=metadata,
        **field_kwargs,
    )

# In Python 3.14, dataclasses adds a new parameter to the :class:`Field`
# constructor: `doc`
#
# Ref: https://docs.python.org/3.14/library/dataclasses.html#dataclasses.field
if PY314_OR_ABOVE:
    # noinspection PyPep8Naming,PyShadowingBuiltins
    def Alias(
        *all,
        load=None,
        dump=None,
        env=None,
        skip=False,
        default=MISSING,
        default_factory=MISSING,
        init=True,
        repr=True,
        hash=None,
        compare=True,
        metadata=None,
        kw_only=MISSING,
        doc=None,
    ):

        all, load, dump, env = _normalize_alias_args(default, default_factory, all, load, dump, env)

        return Field(
            load,
            dump,
            env,
            skip,
            None,
            default,
            default_factory,
            init,
            repr,
            hash,
            compare,
            metadata,
            kw_only,
            doc,
        )

    # noinspection PyPep8Naming,PyShadowingBuiltins
    def AliasPath(
        *all,
        load=None,
        dump=None,
        skip=False,
        default=MISSING,
        default_factory=MISSING,
        init=True,
        repr=True,
        hash=None,
        compare=True,
        metadata=None,
        kw_only=MISSING,
        doc=None,
    ):
        all, load, dump = _normalize_alias_path_args(all, load, dump)

        return Field(
            load,
            dump,
            load,
            skip,
            all,
            default,
            default_factory,
            init,
            repr,
            hash,
            compare,
            metadata,
            kw_only,
            doc,
        )

    # noinspection PyShadowingBuiltins
    def skip_if_field(
        condition,
        *,
        default=MISSING,
        default_factory=MISSING,
        init=True,
        repr=True,
        hash=None,
        compare=True,
        metadata=None,
        kw_only=MISSING,
        doc=None,
    ):

        if default is not MISSING and default_factory is not MISSING:
            raise ValueError("cannot specify both default and default_factory")

        if metadata is None:
            metadata = {}

        metadata["__skip_if__"] = condition

        return _Field(
            default,
            default_factory,
            init,
            repr,
            hash,
            compare,
            metadata,
            kw_only,
            doc,
        )

    class Field(_Field):

        __slots__ = ("load_alias", "dump_alias", "env_vars", "skip", "path")

        # noinspection PyShadowingBuiltins
        def __init__(
            self,
            load_alias,
            dump_alias,
            env_vars,
            skip,
            path,
            default,
            default_factory,
            init,
            repr,
            hash,
            compare,
            metadata,
            kw_only,
            doc=None,
        ):

            # noinspection PyArgumentList
            super().__init__(
                default,
                default_factory,
                init,
                repr,
                hash,
                compare,
                metadata,
                kw_only,
                doc,
            )

            self.load_alias = load_alias
            self.dump_alias = dump_alias
            self.env_vars = env_vars
            self.skip = skip
            self.path = path


# In Python 3.10, dataclasses adds a new parameter to the :class:`Field`
# constructor: `kw_only`
#
# Ref: https://docs.python.org/3.10/library/dataclasses.html#dataclasses.dataclass
elif PY310_OR_ABOVE:  # pragma: no cover

    # noinspection PyPep8Naming,PyShadowingBuiltins
    def Alias(*all,
              load=None,
              dump=None,
              env=None,
              skip=False,
              default=MISSING,
              default_factory=MISSING,
              init=True, repr=True,
              hash=None, compare=True,
              metadata=None, kw_only=MISSING):

        all, load, dump, env = _normalize_alias_args(default, default_factory, all, load, dump, env)

        return Field(
            load,
            dump,
            env,
            skip,
            None,
            default,
            default_factory,
            init,
            repr,
            hash,
            compare,
            metadata,
            kw_only,
        )

    # noinspection PyPep8Naming,PyShadowingBuiltins
    def AliasPath(*all,
                  load=None,
                  dump=None,
                  skip=False,
                  default=MISSING,
                  default_factory=MISSING,
                  init=True, repr=True,
                  hash=None, compare=True,
                  metadata=None, kw_only=MISSING):
        all, load, dump = _normalize_alias_path_args(all, load, dump)

        return Field(
            load,
            dump,
            load,
            skip,
            all,
            default,
            default_factory,
            init,
            repr,
            hash,
            compare,
            metadata,
            kw_only,
        )

    # noinspection PyShadowingBuiltins
    def skip_if_field(
        condition,
        *,
        default=MISSING,
        default_factory=MISSING,
        init=True,
        repr=True,
        hash=None,
        compare=True,
        metadata=None,
        kw_only=MISSING
    ):

        if default is not MISSING and default_factory is not MISSING:
            raise ValueError("cannot specify both default and default_factory")

        if metadata is None:
            metadata = {}

        metadata["__skip_if__"] = condition

        return _Field(
            default,
            default_factory,
            init,
            repr,
            hash,
            compare,
            metadata,
            kw_only,
        )

    class Field(_Field):

        __slots__ = ('load_alias',
                     'dump_alias',
                     'env_vars',
                     'skip',
                     'path')

        # noinspection PyShadowingBuiltins
        def __init__(self,
                     load_alias, dump_alias, env_vars, skip, path,
                     default, default_factory, init, repr, hash, compare,
                     metadata, kw_only):

            super().__init__(default, default_factory, init, repr, hash,
                             compare, metadata, kw_only)

            if path is not None:
                if isinstance(path, str):
                    path = split_object_path(path) if path else (path, )

            self.load_alias = load_alias
            self.dump_alias = dump_alias
            self.env_vars = env_vars
            self.skip = skip
            self.path = path

else:  # pragma: no cover
    # noinspection PyPep8Naming,PyShadowingBuiltins
    def Alias(*all,
              load=None,
              dump=None,
              env=None,
              skip=False,
              default=MISSING,
              default_factory=MISSING,
              init=True, repr=True,
              hash=None, compare=True, metadata=None):

        all, load, dump, env = _normalize_alias_args(default, default_factory, all, load, dump, env)

        return Field(
            load,
            dump,
            env,
            skip,
            None,
            default,
            default_factory,
            init,
            repr,
            hash,
            compare,
            metadata,
        )

    # noinspection PyPep8Naming,PyShadowingBuiltins
    def AliasPath(*all,
                  load=None,
                  dump=None,
                  skip=False,
                  default=MISSING,
                  default_factory=MISSING,
                  init=True, repr=True,
                  hash=None, compare=True,
                  metadata=None):
        all, load, dump = _normalize_alias_path_args(all, load, dump)

        return Field(
            load,
            dump,
            load,
            skip,
            all,
            default,
            default_factory,
            init,
            repr,
            hash,
            compare,
            metadata,
        )

    # noinspection PyShadowingBuiltins
    def skip_if_field(
        condition,
        *,
        default=MISSING,
        default_factory=MISSING,
        init=True,
        repr=True,
        hash=None,
        compare=True,
        metadata=None
    ):

        if default is not MISSING and default_factory is not MISSING:
            raise ValueError("cannot specify both default and default_factory")

        if metadata is None:
            metadata = {}

        metadata["__skip_if__"] = condition

        # noinspection PyArgumentList
        return _Field(
            default,
            default_factory,
            init,
            repr,
            hash,
            compare,
            metadata,
        )

    class Field(_Field):

        __slots__ = ('load_alias',
                     'dump_alias',
                     'env_vars',
                     'skip',
                     'path')

        # noinspection PyArgumentList,PyShadowingBuiltins
        def __init__(self,
                     load_alias, dump_alias, env_vars, skip, path,
                     default, default_factory, init, repr, hash, compare,
                     metadata):

            super().__init__(default, default_factory, init, repr, hash,
                             compare, metadata)

            if path is not None:
                if isinstance(path, str):
                    path = split_object_path(path) if path else (path,)

            self.load_alias = load_alias
            self.dump_alias = dump_alias
            self.env_vars = env_vars
            self.skip = skip
            self.path = path


Alias.__doc__ = """
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

        from dataclass_wizard import Alias, LoadMeta, fromdict

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

AliasPath.__doc__ = """
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

Field.__doc__ = """
    Alias to a :class:`dataclasses.Field`, but one which also represents a
    mapping of one or more JSON key names to a dataclass field.

    See the docs on the :func:`Alias` and :func:`AliasPath` for more info.
"""
