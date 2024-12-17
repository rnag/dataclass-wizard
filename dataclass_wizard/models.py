import json
from dataclasses import MISSING, Field
from datetime import date, datetime, time
from typing import Generic, Mapping, NewType, Any, TypedDict

from .constants import PY310_OR_ABOVE
from .decorators import cached_property
from .type_def import T, DT, PyNotRequired
# noinspection PyProtectedMember
from .utils.dataclass_compat import _create_fn
from .utils.object_path import split_object_path
from .utils.type_conv import as_datetime, as_time, as_date


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
# A date, time, datetime sub type, or None.
# DT_OR_NONE = Optional[DT]


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


# noinspection PyShadowingBuiltins
def json_key(*keys: str, all=False, dump=True):
    return JSON(*keys, all=all, dump=dump)


# noinspection PyPep8Naming,PyShadowingBuiltins
def KeyPath(keys, all=True, dump=True):
    if isinstance(keys, str):
        keys = split_object_path(keys)

    return JSON(*keys, all=all, dump=dump, path=True)


# noinspection PyShadowingBuiltins
def json_field(keys, *,
               all=False, dump=True,
               default=MISSING,
               default_factory=MISSING,
               init=True, repr=True,
               hash=None, compare=True, metadata=None):

    if default is not MISSING and default_factory is not MISSING:
        raise ValueError('cannot specify both default and default_factory')

    return JSONField(keys, all, dump, default, default_factory, init, repr,
                     hash, compare, metadata)


env_field = json_field


class JSON:

    __slots__ = ('keys',
                 'all',
                 'dump',
                 'path')

    # noinspection PyShadowingBuiltins
    def __init__(self, *keys, all=False, dump=True, path=False):

        self.keys = (split_object_path(keys)
                     if path and isinstance(keys, str) else keys)
        self.all = all
        self.dump = dump
        self.path = path


class JSONField(Field):

    __slots__ = ('json', )

    # In Python 3.10, dataclasses adds a new parameter to the :class:`Field`
    # constructor: `kw_only`
    #
    # Ref: https://docs.python.org/3.10/library/dataclasses.html#dataclasses.dataclass
    if PY310_OR_ABOVE:  # pragma: no cover
        # noinspection PyShadowingBuiltins
        def __init__(self, keys, all: bool, dump: bool,
                     default, default_factory, init, repr, hash, compare,
                     metadata, path: bool = False):

            super().__init__(default, default_factory, init, repr, hash,
                             compare, metadata, False)

            if isinstance(keys, str):
                keys = split_object_path(keys) if path else (keys,)
            elif keys is ...:
                keys = ()

            self.json = JSON(*keys, all=all, dump=dump, path=path)

    else:  # pragma: no cover
        # noinspection PyArgumentList,PyShadowingBuiltins
        def __init__(self, keys, all: bool, dump: bool,
                     default, default_factory, init, repr, hash, compare,
                     metadata, path: bool = False):

            super().__init__(default, default_factory, init, repr, hash,
                             compare, metadata)

            if isinstance(keys, str):
                keys = split_object_path(keys) if path else (keys,)
            elif keys is ...:
                keys = ()

            self.json = JSON(*keys, all=all, dump=dump, path=path)


# noinspection PyPep8Naming
def Pattern(pattern):
    return PatternedDT(pattern)


class _PatternBase:
    __slots__ = ()

    def __class_getitem__(cls, pattern):
        return PatternedDT(pattern, cls.__base__)

    __getitem__ = __class_getitem__


class DatePattern(date, _PatternBase):
    __slots__ = ()


class TimePattern(time, _PatternBase):
    __slots__ = ()


class DateTimePattern(datetime, _PatternBase):
    __slots__ = ()


class PatternedDT(Generic[DT]):

    # `cls` is the date/time/datetime type or subclass.
    # `pattern` is the format string to pass in to `datetime.strptime`.
    __slots__ = ('cls',
                 'pattern')

    def __init__(self, pattern, cls = None):
        self.cls = cls
        self.pattern = pattern

    def get_transform_func(self):
        cls = self.cls

        # Parse with `fromisoformat` first, because its *much* faster than
        # `datetime.strptime` - see linked article above for more details.
        body_lines = [
            'dt = default_load_func(date_string, cls, raise_=False)',
            'if dt is not None:',
            '  return dt',
            'dt = datetime.strptime(date_string, pattern)',
        ]

        locals_ns = {'datetime': datetime,
                     'pattern': self.pattern,
                     'cls': cls}

        if cls is datetime:
            default_load_func = as_datetime
            body_lines.append('return dt')
        elif cls is date:
            default_load_func = as_date
            body_lines.append('return dt.date()')
        elif cls is time:
            default_load_func = as_time
            # temp fix for Python 3.11+, since `time.fromisoformat` is updated
            # to support more formats, such as "-" and "+" in strings.
            if '-' in self.pattern or '+' in self.pattern:
                body_lines = ['try:',
                              '  return datetime.strptime(date_string, pattern).time()',
                              'except (ValueError, TypeError):',
                              '  dt = default_load_func(date_string, cls, raise_=False)',
                              '  if dt is not None:',
                              '    return dt']
            else:
                body_lines.append('return dt.time()')
        elif issubclass(cls, datetime):
            default_load_func = as_datetime
            locals_ns['datetime'] = cls
            body_lines.append('return dt')
        elif issubclass(cls, date):
            default_load_func = as_date
            body_lines.append('return cls(dt.year, dt.month, dt.day)')
        elif issubclass(cls, time):
            default_load_func = as_time
            # temp fix for Python 3.11+, since `time.fromisoformat` is updated
            # to support more formats, such as "-" and "+" in strings.
            if '-' in self.pattern or '+' in self.pattern:
                body_lines = ['try:',
                              '  dt = datetime.strptime(date_string, pattern).time()',
                              'except (ValueError, TypeError):',
                              '  dt = default_load_func(date_string, cls, raise_=False)',
                              '  if dt is not None:',
                              '    return dt']

            body_lines.append('return cls(dt.hour, dt.minute, dt.second, '
                              'dt.microsecond, fold=dt.fold)')
        else:
            raise TypeError(f'Annotation for `Pattern` is of invalid type '
                            f'({cls}). Expected a type or subtype of: '
                            f'{DT.__constraints__}')

        locals_ns['default_load_func'] = default_load_func

        return _create_fn('pattern_to_dt',
                          ('date_string', ),
                          body_lines,
                          locals=locals_ns,
                          return_type=DT)

    def __repr__(self):
        repr_val = [f'{k}={getattr(self, k)!r}' for k in self.__slots__]
        return f'{self.__class__.__name__}({", ".join(repr_val)})'


class Container(list[T]):

    __slots__ = ('__dict__',
                 '__orig_class__')

    @cached_property
    def __model__(self):

        try:
            # noinspection PyUnresolvedReferences
            return self.__orig_class__.__args__[0]
        except AttributeError:
            cls_name = self.__class__.__qualname__
            msg = (f'A {cls_name} object needs to be instantiated with '
                   f'a generic type T.\n\n'
                   'Example:\n'
                   f'  my_list = {cls_name}[T](...)')

            raise TypeError(msg) from None

    def __str__(self):

        import pprint
        return pprint.pformat(self)

    def prettify(self, encoder = json.dumps,
                 ensure_ascii=False,
                 **encoder_kwargs):

        return self.to_json(
            indent=2,
            encoder=encoder,
            ensure_ascii=ensure_ascii,
            **encoder_kwargs
        )

    def to_json(self, encoder=json.dumps,
                **encoder_kwargs):

        from .dumpers import asdict

        cls = self.__model__
        list_of_dict = [asdict(o, cls=cls) for o in self]

        return encoder(list_of_dict, **encoder_kwargs)

    def to_json_file(self, file, mode = 'w',
                     encoder=json.dump,
                     **encoder_kwargs):

        from .dumpers import asdict

        cls = self.__model__
        list_of_dict = [asdict(o, cls=cls) for o in self]

        with open(file, mode) as out_file:
            encoder(list_of_dict, out_file, **encoder_kwargs)


# noinspection PyShadowingBuiltins
def path_field(keys, *,
               all=True, dump=True,
               default=MISSING,
               default_factory=MISSING,
               init=True, repr=True,
               hash=None, compare=True, metadata=None):

    if default is not MISSING and default_factory is not MISSING:
        raise ValueError('cannot specify both default and default_factory')

    return JSONField(keys, all, dump, default, default_factory, init, repr,
                    hash, compare, metadata, True)


# In Python 3.10, dataclasses adds a new parameter to the :class:`Field`
# constructor: `kw_only`
#
# Ref: https://docs.python.org/3.10/library/dataclasses.html#dataclasses.dataclass
if PY310_OR_ABOVE:  # pragma: no cover
    def skip_if_field(condition, *, default=MISSING, default_factory=MISSING, init=True, repr=True,
                      hash=None, compare=True, metadata=None, kw_only=MISSING):

        if default is not MISSING and default_factory is not MISSING:
            raise ValueError('cannot specify both default and default_factory')

        if metadata is None:
            metadata = {}

        metadata['__skip_if__'] = condition

        return Field(default, default_factory, init, repr, hash,
                     compare, metadata, kw_only)
else:  # pragma: no cover
    def skip_if_field(condition, *, default=MISSING, default_factory=MISSING, init=True, repr=True,
                      hash=None, compare=True, metadata=None):

        if default is not MISSING and default_factory is not MISSING:
            raise ValueError('cannot specify both default and default_factory')

        if metadata is None:
            metadata = {}

        metadata['__skip_if__'] = condition

        # noinspection PyArgumentList
        return Field(default, default_factory, init, repr, hash,
                     compare, metadata)


class Condition:

    __slots__ = (
        'op',
        'val',
        't_or_f',
        '_wrapped',
    )

    def __init__(self, operator, value):
        self.op = operator
        self.val = value
        self.t_or_f = operator in {'+', '!'}

    def __str__(self):
        return f"{self.op} {self.val!r}"

    def evaluate(self, other) -> bool:  # pragma: no cover
        # Optionally support runtime evaluation of the condition
        operators = {
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
            "is": lambda a, b: a is b,
            "is not": lambda a, b: a is not b,
            "+": lambda a, _: True if a else False,
            "!": lambda a, _: not a,
        }
        return operators[self.op](other, self.val)


# Aliases for conditions

# noinspection PyPep8Naming
def EQ(value): return Condition("==", value)
# noinspection PyPep8Naming
def NE(value): return Condition("!=", value)
# noinspection PyPep8Naming
def LT(value): return Condition("<", value)
# noinspection PyPep8Naming
def LE(value): return Condition("<=", value)
# noinspection PyPep8Naming
def GT(value): return Condition(">", value)
# noinspection PyPep8Naming
def GE(value): return Condition(">=", value)
# noinspection PyPep8Naming
def IS(value): return Condition("is", value)
# noinspection PyPep8Naming
def IS_NOT(value): return Condition("is not", value)
# noinspection PyPep8Naming
def IS_TRUTHY(): return Condition("+", None)
# noinspection PyPep8Naming
def IS_FALSY(): return Condition("!", None)


# noinspection PyPep8Naming
def SkipIf(condition):
    """
    Mark a condition to be used as a skip directive during serialization.
    """
    condition._wrapped = True  # Set a marker attribute
    return condition


# Convenience alias, to skip serializing field if value is None
SkipIfNone = SkipIf(IS(None))


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
        >>> cond = Condition(t_or_f=True, op='+', val=None)
        >>> finalize_skip_if(cond, 'my_var', '==')
        'my_var'
    """
    if skip_if.t_or_f:
        return operand_1 if skip_if.op == '+' else f'not {operand_1}'

    return f'{operand_1} {conditional}'


def get_skip_if_condition(skip_if, _locals, operand_2):
    """
    Retrieves the skip condition based on the provided `Condition` object.

    Args:
        skip_if (Condition): The condition to evaluate.
        _locals (dict[str, Any]): A dictionary of local variables for condition evaluation.
        operand_2 (str): The secondary operand (e.g., a variable or value).

    Returns:
        Any: The result of the evaluated condition or a string representation for custom values.

    Example:
        >>> cond = Condition(t_or_f=False, op='==', val=10)
        >>> locals_dict = {}
        >>> get_skip_if_condition(cond, locals_dict, 'other_var')
        '== other_var'
    """
    # TODO: To avoid circular import
    from .class_helper import is_builtin

    if skip_if is None:
        return False

    if skip_if.t_or_f:  # Truthy or falsy condition, no operand
        return True

    if is_builtin(skip_if.val):
        return str(skip_if)

    # Update locals (as `val` is not a builtin)
    _locals[operand_2] = skip_if.val
    return f'{skip_if.op} {operand_2}'
