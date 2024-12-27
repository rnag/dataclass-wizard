from collections import defaultdict
from dataclasses import MISSING, Field as _Field
from typing import Any, TypedDict

from ..constants import PY310_OR_ABOVE
from ..log import LOG
from ..type_def import DefFactory, ExplicitNull, PyNotRequired
# noinspection PyProtectedMember
from ..utils.object_path import split_object_path
from ..utils.typing_compat import get_origin_v2


_BUILTIN_COLLECTION_TYPES = frozenset({
    list,
    set,
    dict,
    tuple
})


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
                 index=None):

        self.name = name
        self.origin = origin
        self.args = args
        self.i = i
        self.field_i = field_i
        self.prefix = prefix
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
        locals = extras['locals']

        for tp in tps:
            locals.setdefault(tp.__name__, tp)

        for name, tp in name_to_tp.items():
            locals.setdefault(name, tp)

    def type_name(self, extras, bound=None):
        """Return type name as string (useful for `Union` type checks)"""
        if self.name is None:
            self.name = get_origin_v2(self.origin).__name__

        return self._wrap_inner(
            extras, force=True, bound=bound)

    def v(self):
        return (f'{self.prefix}{self.i}' if (idx := self.index) is None
                else f'{self.prefix}{self.i}[{idx}]')

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
            name = tp.__name__
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
            else:
                tn = f'{prefix}{name}_{self.field_i}'
                LOG.debug(f'Adding %s=%s', tn, name)
                extras['locals'][tn] = tp

            return tn

        return name if return_name else None

    def __str__(self):
        return getattr(self, '_wrapped', '')

    def __repr__(self):
        items = ', '.join([f'{v}={getattr(self, v)!r}'
                           for v in self.__slots__
                           if not v.startswith('_')])

        return f'{self.__class__.__name__}({items})'


class Extras(TypedDict):
    """
    "Extra" config that can be used in the load / dump process.
    """
    config: PyNotRequired['META']
    cls: type
    cls_name: str
    fn_gen: 'FunctionBuilder'
    locals: dict[str, Any]
    pattern: PyNotRequired['PatternedDT']
    recursion_guard: dict[type, str]


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

# In Python 3.10, dataclasses adds a new parameter to the :class:`Field`
# constructor: `kw_only`
#
# Ref: https://docs.python.org/3.10/library/dataclasses.html#dataclasses.dataclass
if PY310_OR_ABOVE:  # pragma: no cover

    # noinspection PyPep8Naming,PyShadowingBuiltins
    def Alias(all=None, *,
              load=None,
              dump=None,
              skip=False,
              path=None,
              default=MISSING,
              default_factory=MISSING,
              init=True, repr=True,
              hash=None, compare=True,
              metadata=None, kw_only=False):

        if default is not MISSING and default_factory is not MISSING:
            raise ValueError('cannot specify both default and default_factory')

        if all is not None:
            load = dump = all

        return Field(load, dump, skip, path, default, default_factory, init, repr,
                     hash, compare, metadata, kw_only)

    # noinspection PyPep8Naming,PyShadowingBuiltins
    def AliasPath(all=None, *,
                  load=None,
                  dump=None,
                  skip=False,
                  default=MISSING,
                  default_factory=MISSING,
                  init=True, repr=True,
                  hash=None, compare=True,
                  metadata=None, kw_only=False):

        if load is not None:
            all = load
            load = None
            dump = ExplicitNull

        elif dump is not None:
            all = dump
            dump = None
            load = ExplicitNull

        if isinstance(all, str):
            all = split_object_path(all)

        return Field(load, dump, skip, all, default, default_factory, init, repr,
                     hash, compare, metadata, kw_only)


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
    def Alias(all=None, *,
              load=None,
              dump=None,
              skip=False,
              path=None,
              default=MISSING,
              default_factory=MISSING,
              init=True, repr=True,
              hash=None, compare=True, metadata=None):

        if default is not MISSING and default_factory is not MISSING:
            raise ValueError('cannot specify both default and default_factory')

        if all is not None:
            load = dump = all

        return Field(load, dump, skip, path,
                     default, default_factory, init, repr,
                     hash, compare, metadata)

    # noinspection PyPep8Naming,PyShadowingBuiltins
    def AliasPath(all=None, *,
                  load=None,
                  dump=None,
                  skip=False,
                  default=MISSING,
                  default_factory=MISSING,
                  init=True, repr=True,
                  hash=None, compare=True,
                  metadata=None):

        if load is not None:
            all = load
            load = None
            dump = ExplicitNull

        elif dump is not None:
            all = dump
            dump = None
            load = ExplicitNull

        if isinstance(all, str):
            all = split_object_path(all)

        if isinstance(all, str):
            all = split_object_path(all)

        return Field(load, dump, skip, all, default, default_factory, init, repr,
                     hash, compare, metadata)


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
