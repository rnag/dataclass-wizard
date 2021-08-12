__all__ = ['Parser',
           'LiteralParser',
           'UnionParser',
           'OptionalParser',
           'ForwardRefParser',
           'ListParser',
           'TupleParser',
           'VariadicTupleParser',
           'NamedTupleParser',
           'MappingParser',
           'DefaultDictParser',
           'TypedDictParser']

import sys
from typing import (
    Type, Any, Callable, Tuple, Dict, Optional, FrozenSet, Union, _eval_type)

from dataclasses import dataclass, InitVar, field

from .abstractions import AbstractParser
from .errors import ParseError
from .type_def import NoneType, PyForwardRef, T, M, S, DD
from .utils.type_check import (
    get_origin, get_args, get_named_tuple_field_types,
    get_keys_for_typed_dict)


GetParserType = Callable[[Type[T], Type[T]], AbstractParser]


@dataclass
class Parser(AbstractParser):

    hook: Callable[[Any, Type[T]], T]

    def __call__(self, o: Any) -> T:
        return self.hook(o, self.base_type)


@dataclass
class LiteralParser(AbstractParser):

    base_type: Type[M]
    value_to_type: Dict[Any, Type] = field(init=False)

    def __post_init__(self, cls: Type[T]):
        self.value_to_type = {
            val: type(val) for val in get_args(self.base_type)
        }

    def __call__(self, o: Any):
        """
        Checks for Literal equivalence, as mentioned here:
          https://www.python.org/dev/peps/pep-0586/#equivalence-of-two-literals

        """
        try:
            type_does_not_match = type(o) != self.value_to_type[o]

        except KeyError:
            # No such Literal with the value of `o`
            e = ValueError('Value not in expected Literal values')
            raise ParseError(
                e, o, self.base_type,
                allowed_values=list(self.value_to_type))

        else:
            # The value of `o` is in the ones defined for the Literal, but
            # also confirm the type matches the one defined for the Literal.
            if type_does_not_match:
                expected_val = next(v for v in self.value_to_type if v == o)    # pragma: no branch
                e = TypeError(
                    'Value did not match expected type for the Literal')

                raise ParseError(
                    e, o, self.base_type,
                    have_type=type(o),
                    desired_type=self.value_to_type[o],
                    desired_value=expected_val,
                    allowed_values=list(self.value_to_type))

        return o


@dataclass
class OptionalParser(AbstractParser):

    get_parser: InitVar[GetParserType]

    def __post_init__(self, cls: Type[T],
                      get_parser: GetParserType):

        self.parser = get_parser(self.base_type, cls)

    def __contains__(self, item):
        """Check if parser is expected to handle the specified item type."""
        if type(item) is NoneType:
            return True

        return super().__contains__(item)

    def __call__(self, o: Any):
        if o is None:
            return o

        return self.parser(o)


@dataclass
class UnionParser(AbstractParser):

    base_type: Tuple[Type[T], ...]
    get_parser: InitVar[GetParserType]

    def __post_init__(self, cls: Type[T],
                      get_parser: GetParserType):

        self.parsers = tuple(get_parser(t, cls) for t in self.base_type
                             if t is not NoneType)

    def __contains__(self, item):
        """Check if parser is expected to handle the specified item type."""
        return type(item) in self.base_type

    def __call__(self, o: Any):
        if o is None:
            return o

        for parser in self.parsers:
            if o in parser:
                return parser(o)

        raise ParseError(
            TypeError('Object was not in any of Union types'),
            o, [p.base_type for p in self.parsers])


@dataclass
class ForwardRefParser(AbstractParser):

    base_type: Union[str, 'PyForwardRef']
    get_parser: InitVar[GetParserType]

    def __post_init__(self, cls: Type[T], get_parser: GetParserType):
        if isinstance(self.base_type, str):
            self.base_type = PyForwardRef(self.base_type, is_argument=False)

        # Evaluate the ForwardRef here
        base_globals = sys.modules[cls.__module__].__dict__
        self.base_type = _eval_type(self.base_type, base_globals, None)
        self.parser = get_parser(self.base_type, cls)

    def __call__(self, o: Any):
        return self.parser(o)


@dataclass
class ListParser(AbstractParser):

    base_type: Type[S]
    get_parser: InitVar[GetParserType]
    hook: Callable[[S, Type[list], AbstractParser], list]
    elem_parser: AbstractParser = field(init=False)

    def __post_init__(self, cls: Type[T], get_parser: GetParserType):

        # Get the subscripted element type
        #   ex. `List[str]` -> `str`
        try:
            elem_type, = get_args(self.base_type)
        except ValueError:
            elem_type = Any

        # Base type of the object which is instantiable
        #   ex. `List[str]` -> `list`
        self.base_type = get_origin(self.base_type)

        self.elem_parser = get_parser(elem_type, cls)

    def __call__(self, o: S) -> S:
        """
        Load an object `o` into a new object of type `base_type` (generally a
        :class:`list` or a sub-class of one)
        """
        try:
            return self.hook(o, self.base_type, self.elem_parser)
        # TODO
        except Exception:
            if not isinstance(o, self.base_type):
                e = TypeError('Incorrect type for field')
                raise ParseError(
                    e, o, self.base_type, desired_type=list)
            else:
                raise


@dataclass
class TupleParser(AbstractParser):
    """
    Parser for subscripted and un-subscripted :class:`Tuple`'s.

    See :class:`VariadicTupleParser` for the parser that handles the variadic
    form, i.e. ``Tuple[str, ...]``
    """

    # Base type of the object which is instantiable
    #   ex. `Tuple[bool, int]` -> `tuple`
    base_type: Type[S]
    get_parser: InitVar[GetParserType]
    hook: Callable[
        [Any, Type[S], Tuple[AbstractParser, ...]], S]

    # A collection with a parser for each type argument
    elem_parsers: Tuple[AbstractParser, ...] = field(init=False)
    # Total count is generally the number of type arguments to `Tuple`, but
    # can be `infinity` when a `Tuple` appears in its un-subscripted form.
    total_count: Union[int, float] = field(init=False)
    # Minimum number of *required* type arguments (this excludes types
    # which appear as `Optional` or `Union`, for example)
    required_count: int = field(init=False)

    def __post_init__(self, cls: Type[T], get_parser: GetParserType):

        # Get the subscripted values
        #   ex. `Tuple[bool, int]` -> (bool, int)
        elem_types = get_args(self.base_type)
        self.base_type = get_origin(self.base_type)
        self.elem_parsers = tuple(get_parser(t, cls) for t in elem_types)
        #   If the annotation appears in its un-subscripted form, e.g. as just
        #   a `Tuple`, we can default this to `Infinity` instead.
        self.total_count = len(self.elem_parsers) or float('inf')
        # Check for the count of parsers which don't handle `NoneType` - this
        # should exclude the parsers for `Union` types that have `None` in the
        # list of args.
        self.required_count = len(tuple(p for p in self.elem_parsers
                                  if None not in p))

    def __call__(self, o: M) -> M:
        """
        Load an object `o` into a new object of type `base_type` (generally a
        :class:`tuple` or a sub-class of one)
        """
        # Confirm that the number of arguments in `o` matches the count in the
        # typed annotation.
        if not self.required_count <= len(o) <= self.total_count:
            e = TypeError('Wrong number of elements.')
            if self.required_count != self.total_count:
                desired_count = f'{self.required_count} - {self.total_count}'
            else:
                desired_count = self.total_count

            raise ParseError(
                e, o, [p.base_type for p in self.elem_parsers],
                desired_count=desired_count,
                actual_count=len(o))

        return self.hook(o, self.base_type, self.elem_parsers)


@dataclass
class VariadicTupleParser(TupleParser):
    """
    Parser that handles the variadic form of :class:`Tuple`'s,
    i.e. ``Tuple[str, ...]``

    Per `PEP 484`_, only **one** required type is allowed before the
    ``Ellipsis``. That is, ``Tuple[int, ...]`` is valid whereas
    ``Tuple[int, str, ...]`` would be invalid. `See here`_ for more info.

    .. _PEP 484: https://www.python.org/dev/peps/pep-0484/
    .. _See here: https://github.com/python/typing/issues/180

    """

    # For `Tuple[T, ...]`, we only need a parser for `T`
    first_elem_parser: Tuple[AbstractParser] = field(init=False)

    def __post_init__(self, cls: Type[T], get_parser: GetParserType):

        # Get the subscripted values
        #   ex. `Tuple[str, ...]` -> (str, )
        elem_types = get_args(self.base_type)
        # Base type of the object which is instantiable
        #   ex. `Tuple[bool, int]` -> `tuple`
        self.base_type = get_origin(self.base_type)
        # A one-element tuple containing the parser for the first type
        # argument.
        self.first_elem_parser = get_parser(elem_types[0], cls),
        # Total count should be `Infinity` here, since the variadic form
        # accepts any number of possible arguments.
        self.total_count = float('inf')
        # Check for the count of parsers which don't handle `NoneType` - this
        # should exclude the parsers for `Union` types that have `None` in the
        # list of args.
        self.required_count = 0 if None in self.first_elem_parser[0] else 1

    def __call__(self, o: M) -> M:
        """
        Load an object `o` into a new object of type `base_type` (generally a
        :class:`tuple` or a sub-class of one)
        """
        self.elem_parsers = self.first_elem_parser * len(o)
        return super().__call__(o)


@dataclass
class NamedTupleParser(AbstractParser):
    base_type: Type[S]
    get_parser: InitVar[GetParserType]
    hook: Callable[
        [Any, Type[S], Optional[Dict[str, AbstractParser]]], S]

    field_to_parser: Optional[Dict[str, AbstractParser]] = field(init=False)

    def __post_init__(self, cls: Type[T], get_parser: GetParserType):

        try:
            # Get the field annotations for the `NamedTuple` type
            type_anns: Dict[str, Type[T]] = get_named_tuple_field_types(
                self.base_type)
        except AttributeError:
            self.field_to_parser = None
        else:
            self.field_to_parser = {
                f: get_parser(typ, cls)
                for f, typ in type_anns.items()}

    def __call__(self, o: Any):
        """
        Load a dictionary or list to a `NamedTuple` sub-class (or an
        un-annotated `namedtuple`)
        """
        return self.hook(o, self.base_type, self.field_to_parser)


@dataclass
class MappingParser(AbstractParser):
    base_type: Type[M]
    get_parser: InitVar[GetParserType]
    hook: Callable[
        [Any, Type[M], AbstractParser, AbstractParser], M]

    key_parser: AbstractParser = field(init=False)
    val_parser: AbstractParser = field(init=False)

    def __post_init__(self, cls: Type[T], get_parser: GetParserType):
        try:
            key_type, val_type = get_args(self.base_type)
        except ValueError:
            key_type = val_type = Any

        # Base type of the object which is instantiable
        #   ex. `Dict[str, Any]` -> `dict`
        self.base_type: Type[M] = get_origin(self.base_type)

        self.key_parser = get_parser(key_type, cls)
        self.val_parser = get_parser(val_type, cls)

    def __call__(self, o: M) -> M:
        return self.hook(o, self.base_type, self.key_parser, self.val_parser)


@dataclass
class DefaultDictParser(MappingParser):
    # Override the type annotations here
    base_type: Type[DD]
    hook: Callable[
        [Any, Type[DD], Callable[[], T], AbstractParser, AbstractParser], DD]
    # The default factory argument to pass to the `defaultdict` subclass
    default_factory: Callable[[], T] = field(init=False)

    def __post_init__(self, cls: Type[T], get_parser: GetParserType):
        super().__post_init__(cls, get_parser)
        self.default_factory = self.val_parser.base_type

    def __call__(self, o: M) -> M:
        return self.hook(o, self.base_type, self.default_factory,
                         self.key_parser, self.val_parser)


@dataclass
class TypedDictParser(AbstractParser):
    base_type: Type[M]
    get_parser: InitVar[GetParserType]
    hook: Callable[[Any, Type[M], Dict[str, AbstractParser],
                    FrozenSet[str], FrozenSet[str]], M]

    key_to_parser: Dict[str, AbstractParser] = field(init=False)
    required_keys: FrozenSet[str] = field(init=False)
    optional_keys: FrozenSet[str] = field(init=False)

    def __post_init__(self, cls: Type[T], get_parser: GetParserType):

        self.key_to_parser = {
            k: get_parser(v, cls)
            for k, v in self.base_type.__annotations__.items()
        }

        self.required_keys, self.optional_keys = get_keys_for_typed_dict(
            self.base_type)

    def __call__(self, o: M) -> M:
        try:
            return self.hook(o, self.base_type, self.key_to_parser,
                             self.required_keys, self.optional_keys)

        except KeyError as e:
            e = KeyError(f'Missing required key: {e.args[0]}')
            raise ParseError(e, o, self.base_type)

        except Exception:
            if not isinstance(o, dict):
                e = TypeError('Incorrect type for object')
                raise ParseError(
                    e, o, self.base_type, desired_type=self.base_type)
            else:
                raise
