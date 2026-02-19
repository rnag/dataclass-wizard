import types
from collections import defaultdict, deque
from typing import TYPE_CHECKING, TypedDict, Any

from ._log import LOG
from ._type_def import META, DefFactory, PyNotRequired, NoneType
from ._type_utils import is_builtin
from .utils._function_builder import FunctionBuilder
from .utils._typing_compat import get_origin_v2

if TYPE_CHECKING:
    from .patterns import PatternBase


_BUILTIN_COLLECTION_TYPES = frozenset({
    list,
    set,
    dict,
    tuple,
    frozenset,
})

# FIXME: Python 3.9 doesn't have `types.EllipsisType` or `types.NotImplementedType`
EllipsisType = getattr(types, 'EllipsisType', type(Ellipsis))
NotImplementedType = getattr(types, 'NotImplementedType', type(NotImplemented))

LEAF_TYPES_NO_BYTES = frozenset({
    # Common JSON Serializable types
    NoneType,
    bool,
    int,
    float,
    str,
    # Other common types
    complex,
    # exclude bytes, since the serialization process is slightly different
    # Other types that are also unaffected by deepcopy
    EllipsisType,
    NotImplementedType,
    types.CodeType,
    types.BuiltinFunctionType,
    types.FunctionType,
    type,
    range,
    property,
})

# Atomic immutable types which don't require any recursive handling and for which deepcopy
# returns the same object. We can provide a fast-path for these types in asdict and astuple.
#
# Credits: `_ATOMIC_TYPES` from `dataclasses.py`
LEAF_TYPES = LEAF_TYPES_NO_BYTES | {bytes}

SEQUENCE_ORIGINS = frozenset({
    list,
    tuple,
    set,
    frozenset,
    deque
})

MAPPING_ORIGINS = frozenset({
    dict,
    defaultdict
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


        if ((new_idx := changes.get('index')) is not None
            and (curr_idx := current_values['index']) is not None):
            if isinstance(curr_idx, (int, str)):
                changes['index'] = (curr_idx, new_idx)
            else:
                changes['index'] = curr_idx + (new_idx, )

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
        names = [ensure_type_ref(extras, tp) for tp in tps]

        for name, tp in name_to_tp.items():
            extras['locals'].setdefault(name, tp)

        return names

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
        idx = self.index
        if idx is None:
            return val_name
        else:
            if isinstance(idx, (int, str)):
                return f'{val_name}[{idx}]'
            return f"{val_name}{''.join(f'[{i}]' for i in idx)}"

    def v_for_def(self):
        """
        Returns a safe value for function `def` statements (e.g., no
        dot (.) or indices [])
        """
        return f'{self.prefix}{self.i}'

    def v_and_next(self):
        next_i = self.i + 1
        return self.v(), f'{self.prefix}{next_i}', next_i

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
        tn = self._wrap_inner(extras, prefix=prefix, force=force, bound=bound)
        if tn is not None:
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

        # If the type is the bound itself, treat it as "builtin" in naming
        # (i.e., don't generate unique alias)
        #
        # This ensures we don't create a "unique" name
        # if it's a non-subclass, e.g. ensures we end
        # up with `date` instead of `date_123`.
        if bound is not None:
            is_builtin = tp is bound

        if tp not in _BUILTIN_COLLECTION_TYPES:
            return ensure_type_ref(
                extras,
                tp,
                name=name,
                prefix=prefix,
                is_builtin=is_builtin,
            )

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


def ensure_type_ref(extras, tp, *, name=None, prefix='', is_builtin=False) -> str:
    """
    Return a safe symbol name for `tp` to use in generated code.

    Adds entries to `extras['locals']` only when required (non-builtins,
    non-collection literals, and cases where a stable local alias is needed).
    """
    if tp is NoneType:
        return 'None'

    if name is None:
        name = tp.__name__

    # Common built-in collections: always use the literal names directly.
    if tp in _BUILTIN_COLLECTION_TYPES:
        return name

    mod = tp.__module__

    # Builtins: can be referenced directly without injecting into locals.
    # Includes str/int/float/bool/bytes and also built-in collection types.
    if mod == 'builtins':
        return name

    if is_builtin or mod == 'collections':
        LOG.debug('Ensuring %s=%s', name, name)
        extras['locals'].setdefault(name, tp)
        return name

    _locals = extras['locals']

    # If the type name is safe and not used yet, inject it.
    # You may want stricter collision checks here.
    if name not in _locals:
        _locals[name] = tp
        return name

    # Collision: create a unique alias.
    # TODO might need to handle `var_name`
    alias = f'{prefix}{name}'
    LOG.debug('Adding %s=%s', alias, name)
    _locals.setdefault(alias, tp)

    return alias


def finalize_skip_if(skip_if, operand_1, conditional):
    """
    Finalizes the skip condition by generating the appropriate string based on the condition.

    Args:
        skip_if (Condition): The condition to evaluate, containing truthiness and operation info.
        operand_1 (str): The primary operand for the condition (e.g., a variable or value).
        conditional (str): The conditional operator to use (e.g., '==', '!=').

    Returns:
        str: The resulting skip condition as a string.

    Example:
        >>> from dataclass_wizard.conditions import Condition
        >>> cond = Condition(t_or_f=True, op='+', val=None)
        >>> finalize_skip_if(cond, 'my_var', '==')
        'my_var'
    """
    if skip_if.t_or_f:
        return operand_1 if skip_if.op == '+' else f'not {operand_1}'

    return f'{operand_1} {conditional}'


def get_skip_if_condition(skip_if, _locals, operand_2=None, condition_i=None, condition_var='_skip_if_'):
    """
    Retrieves the skip condition based on the provided `Condition` object.

    Args:
        skip_if (Condition): The condition to evaluate.
        _locals (dict[str, Any]): A dictionary of local variables for condition evaluation.
        operand_2 (str): The secondary operand (e.g., a variable or value).
        condition_i (Condition): The condition var index.
        condition_var (str): The variable name to evaluate.

    Returns:
        Any: The result of the evaluated condition or a string representation for custom values.

    Example:
        >>> from dataclass_wizard.conditions import Condition
        >>> cond = Condition(t_or_f=False, op='==', val=10)
        >>> locals_dict = {}
        >>> get_skip_if_condition(cond, locals_dict, 'other_var')
        '== other_var'
    """
    if skip_if is None:
        return False

    if skip_if.t_or_f:  # Truthy or falsy condition, no operand
        return True

    if is_builtin(skip_if.val):
        return str(skip_if)

    # Update locals (as `val` is not a builtin)
    if operand_2 is None:
        operand_2 = f'{condition_var}{condition_i}'

    _locals[operand_2] = skip_if.val
    return f'{skip_if.op} {operand_2}'
