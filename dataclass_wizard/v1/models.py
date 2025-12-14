import hashlib
from collections import defaultdict
from dataclasses import MISSING, Field as _Field
from datetime import datetime, date, time, tzinfo, timezone, timedelta
from typing import TYPE_CHECKING, Any, TypedDict, cast
from zoneinfo import ZoneInfo

from .decorators import setup_recursive_safe_function
from ..constants import PY310_OR_ABOVE, PY311_OR_ABOVE, PY314_OR_ABOVE
from ..log import LOG
from ..type_def import DefFactory, ExplicitNull, PyNotRequired, NoneType
from ..utils.function_builder import FunctionBuilder
from ..utils.object_path import split_object_path
from ..utils.typing_compat import get_origin_v2


if TYPE_CHECKING:  # pragma: no cover
    from ..bases import META


# UTC Time Zone
UTC: timezone = timezone.utc

# UTC time zone (no offset)
ZERO: timedelta = timedelta(0)

_BUILTIN_COLLECTION_TYPES = frozenset({
    list,
    set,
    dict,
    tuple
})

# Atomic immutable types which don't require any recursive handling and for which deepcopy
# returns the same object. We can provide a fast-path for these types in asdict and astuple.
SIMPLE_TYPES = (
    # Common JSON Serializable types
    NoneType,
    bool,
    int,
    float,
    str,
    # Other common types
    complex,
    bytes,
    # TODO support
    # Other types that are also unaffected by deepcopy
    # types.EllipsisType,
    # types.NotImplementedType,
    # types.CodeType,
    # types.BuiltinFunctionType,
    # types.FunctionType,
    # type,
    # range,
    # property,
)

SCALAR_TYPES = (
    str,
    int,
    float,
    bool,
)


class TypeInfo:

    __slots__ = (
        # type origin (ex. `List[str]` -> `List`)
        'origin',
        # type arguments (ex. `Dict[str, int]` -> `(str, int)`)
        'args',
        # name of type origin (ex. `List[str]` -> 'list')
        'name',
        # index of iteration, *only* unique within the scope of a field assignment!
        'i',
        # index of field within the dataclass, *guaranteed* to be unique.
        'field_i',
        # prefix of value in assignment (prepended to `i`),
        # defaults to 'v' if not specified.
        'prefix',
        # index of assignment (ex. `2 -> v1[2]`, *or* a string `"key" -> v4["key"]`)
        'index',
        # explicit value name (overrides prefix + index)
        'val_name',
        # optional attribute, that indicates if we should wrap the
        # assignment with `name` -- ex. `(1, 2)` -> `deque((1, 2))`
        '_wrapped',
        # optional attribute, that indicates if we are currently in Optional,
        # e.g. `typing.Optional[...]` *or* `typing.Union[T, ...*T2, None]`
        '_in_opt',
    )

    def __init__(self, origin,
                 args=None,
                 name=None,
                 i=1,
                 field_i=1,
                 prefix='v',
                 val_name=None,
                 index=None):

        self.name = name
        self.origin = origin
        self.args = args
        self.i = i
        self.field_i = field_i
        self.prefix = prefix
        self.val_name = val_name
        self.index = index

    def replace(self, **changes):
        # Validate that `instance` is an instance of the class
        # if not isinstance(instance, TypeInfo):
        #     raise TypeError(f"Expected an instance of {TypeInfo.__name__}, got {type(instance).__name__}")

        # Extract current values from __slots__
        current_values = {slot: getattr(self, slot)
                          for slot in TypeInfo.__slots__
                          if not slot.startswith('_')}

        # Apply the changes
        current_values.update(changes)

        # Create and return a new instance with updated attributes
        # noinspection PyArgumentList
        return TypeInfo(**current_values)

    @property
    def in_optional(self):
        return getattr(self, '_in_opt', False)

    # noinspection PyUnresolvedReferences
    @in_optional.setter
    def in_optional(self, value):
        # noinspection PyAttributeOutsideInit
        self._in_opt = value

    @staticmethod
    def ensure_in_locals(extras, *tps, **name_to_tp):
        _locals = extras['locals']

        for tp in tps:
            _locals.setdefault(tp.__name__, tp)

        for name, tp in name_to_tp.items():
            _locals.setdefault(name, tp)

    def type_name(self, extras, bound=None):
        """Return type name as string (useful for `Union` type checks)"""
        if self.name is None:
            self.name = get_origin_v2(self.origin).__name__

        return self._wrap_inner(
            extras, force=True, bound=bound)

    def v(self):
        val_name = self.val_name
        if val_name is None:
            val_name = f'{self.prefix}{self.i}'
        return (val_name if (idx := self.index) is None
                else f'{val_name}[{idx}]')

    def v_and_next(self):
        next_i = self.i + 1
        return self.v(), f'v{next_i}', next_i

    def v_and_next_k_v(self):
        next_i = self.i + 1
        return self.v(), f'k{next_i}', f'v{next_i}', next_i

    def wrap_dd(self, default_factory: DefFactory, result: str, extras):
        tn = self._wrap_inner(extras, is_builtin=True, bound=defaultdict)
        tn_df = self._wrap_inner(extras, default_factory)
        result = f'{tn}({tn_df}, {result})'
        setattr(self, '_wrapped', result)
        return self

    def multi_wrap(self, extras, prefix='', *result, force=False):
        tn = self._wrap_inner(extras, prefix=prefix, force=force)
        if tn is not None:
            result = [f'{tn}({r})' for r in result]

        return result

    def wrap(self, result: str, extras, force=False, prefix='', bound=None):
        if (tn := self._wrap_inner(
                extras, prefix=prefix, force=force,
                bound=bound)) is not None:
            result = f'{tn}({result})'

        setattr(self, '_wrapped', result)
        return self

    def wrap_builtin(self, bound, result, extras):
        tn = self._wrap_inner(extras, is_builtin=True, bound=bound)
        result = f'{tn}({result})'

        setattr(self, '_wrapped', result)
        return self

    def _wrap_inner(self, extras,
                    tp=None,
                    prefix='',
                    is_builtin=False,
                    force=False,
                    bound=None) -> 'str | None':

        if tp is None:
            tp = self.origin
            name = self.name
            return_name = force
        else:
            name = 'None' if tp is NoneType else tp.__name__
            return_name = True

        # This ensures we don't create a "unique" name
        # if it's a non-subclass, e.g. ensures we end
        # up with `date` instead of `date_123`.
        if bound is not None:
            is_builtin = tp is bound

        if tp not in _BUILTIN_COLLECTION_TYPES:
            if (mod := tp.__module__) == 'builtins':
                tn = name
            elif (is_builtin
                  or mod == 'collections'):
                tn = name
                LOG.debug(f'Ensuring %s=%s', tn, name)
                extras['locals'].setdefault(tn, tp)
            elif mod == 'builtins':
                tn = name
            else:
                # TODO might need to handle `var_name`
                tn = f'{prefix}{name}_{self.field_i}'
                LOG.debug(f'Adding %s=%s', tn, name)
                extras['locals'][tn] = tp

            return tn

        return name if return_name else None

    def __str__(self):
        return getattr(self, '_wrapped', '')

    def __repr__(self):  # pragma: no cover
        items = ', '.join([f'{v}={getattr(self, v)!r}'
                           for v in self.__slots__
                           if not v.startswith('_')])

        return f'{self.__class__.__name__}({items})'


class Extras(TypedDict):
    """
    "Extra" config that can be used in the load / dump process.
    """
    config: 'META'
    cls: type
    cls_name: str
    fn_gen: FunctionBuilder
    locals: dict[str, Any]
    pattern: PyNotRequired['PatternBase']
    recursion_guard: dict[type, str]


class PatternBase:

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
                tz_info = ZoneInfo(tz_info)
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
    def load_to_pattern(self, tp: TypeInfo, extras: Extras):
        from .type_conv import as_datetime_v1, as_date_v1, as_time_v1

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
            _as_func_args = f'v1, {_fromtimestamp}, __tz' if has_tz else f'v1, {_fromtimestamp}'
            name_to_func[_as_func] = as_datetime_v1
            # `datetime` has a `fromtimestamp` method
            name_to_func[_fromtimestamp] = __base__.fromtimestamp
            end_part = ''
        elif is_date:
            _as_func = '__as_date'
            _as_func_args = f'v1, {_fromtimestamp}'
            name_to_func[_as_func] = as_date_v1
            # `date` has a `fromtimestamp` method
            name_to_func[_fromtimestamp] = __base__.fromtimestamp
            end_part = '.date()'
        else:
            _as_func = '__as_time'
            _as_func_args = f'v1, cls'
            name_to_func[_as_func] = as_time_v1
            end_part = '.timetz()' if has_tz else '.time()'

        tp.ensure_in_locals(extras, **name_to_func)

        if PY311_OR_ABOVE:
            _parse_iso_string = f'{_fromisoformat}(v1){tz_part}'
            errors_to_except = (TypeError, )
        else:  # pragma: no cover
            _parse_iso_string = f"{_fromisoformat}(v1.replace('Z', '+00:00', 1)){tz_part}"
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

                        fn_gen.add_line(f'__dt = {_strptime}(v1, {p!r})')
                        fn_gen.add_line('return cls('
                                        '__dt.hour, '
                                        '__dt.minute, '
                                        '__dt.second, '
                                        '__dt.microsecond, '
                                        f'{tz_arg}fold=__dt.fold)')
                    else:
                        fn_gen.add_line(f'return {_strptime}(v1, {p!r}){tz_part}{end_part}')
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
                            fn_gen.add_line(f'__dt = {_strptime}(v1, {p!r})')
                            fn_gen.add_line('return cls('
                                            '__dt.year, '
                                            '__dt.month, '
                                            '__dt.day)')
                        elif is_subclass_time:
                            fn_gen.add_line(f'__dt = {_strptime}(v1, {p!r})')
                            tz_arg = '__tz, ' if has_tz else ''

                            fn_gen.add_line('return cls('
                                            '__dt.hour, '
                                            '__dt.minute, '
                                            '__dt.second, '
                                            '__dt.microsecond, '
                                            f'{tz_arg}fold=__dt.fold)')
                        else:
                            fn_gen.add_line(f'return {_strptime}(v1, {p!r}){tz_part}{end_part}')
                    with fn_gen.except_(Exception):
                        fn_gen.add_line('pass')
        # Raise a helpful error if we are unable to parse
        # the date string with the provided patterns.
        fn_gen.add_line(
            'raise ValueError(f"Unable to parse the string \'{v1}\' '
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


def _normalize_alias_args(default, default_factory, all_aliases, load, dump):
    """Normalize `Alias` arguments and canonicalize alias values."""

    if default is not MISSING and default_factory is not MISSING:
        raise ValueError('cannot specify both default and default_factory')

    if all_aliases:
        load = dump = all_aliases

    elif load is not None and isinstance(load, str):
        load = (load,)

    return all_aliases, load, dump


# Instances of Field are only ever created from within this module,
# and only from the field() function, although Field instances are
# exposed externally as (conceptually) read-only objects.
#
# name and type are filled in after the fact, not in __init__.
# They're not known at the time this class is instantiated, but it's
# convenient if they're available later.
#
# When cls._FIELDS is filled in with a list of Field objects, the name
# and type fields will have been populated.

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
        skip=False,
        default=MISSING,
        default_factory=MISSING,
        init=True,
        repr=True,
        hash=None,
        compare=True,
        metadata=None,
        kw_only=False,
        doc=None,
    ):

        all, load, dump = _normalize_alias_args(default, default_factory, all, load, dump)

        return Field(
            load,
            dump,
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
        kw_only=False,
        doc=None,
    ):
        all, load, dump = _normalize_alias_path_args(all, load, dump)

        return Field(
            load,
            dump,
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

    class Field(_Field):

        __slots__ = ("load_alias", "dump_alias", "skip", "path")

        # noinspection PyShadowingBuiltins
        def __init__(
            self,
            load_alias,
            dump_alias,
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
              skip=False,
              path=None,
              default=MISSING,
              default_factory=MISSING,
              init=True, repr=True,
              hash=None, compare=True,
              metadata=None, kw_only=False):

        all, load, dump = _normalize_alias_args(default, default_factory, all, load, dump)

        return Field(
            load,
            dump,
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
                  metadata=None, kw_only=False):
        all, load, dump = _normalize_alias_path_args(all, load, dump)

        return Field(
            load,
            dump,
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

    class Field(_Field):

        __slots__ = ('load_alias',
                     'dump_alias',
                     'skip',
                     'path')

        # noinspection PyShadowingBuiltins
        def __init__(self,
                     load_alias, dump_alias, skip, path,
                     default, default_factory, init, repr, hash, compare,
                     metadata, kw_only):

            super().__init__(default, default_factory, init, repr, hash,
                             compare, metadata, kw_only)

            if path is not None:
                if isinstance(path, str):
                    path = split_object_path(path) if path else (path, )

            self.load_alias = load_alias
            self.dump_alias = dump_alias
            self.skip = skip
            self.path = path

else:  # pragma: no cover
    # noinspection PyPep8Naming,PyShadowingBuiltins
    def Alias(*all,
              load=None,
              dump=None,
              skip=False,
              path=None,
              default=MISSING,
              default_factory=MISSING,
              init=True, repr=True,
              hash=None, compare=True, metadata=None):

        all, load, dump = _normalize_alias_args(default, default_factory, all, load, dump)

        return Field(
            load,
            dump,
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

    class Field(_Field):

        __slots__ = ('load_alias',
                     'dump_alias',
                     'skip',
                     'path')

        # noinspection PyArgumentList,PyShadowingBuiltins
        def __init__(self,
                     load_alias, dump_alias, skip, path,
                     default, default_factory, init, repr, hash, compare,
                     metadata):

            super().__init__(default, default_factory, init, repr, hash,
                             compare, metadata)

            if path is not None:
                if isinstance(path, str):
                    path = split_object_path(path) if path else (path,)

            self.load_alias = load_alias
            self.dump_alias = dump_alias
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

Field.__doc__ = """
    Alias to a :class:`dataclasses.Field`, but one which also represents a
    mapping of one or more JSON key names to a dataclass field.

    See the docs on the :func:`Alias` and :func:`AliasPath` for more info.
"""
