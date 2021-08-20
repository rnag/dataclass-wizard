from collections import defaultdict, deque
from dataclasses import is_dataclass
from datetime import datetime, time, date
from decimal import Decimal
from enum import Enum
from typing import (
    Any, Type, Dict, List, Tuple, Iterable, Sequence, Optional, Union,
    NamedTupleMeta, SupportsFloat, SupportsInt, AnyStr, Text
)
from uuid import UUID

from .abstractions import AbstractLoader, AbstractParser, FieldToParser
from .bases import BaseLoadHook
from .class_helper import (
    get_class_name, create_new_class,
    dataclass_to_loader, set_class_loader,
    dataclass_field_to_load_parser, json_field_to_dataclass_field,
)
from .constants import _LOAD_HOOKS
from .errors import ParseError
from .log import LOG
from .parsers import *
from .type_def import (
    ExplicitNull, PyForwardRef, FrozenKeys, DefFactory, NoneType,
    M, N, T, E, U, DD, LSQ, NT
)
from .utils.string_conv import to_snake_case
from .utils.typing_compat import (
    is_literal, is_typed_dict, get_origin, get_args, is_annotated
)
from .utils.type_conv import (
    as_bool, as_str, as_datetime, as_date, as_time, as_int
)


class LoadMixin(AbstractLoader, BaseLoadHook):
    """
    This Mixin class derives its name from the eponymous `json.loads`
    function. Essentially it contains helper methods to convert JSON strings
    (or a Python dictionary object) to a `dataclass` which can often contain
    complex types such as lists, dicts, or even other dataclasses nested
    within it.

    Refer to the :class:`AbstractLoader` class for documentation on any of the
    implemented methods.

    """
    __slots__ = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        setup_default_loader(cls)

    @staticmethod
    def transform_json_field(string: str) -> str:

        return to_snake_case(string)

    @staticmethod
    def default_load_to(o: T, *_) -> T:

        return o

    @staticmethod
    def load_after_type_check(o: Any, base_type: Type[T]) -> T:

        if isinstance(o, base_type):
            return o

        e = ValueError(f'data type is not a {base_type!s}')
        raise ParseError(e, o, base_type)

    @staticmethod
    def load_to_str(o: Union[Text, N, None], base_type: Type[str]) -> str:

        return as_str(o, base_type)

    @staticmethod
    def load_to_int(o: Union[SupportsInt, str], base_type: Type[N]) -> N:

        return as_int(o, base_type)

    @staticmethod
    def load_to_float(o: Union[SupportsFloat, str], base_type: Type[N]) -> N:

        return base_type(o)

    @staticmethod
    def load_to_bool(o: Union[str, bool, N], base_type: Type[bool]) -> bool:

        return as_bool(o)

    @staticmethod
    def load_to_enum(o: Union[AnyStr, N], base_type: Type[E]) -> E:

        return base_type(o)

    @staticmethod
    def load_to_uuid(o: Union[AnyStr, U], base_type: Type[U]) -> U:

        return base_type(o)

    @staticmethod
    def load_to_iterable(
            o: Iterable, base_type: Type[LSQ],
            elem_parser: AbstractParser) -> LSQ:

        return base_type(elem_parser(elem) for elem in o)

    @classmethod
    def load_to_tuple(
            cls, o: Union[List, Tuple], base_type: Type[Tuple],
            elem_parsers: Sequence[AbstractParser]) -> Tuple:

        if elem_parsers:
            return base_type(parser(e) for parser, e in zip(elem_parsers, o))
        else:
            any_parser: AbstractParser = cls.get_parser_for_annotation(Any)
            return base_type(any_parser(e) for e in o)

    @classmethod
    def load_to_named_tuple(
            cls, o: Union[Dict, List, Tuple], base_type: Type[NT],
            field_to_parser: Optional[FieldToParser]) -> NT:

        if field_to_parser is not None:
            # Annotated as a sub-type of `typing.NamedTuple`
            if isinstance(o, dict):
                # Convert the values of all fields in the NamedTuple, using
                # their type annotations. The keys in a dictionary object
                # (assuming it was loaded from JSON) are required to be
                # strings, so we don't need to convert them.
                return base_type(**{k: field_to_parser[k](v)
                                    for k, v in o.items()})
            # We're passed in a list or a tuple.
            field_parsers = list(field_to_parser.values())
            return base_type(*[
                parser(elem) for parser, elem in zip(field_parsers, o)])

        else:
            # Annotated as just a regular `collections.namedtuple`
            if isinstance(o, dict):
                dict_parser = cls.get_parser_for_annotation(dict)
                return base_type(**dict_parser(o))
            # We're passed in a list or a tuple.
            list_parser = cls.get_parser_for_annotation(list)
            return base_type(*list_parser(o))

    @staticmethod
    def load_to_dict(
            o: Dict, base_type: Type[M],
            key_parser: AbstractParser,
            val_parser: AbstractParser) -> M:

        return base_type(
            (key_parser(k), val_parser(v))
            for k, v in o.items()
        )

    @staticmethod
    def load_to_defaultdict(
            o: Dict, base_type: Type[DD],
            default_factory: DefFactory,
            key_parser: AbstractParser,
            val_parser: AbstractParser) -> DD:

        return base_type(
            default_factory,
            {key_parser(k): val_parser(v)
             for k, v in o.items()}
        )

    @staticmethod
    def load_to_typed_dict(
            o: Dict, base_type: Type[M],
            key_to_parser: FieldToParser,
            required_keys: FrozenKeys,
            optional_keys: FrozenKeys) -> M:

        kwargs = {}

        # Set required keys for the `TypedDict`
        for k in required_keys:
            kwargs[k] = key_to_parser[k](o[k])

        # Set optional keys for the `TypedDict` (if they exist)
        for k in optional_keys:
            if k in o:
                kwargs[k] = key_to_parser[k](o[k])

        return base_type(**kwargs)

    @staticmethod
    def load_to_decimal(o: N, base_type: Type[Decimal]) -> Decimal:

        return base_type(str(o))

    @staticmethod
    def load_to_datetime(
            o: Union[str, N], base_type: Type[datetime]) -> datetime:

        return as_datetime(o, base_type)

    @staticmethod
    def load_to_time(o: str, base_type: Type[time]) -> time:

        return as_time(o, base_type)

    @staticmethod
    def load_to_date(o: Union[str, N], base_type: Type[date]) -> date:

        return as_date(o, base_type)

    @classmethod
    def get_parser_for_annotation(cls, ann_type: Type[T],
                                  base_cls: Type[T] = None) -> AbstractParser:
        """Returns the Parser (dispatcher) for a given annotation type."""
        hooks = cls.__LOAD_HOOKS__
        load_hook = hooks.get(ann_type)
        base_type = ann_type

        # TODO: I'll need to refactor the code below to remove the nested `if`
        #   statements, when time allows. Right now the branching logic is
        #   unseemly and there's really no need for that, as any such
        #   performance gains (if they do exist) are minimal at best.

        if load_hook is None:
            # Need to check this first, because the `Literal` type in Python
            # 3.6 behaves a bit differently (doesn't have an `__origin__`
            # attribute for example)
            if is_literal(ann_type):
                return LiteralParser(cls, ann_type)

            if is_annotated(ann_type):
                # Given `Annotated[T, MaxValue(10), ...]`, we only need `T`
                ann_type = get_args(ann_type)[0]
                return cls.get_parser_for_annotation(ann_type, base_cls)

            # This property will be available for most generic types in the
            # `typing` library.
            try:
                base_type = get_origin(ann_type, raise_=True)

            # If we can't access this property, it's likely a non-generic
            # class or a non-generic sub-type.
            except AttributeError:

                if isinstance(base_type, type):

                    if is_dataclass(base_type):
                        load_hook = _load_to_dataclass

                    elif issubclass(base_type, Enum):
                        load_hook = hooks.get(Enum)

                    elif issubclass(base_type, UUID):
                        load_hook = hooks.get(UUID)

                    elif issubclass(base_type, tuple) \
                            and hasattr(base_type, '_fields'):
                        load_hook = hooks.get(NamedTupleMeta)
                        return NamedTupleParser(
                            base_cls, base_type, load_hook,
                            cls.get_parser_for_annotation
                        )

                    elif is_typed_dict(base_type):
                        load_hook = cls.load_to_typed_dict
                        return TypedDictParser(
                            base_cls, base_type, load_hook,
                            cls.get_parser_for_annotation
                        )

                elif base_type is Any:
                    load_hook = cls.default_load_to

                elif isinstance(base_type, (str, PyForwardRef)):
                    return ForwardRefParser(
                        base_cls, base_type, cls.get_parser_for_annotation
                    )

                elif base_type is Ellipsis:
                    load_hook = cls.default_load_to

                # If we can't find the underlying type of the object, we
                # should emit a warning for awareness.
                else:
                    load_hook = cls.default_load_to
                    LOG.warning('Using default loader, type=%r', ann_type)

            # Else, it's annotated with a generic type like Union or List -
            # basically anything that's subscriptable.
            else:
                if base_type is Union:
                    # Get the subscripted values
                    #   ex. `Union[int, str]` -> (int, str)
                    base_types = get_args(ann_type)

                    if not base_types:
                        # Annotated as just `Union` (no subscripted types)
                        load_hook = cls.default_load_to

                    elif NoneType in base_types and len(base_types) == 2:
                        # Special case for Optional[x], which is actually Union[x, None]
                        return OptionalParser(
                            base_cls, base_types[0],
                            cls.get_parser_for_annotation
                        )

                    else:
                        return UnionParser(
                            base_cls, base_types,
                            cls.get_parser_for_annotation
                        )

                elif issubclass(base_type, defaultdict):
                    load_hook = cls.load_to_defaultdict
                    return DefaultDictParser(
                        base_cls, ann_type, load_hook,
                        cls.get_parser_for_annotation
                    )

                elif issubclass(base_type, dict):
                    load_hook = cls.load_to_dict
                    return MappingParser(
                        base_cls, ann_type, load_hook,
                        cls.get_parser_for_annotation
                    )

                elif issubclass(base_type, LSQ.__constraints__):
                    load_hook = cls.load_to_iterable
                    return IterableParser(
                        base_cls, ann_type, load_hook,
                        cls.get_parser_for_annotation
                    )

                elif issubclass(base_type, tuple):
                    load_hook = cls.load_to_tuple
                    # Check if the `Tuple` appears in the variadic form
                    #   i.e. Tuple[str, ...]
                    args = get_args(ann_type)
                    is_variadic = args and args[-1] is ...
                    # Determine the parser for the annotation
                    parser: Type[AbstractParser] = TupleParser
                    if is_variadic:
                        parser = VariadicTupleParser

                    return parser(
                        base_cls, ann_type, load_hook,
                        cls.get_parser_for_annotation
                    )

                else:
                    load_hook = hooks.get(base_type)

        # TODO i'll need to refactor this to remove duplicate lines above -
        # maybe merge them together.
        elif issubclass(base_type, dict):
            load_hook = cls.load_to_dict
            return MappingParser(
                base_cls, ann_type, load_hook, cls.get_parser_for_annotation)

        elif issubclass(base_type, LSQ.__constraints__):
            load_hook = cls.load_to_iterable
            return IterableParser(
                base_cls, ann_type, load_hook, cls.get_parser_for_annotation)

        elif issubclass(base_type, tuple):
            load_hook = cls.load_to_tuple
            return TupleParser(
                base_cls, ann_type, load_hook, cls.get_parser_for_annotation)

        return Parser(base_cls, base_type, load_hook)


def setup_default_loader(cls=LoadMixin):
    """
    Setup the default type hooks to use when converting `str` (json) or a
    Python `dict` object to a `dataclass` instance.

    Note: `cls` must be :class:`LoadMixIn` or a sub-class of it.
    """
    # Simple types
    cls.register_load_hook(str, cls.load_to_str)
    cls.register_load_hook(int, cls.load_to_int)
    cls.register_load_hook(float, cls.load_to_float)
    cls.register_load_hook(bool, cls.load_to_bool)
    cls.register_load_hook(bytes, cls.load_after_type_check)
    cls.register_load_hook(bytearray, cls.load_after_type_check)
    cls.register_load_hook(NoneType, cls.default_load_to)
    # Complex types
    cls.register_load_hook(Enum, cls.load_to_enum)
    cls.register_load_hook(UUID, cls.load_to_uuid)
    cls.register_load_hook(set, cls.load_to_iterable)
    cls.register_load_hook(frozenset, cls.load_to_iterable)
    cls.register_load_hook(deque, cls.load_to_iterable)
    cls.register_load_hook(list, cls.load_to_iterable)
    cls.register_load_hook(tuple, cls.load_to_tuple)
    cls.register_load_hook(NamedTupleMeta, cls.load_to_named_tuple)
    cls.register_load_hook(defaultdict, cls.load_to_defaultdict)
    cls.register_load_hook(dict, cls.load_to_dict)
    cls.register_load_hook(Decimal, cls.load_to_decimal)
    # Dates and times
    cls.register_load_hook(datetime, cls.load_to_datetime)
    cls.register_load_hook(time, cls.load_to_time)
    cls.register_load_hook(date, cls.load_to_date)


def get_loader(class_or_instance=None, create=False) -> Type[LoadMixin]:
    """
    Get the loader for the class, using the following logic:

        * Return the class if it's already a sub-class of :class:`LoadMixin`
        * If `create` is enabled, a new sub-class of :class:`LoadMixin` for
          the class will be generated and cached on the initial run.
        * Otherwise, we will return the base loader, :class:`LoadMixin`, which
          can potentially be shared by more than one dataclass.

    """
    try:
        return dataclass_to_loader(class_or_instance)

    except KeyError:

        if hasattr(class_or_instance, _LOAD_HOOKS):
            return set_class_loader(class_or_instance, class_or_instance)

        elif create:
            cls_loader = create_new_class(class_or_instance, (LoadMixin, ))
            return set_class_loader(class_or_instance, cls_loader)

        return set_class_loader(class_or_instance, LoadMixin)


# TODO move to :class:`LoadMixin` if possible
def _load_to_dataclass(d: Dict[str, Any], cls: Type[T]) -> T:
    """
    Converts a Python dictionary object to a dataclass instance.

    Iterates over each dataclass field recursively; lists, dicts, and nested
    dataclasses will likewise be initialized as expected.

    """
    # Gets the loader for the class, or the default loader otherwise.
    cls_loader = get_loader(cls)
    # Need to create a separate dictionary to copy over the constructor args,
    # as we don't want to mutate the original dictionary object.
    cls_kwargs = {}
    # This contains a mapping of the original field name to the parser for its
    # annotated type; the item lookup will be case-insensitive.
    field_to_parser = dataclass_field_to_load_parser(cls_loader, cls)
    # A cached mapping of keys in a JSON or dictionary object to the
    # resolved dataclass field name; useful so we don't need to do a case
    # transformation (via regex) each time.
    json_to_dataclass_field = json_field_to_dataclass_field(cls)

    # Loop over the dictionary object
    for json_field, json_val in d.items():

        # Get the resolved dataclass field name
        field_name = json_to_dataclass_field.get(json_field)

        if not field_name:
            # On an initial run, or no resolved field name

            if field_name is ExplicitNull:
                continue

            # Transform JSON field name (typically camel-cased) to the
            # snake-cased variant which is convention in Python.
            underscored_field = cls_loader.transform_json_field(json_field)

            try:
                # Do a case-insensitive lookup of the dataclass field, and
                # cache the mapping so we have it for next time
                field_name = field_to_parser.get_key(underscored_field)
                json_to_dataclass_field[json_field] = field_name

            except KeyError:
                # Else, we see an unknown field in the dictionary object
                json_to_dataclass_field[json_field] = ExplicitNull
                LOG.warning(
                    'JSON field %r missing from dataclass schema, '
                    'class=%r, parsed field=%r',
                    json_field, get_class_name(cls), underscored_field)
                continue

        try:
            # Note: pass the original cased field to the class constructor;
            # don't use the lowercase result from `transform_json_field`
            cls_kwargs[field_name] = field_to_parser[field_name](json_val)

        except ParseError as e:
            # We run into a parsing error while loading the field value; Add
            # additional info on the Exception object before re-raising it
            #
            # First confirm these values are not already set by an inner
            # dataclass. If so, it likely makes it easier to debug the cause.
            if not e.class_name:
                e.class_name = cls.__qualname__
                e.field_name = field_name
            raise

    obj = cls(**cls_kwargs)
    return obj


# noinspection SpellCheckingInspection
def fromdict(cls: Type[T], d: Dict[str, Any]) -> T:
    """
    Converts a Python dictionary object to a dataclass instance.

    Iterates over each dataclass field recursively; lists, dicts, and nested
    dataclasses will likewise be initialized as expected.

    """
    return _load_to_dataclass(d, cls)
