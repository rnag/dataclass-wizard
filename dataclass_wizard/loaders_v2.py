import types
from base64 import decodebytes
from collections import defaultdict, deque, namedtuple
import collections.abc as abc

from dataclasses import is_dataclass, MISSING
from datetime import datetime, time, date, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
# noinspection PyUnresolvedReferences,PyProtectedMember
from typing import (
    Any, Type, Dict, List, Tuple, Iterable, Sequence, Union,
    NamedTupleMeta,
    SupportsFloat, AnyStr, Text, Callable, Optional
)

from uuid import UUID

from .abstractions import AbstractParser, AbstractLoaderGenerator
from .bases import BaseLoadHook, AbstractMeta, META
from .class_helper import (
    create_new_class,
    dataclass_to_loader, set_class_loader,
    dataclass_field_to_load_parser, json_field_to_dataclass_field,
    CLASS_TO_LOAD_FUNC, dataclass_fields, get_meta, is_subclass_safe, dataclass_field_to_json_path,
    dataclass_init_fields, dataclass_field_to_default, is_builtin,
)
from .constants import _LOAD_HOOKS, SINGLE_ARG_ALIAS, IDENTITY, CATCH_ALL
from .decorators import _alias, _single_arg_alias, resolve_alias_func, _identity
from .errors import (ParseError, MissingFields, UnknownJSONKey,
                     MissingData, RecursiveClassError)
from .log import LOG
from .models import Extras, PatternedDT, TypeInfo
from .parsers import *
from .type_def import (
    ExplicitNull, FrozenKeys, DefFactory, NoneType, JSONObject,
    PyRequired, PyNotRequired,
    M, N, T, E, U, DD, LSQ, NT
)
from .utils.function_builder import FunctionBuilder
# noinspection PyProtectedMember
from .utils.dataclass_compat import _set_new_attribute
from .utils.object_path import safe_get
from .utils.string_conv import to_snake_case
from .utils.type_conv import (
    as_bool, as_str, as_datetime, as_date, as_time, as_int, as_timedelta, _TRUTHY_VALUES
)
from .utils.typing_compat import (
    is_literal, is_typed_dict, get_origin, get_args, is_annotated,
    eval_forward_ref_if_needed, get_origin_v2, is_union
)


# Atomic immutable types which don't require any recursive handling and for which deepcopy
# returns the same object. We can provide a fast-path for these types in asdict and astuple.
_SIMPLE_TYPES = (
    # Common JSON Serializable types
    types.NoneType,
    bool,
    int,
    float,
    str,
    # Other common types
    complex,
    bytes,
)


class LoadMixin(AbstractLoaderGenerator, BaseLoadHook):
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
    @_alias(to_snake_case)
    def transform_json_field(string: str) -> str:
        # alias: to_snake_case
        ...

    @staticmethod
    @_identity
    def default_load_to(o: T, _: Any) -> T:
        # identity: o
        ...

    @staticmethod
    def load_after_type_check(o: Any, base_type: Type[T]) -> T:

        if isinstance(o, base_type):
            return o

        e = ValueError(f'data type is not a {base_type!s}')
        raise ParseError(e, o, base_type)

    @staticmethod
    def load_to_str(tp: TypeInfo, extras: Extras) -> str:
        # TODO skip None check if in Optional
        return f"'' if {(v := tp.v())} is None else {tp.name}({v})"

    @staticmethod
    def load_to_int(tp: TypeInfo, extras: Extras) -> str:
        # TODO
        extras['locals'].setdefault('as_int', as_int)

        # TODO
        return f"as_int({tp.v()}, {tp.name})"

    @staticmethod
    def load_to_float(tp: TypeInfo, extras: Extras) -> str:
        # alias: base_type(o)
        return f'{tp.name}({tp.v()})'

    @staticmethod
    def load_to_bool(tp: TypeInfo, extras: Extras) -> str:
        extras['locals'].setdefault('as_bool', as_bool)
        return f"as_bool({tp.v()})"
        # Uncomment for efficiency!
        # extras['locals']['_T'] = _TRUTHY_VALUES
        # return f'{tp.v()} if (t := type({tp.v()})) is bool else ({tp.v()}.lower() in _T if t is str else {tp.v()} == 1)'

    @staticmethod
    def load_to_bytes(tp: TypeInfo, extras: Extras) -> str:
        extras['locals'].setdefault('decodebytes', decodebytes)
        return f'decodebytes({tp.v()}.encode())'

    @staticmethod
    def load_to_bytearray(tp: TypeInfo, extras: Extras) -> str:
        extras['locals'].setdefault('decodebytes', decodebytes)
        return f'{tp.name}(decodebytes({tp.v()}.encode()))'

    @staticmethod
    def load_to_none(tp: TypeInfo, extras: Extras) -> str:
        return 'None'

    @staticmethod
    @_single_arg_alias('base_type')
    def load_to_enum(o: Union[AnyStr, N], base_type: Type[E]) -> E:
        # alias: base_type(o)
        ...

    @staticmethod
    @_single_arg_alias('base_type')
    def load_to_uuid(o: Union[AnyStr, U], base_type: Type[U]) -> U:
        # alias: base_type(o)
        ...

    @classmethod
    def load_to_iterable(cls, tp: TypeInfo, extras: Extras) -> str:
        v, v_next, i_next = tp.v_and_next()
        gorg = tp.origin

        try:
            elem_type = tp.args[0]
        except:
            elem_type = tp.args

        # print('INNER:', extras, gorg)

        tp_next = TypeInfo(elem_type, i=i_next, index=tp.index)
        string = cls.get_string_for_annotation(tp_next, None, extras)

        # string = cls.get_string_for_annotation(elem_type, nxt, None, extras)

        # TODO
        if issubclass(gorg, (set, frozenset)):
            start_char = '{'
            end_char = '}'
        else:
            start_char = '['
            end_char = ']'

        result = f'{start_char}{string} for {v_next} in {v}{end_char}'

        # TODO
        should_wrap = gorg not in {list, set, dict, tuple}
        # if gorg.__module__ not in {'builtins', 'collections'}:

        return f'{tp.name}({result})' if should_wrap else result

    @classmethod
    def load_to_tuple(cls, tp: TypeInfo, extras: Extras) -> str:
        args = tp.args

        # Determine the code string for the annotation

        # Check if the `Tuple` appears in the variadic form
        #   i.e. Tuple[str, ...]
        is_variadic = args and args[-1] is ...

        if is_variadic:
            #     Parser that handles the variadic form of :class:`Tuple`'s,
            #     i.e. ``Tuple[str, ...]``
            #
            #     Per `PEP 484`_, only **one** required type is allowed before the
            #     ``Ellipsis``. That is, ``Tuple[int, ...]`` is valid whereas
            #     ``Tuple[int, str, ...]`` would be invalid. `See here`_ for more info.
            #
            #     .. _PEP 484: https://www.python.org/dev/peps/pep-0484/
            #     .. _See here: https://github.com/python/typing/issues/180
            v, v_next, i_next = tp.v_and_next()

            tp_next = TypeInfo(args[0], i=i_next, index=tp.index)
            string = cls.get_string_for_annotation(tp_next, None, extras)

            # A one-element tuple containing the parser for the first type
            # argument.
            # Given `Tuple[T, ...]`, we only need a parser for `T`
            # self.first_elem_parser = get_parser(elem_types[0], cls, extras),
            # Total count should be `Infinity` here, since the variadic form
            # accepts any number of possible arguments.
            # self.total_count: N = float('inf')
            # self.required_count = 0

            result = f'[{string} for {v_next} in {v}]'
            # Wrap because we need to create a tuple from list comprehension
            should_wrap = True

        else:
            string = ', '.join([
                cls.get_string_for_annotation(
                    TypeInfo(arg, i=tp.i, index=k),
                    None, extras)
                for k, arg in enumerate(args)])

            result = f'({string}, )'
            should_wrap = False

        # print('INNER:', extras, tp.origin)

        # TODO
        if should_wrap or tp.origin not in {list, set, dict, tuple}:
            tn = tp.name
            if tp.origin.__module__ not in {'builtins', 'collections'}:
                tn = f'tp{tp.i}'
                # TODO remove
                print(f'Adding {tn}={tp.name}')
                locals = extras['locals']
                locals[tn] = tp.origin

            return f'{tn}({result})'

        return result

    @staticmethod
    def _old_load_to_tuple(
            o: Union[List, Tuple], base_type: Type[Tuple],
            elem_parsers: Sequence[AbstractParser]) -> Tuple:

        try:
            zipped = zip(elem_parsers, o)
        except TypeError:
            return base_type([e for e in o])
        else:
            return base_type([parser(e) for parser, e in zipped])

    @staticmethod
    def load_to_named_tuple(
            o: Union[Dict, List, Tuple], base_type: Type[NT],
            field_to_parser: 'FieldToParser',
            field_parsers: List[AbstractParser]) -> NT:

        if isinstance(o, dict):
            # Convert the values of all fields in the NamedTuple, using
            # their type annotations. The keys in a dictionary object
            # (assuming it was loaded from JSON) are required to be
            # strings, so we don't need to convert them.
            return base_type(
                **{k: field_to_parser[k](o[k]) for k in o})
        # We're passed in a list or a tuple.
        return base_type(
            *[parser(elem) for parser, elem in zip(field_parsers, o)])

    @staticmethod
    def load_to_named_tuple_untyped(
            o: Union[Dict, List, Tuple], base_type: Type[NT],
            dict_parser: AbstractParser, list_parser: AbstractParser) -> NT:

        if isinstance(o, dict):
            return base_type(**dict_parser(o))
        # We're passed in a list or a tuple.
        return base_type(*list_parser(o))

    @classmethod
    def load_to_dict(cls, tp: TypeInfo, extras: Extras) -> str:
        v, k_next, v_next, i_next = tp.v_and_next_k_v()
        print('HEY')
        print(tp)

        try:
            kt, vt = tp.args
        except ValueError:
            # TODO
            kt = vt = Any

        gorg = tp.origin
        idx = tp.index

        tp_k_next = TypeInfo(kt, None, None, i_next, 'k', idx)
        string_k = cls.get_string_for_annotation(tp_k_next, None, extras)

        tp_v_next = TypeInfo(vt, None, None, i_next, 'v', idx)
        string_v = cls.get_string_for_annotation(tp_v_next, None, extras)

        result = f'{{{string_k}: {string_v} for {k_next}, {v_next} in {v}.items()}}'

        # TODO
        should_wrap = gorg not in {list, set, dict, tuple}
        # if gorg.__module__ not in {'builtins', 'collections'}:

        #         return base_type(
        #             (key_parser(k), val_parser(v))
        #             for k, v in o.items()
        #         )
        return f'{tp.name}({result})' if should_wrap else result

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
            key_to_parser: 'FieldToParser',
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
    def load_to_path(o: N, base_type: Type[Path]) -> Path:

        return base_type(str(o))

    @staticmethod
    @_alias(as_datetime)
    def load_to_datetime(
            o: Union[str, N], base_type: Type[datetime]) -> datetime:
        # alias: as_datetime
        ...

    @staticmethod
    @_alias(as_time)
    def load_to_time(o: str, base_type: Type[time]) -> time:
        # alias: as_time
        ...

    @staticmethod
    @_alias(as_date)
    def load_to_date(o: Union[str, N], base_type: Type[date]) -> date:
        # alias: as_date
        ...

    @staticmethod
    @_alias(as_timedelta)
    def load_to_timedelta(
            o: Union[str, N], base_type: Type[timedelta]) -> timedelta:
        # alias: as_timedelta
        ...

    @staticmethod
    def load_func_for_dataclass(
        cls: Type[T],
        config: Optional[META],
    ) -> Callable[[JSONObject], T]:

        return load_func_for_dataclass(
            cls, is_main_class=False, config=config)

    @classmethod
    def get_string_for_annotation(cls,
                                  tp: TypeInfo,
                                  base_cls: 'type | None',
                                  extras: Extras) -> str:
        type_ann = tp.origin

        hooks = cls.__LOAD_HOOKS__
        origin = get_origin_v2(type_ann)
        name = getattr(origin, '__name__', origin)

        # print('GET_STRING:', ann_type, origin)

        if origin in _SIMPLE_TYPES or issubclass(origin, _SIMPLE_TYPES):
            load_hook = hooks.get(origin)
            args = None

        elif (load_hook := hooks.get(origin)) is not None:
            # TODO
            try:
                args = get_args(type_ann)
            except ValueError:
                args = Any,

        else:

            # TODO everything should use `get_origin_v2`

            try:
                args = get_args(type_ann)
            except ValueError:
                args = Any,

            # Special case for Optional[x], which is actually Union[x, None]
            if is_union(origin):
                if NoneType in args and len(args) == 2:
                    tp = TypeInfo(args[0], None, None, tp.i, tp.prefix, tp.index)
                    string = cls.get_string_for_annotation(tp, base_cls, extras)
                    return f'None if {tp.v()} is None else {string}'

            else:
                # TODO END
                for t in hooks:
                    # print(t)
                    if issubclass(origin, (t, )):
                        load_hook = hooks[t]

        # print('TEST', gorg, elem_type)

        tp = TypeInfo(origin, args, name, tp.i, tp.prefix, tp.index)
        if load_hook is not None:
            return load_hook(tp, extras)

        # base_type = type_ann


    @classmethod
    def get_parser_for_annotation(cls, ann_type: Type[T],
                                  base_cls: Type = None,
                                  extras: Extras = None) -> 'AbstractParser | Callable[[dict[str, Any]], T]':
        """Returns the Parser (dispatcher) for a given annotation type."""
        hooks = cls.__LOAD_HOOKS__
        ann_type = eval_forward_ref_if_needed(ann_type, base_cls)
        load_hook = hooks.get(ann_type)
        base_type = ann_type

        # TODO: I'll need to refactor the code below to remove the nested `if`
        #   statements, when time allows. Right now the branching logic is
        #   unseemly and there's really no need for that, as any such
        #   performance gains (if they do exist) are minimal at best.

        if 'pattern' in extras and is_subclass_safe(
                ann_type, (date, time, datetime)):
            # Check for a field that was initially annotated like:
            #   Annotated[List[time], Pattern('%H:%M:%S')]
            return PatternedDTParser(base_cls, extras, base_type)

        if load_hook is None:
            # Need to check this first, because the `Literal` type in Python
            # 3.6 behaves a bit differently (doesn't have an `__origin__`
            # attribute for example)
            if is_literal(ann_type):
                return LiteralParser(base_cls, extras, ann_type)

            if is_annotated(ann_type):
                # Given `Annotated[T, MaxValue(10), ...]`, we only need `T`
                ann_type = get_args(ann_type)[0]
                return cls.get_parser_for_annotation(
                    ann_type, base_cls, extras)

            # This property will be available for most generic types in the
            # `typing` library.
            try:
                base_type = get_origin(ann_type, raise_=True)

            # If we can't access this property, it's likely a non-generic
            # class or a non-generic sub-type.
            except AttributeError:

                # https://stackoverflow.com/questions/76520264/dataclasswizard-after-upgrading-to-python3-11-is-not-working-as-expected
                if base_type is Any:
                    load_hook = cls.default_load_to

                elif isinstance(base_type, type):

                    if is_dataclass(base_type):
                        config: META = extras.get('config')

                        # enable support for cyclic / self-referential dataclasses
                        # see https://github.com/rnag/dataclass-wizard/issues/62
                        if AbstractMeta.recursive_classes or (config and config.recursive_classes):
                            # noinspection PyTypeChecker
                            return RecursionSafeParser(
                                base_cls, extras, base_type, hook=None
                            )
                        else:  # else, logic is same as normal
                            base_type: 'type[T]'
                            # return a dynamically generated `fromdict`
                            # for the `cls` (base_type)
                            return cls.load_func_for_dataclass(
                                base_type,
                                config=extras['config']
                            )

                    elif issubclass(base_type, Enum):
                        load_hook = hooks.get(Enum)

                    elif issubclass(base_type, UUID):
                        load_hook = hooks.get(UUID)

                    elif issubclass(base_type, tuple) \
                            and hasattr(base_type, '_fields'):

                        if getattr(base_type, '__annotations__', None):
                            # Annotated as a `typing.NamedTuple` subtype
                            load_hook = hooks.get(NamedTupleMeta)
                            return NamedTupleParser(
                                base_cls, extras, base_type, load_hook,
                                cls.get_parser_for_annotation
                            )
                        else:
                            # Annotated as a `collections.namedtuple` subtype
                            load_hook = hooks.get(namedtuple)
                            return NamedTupleUntypedParser(
                                base_cls, extras, base_type, load_hook,
                                cls.get_parser_for_annotation
                            )

                    elif is_typed_dict(base_type):
                        load_hook = cls.load_to_typed_dict
                        return TypedDictParser(
                            base_cls, extras, base_type, load_hook,
                            cls.get_parser_for_annotation
                        )

                elif isinstance(base_type, PatternedDT):
                    # Check for a field that was initially annotated like:
                    #   DateTimePattern('%m/%d/%y %H:%M:%S')]
                    return PatternedDTParser(base_cls, extras, base_type)

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
                            base_cls, extras, base_types[0],
                            cls.get_parser_for_annotation
                        )

                    else:
                        return UnionParser(
                            base_cls, extras, base_types,
                            cls.get_parser_for_annotation
                        )

                elif base_type in (PyRequired, PyNotRequired):
                    # Given `Required[T]` or `NotRequired[T]`, we only need `T`
                    ann_type = get_args(ann_type)[0]
                    return cls.get_parser_for_annotation(
                        ann_type, base_cls, extras)

                elif issubclass(base_type, defaultdict):
                    load_hook = hooks[defaultdict]
                    return DefaultDictParser(
                        base_cls, extras, ann_type, load_hook,
                        cls.get_parser_for_annotation
                    )

                elif issubclass(base_type, dict):
                    load_hook = hooks[dict]
                    return MappingParser(
                        base_cls, extras, ann_type, load_hook,
                        cls.get_parser_for_annotation
                    )

                elif issubclass(base_type, LSQ.__constraints__):
                    load_hook = cls.load_to_iterable
                    return IterableParser(
                        base_cls, extras, ann_type, load_hook,
                        cls.get_parser_for_annotation
                    )

                elif issubclass(base_type, tuple):
                    load_hook = hooks[tuple]
                    # Check if the `Tuple` appears in the variadic form
                    #   i.e. Tuple[str, ...]
                    args = get_args(ann_type)
                    is_variadic = args and args[-1] is ...
                    # Determine the parser for the annotation
                    parser: Type[AbstractParser] = TupleParser
                    if is_variadic:
                        parser = VariadicTupleParser

                    return parser(
                        base_cls, extras, ann_type, load_hook,
                        cls.get_parser_for_annotation
                    )

                elif base_type in (abc.Sequence, abc.MutableSequence, abc.Collection):
                    load_hook = cls.load_to_iterable
                    # desired (non-generic) origin type
                    desired_type = tuple if base_type is abc.Sequence else list
                    # Re-map to desired type, e.g. `Sequence[int]` -> `tuple[int]`
                    ann_type = desired_type[ann_type] if (
                        ann_type := get_args(ann_type)[0]) else desired_type

                    return IterableParser(
                        base_cls, extras, ann_type, load_hook,
                        cls.get_parser_for_annotation
                    )

                else:
                    load_hook = hooks.get(base_type)

        # TODO i'll need to refactor this to remove duplicate lines above -
        # maybe merge them together.
        elif issubclass(base_type, dict):
            load_hook = hooks[dict]
            return MappingParser(
                base_cls, extras, ann_type, load_hook,
                cls.get_parser_for_annotation)

        elif issubclass(base_type, LSQ.__constraints__):
            load_hook = cls.load_to_iterable
            return IterableParser(
                base_cls, extras, ann_type, load_hook,
                cls.get_parser_for_annotation)

        elif issubclass(base_type, tuple):
            load_hook = hooks[tuple]
            return TupleParser(
                base_cls, extras, ann_type, load_hook,
                cls.get_parser_for_annotation)

        if load_hook is None:
            # If load hook is still not resolved at this point, it's possible
            # the type is a subclass of a known type.
            for typ in hooks:
                # TODO use a `is_subclass_safe` helper function instead
                try:
                    if issubclass(base_type, typ):
                        load_hook = hooks[typ]
                        break
                except TypeError:
                    continue

            else:
                # No matching hook is found for the type.
                err = TypeError('Provided type is not currently supported.')
                raise ParseError(
                    err, None, base_type,
                    unsupported_type=base_type
                )

        if hasattr(load_hook, SINGLE_ARG_ALIAS):
            load_hook = resolve_alias_func(load_hook, locals())
            return SingleArgParser(base_cls, extras, base_type, load_hook)

        if hasattr(load_hook, IDENTITY):
            return IdentityParser(base_type, extras, base_type)

        return Parser(base_cls, extras, base_type, load_hook)


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
    cls.register_load_hook(bytes, cls.load_to_bytes)
    cls.register_load_hook(bytearray, cls.load_to_bytearray)
    cls.register_load_hook(NoneType, cls.load_to_none)
    # Complex types
    cls.register_load_hook(Enum, cls.load_to_enum)
    cls.register_load_hook(UUID, cls.load_to_uuid)
    cls.register_load_hook(set, cls.load_to_iterable)
    cls.register_load_hook(frozenset, cls.load_to_iterable)
    cls.register_load_hook(deque, cls.load_to_iterable)
    cls.register_load_hook(list, cls.load_to_iterable)
    cls.register_load_hook(tuple, cls.load_to_tuple)
    # noinspection PyTypeChecker
    # cls.register_load_hook(namedtuple, cls.load_to_named_tuple_untyped)
    cls.register_load_hook(NamedTupleMeta, cls.load_to_named_tuple)
    cls.register_load_hook(defaultdict, cls.load_to_defaultdict)
    cls.register_load_hook(dict, cls.load_to_dict)
    cls.register_load_hook(Decimal, cls.load_to_decimal)
    cls.register_load_hook(Path, cls.load_to_path)
    # Dates and times
    cls.register_load_hook(datetime, cls.load_to_datetime)
    cls.register_load_hook(time, cls.load_to_time)
    cls.register_load_hook(date, cls.load_to_date)
    cls.register_load_hook(timedelta, cls.load_to_timedelta)


def get_loader(class_or_instance=None, create=True,
               base_cls: T = LoadMixin) -> Type[T]:
    """
    Get the loader for the class, using the following logic:

        * Return the class if it's already a sub-class of :class:`LoadMixin`
        * If `create` is enabled (which is the default), a new sub-class of
          :class:`LoadMixin` for the class will be generated and cached on the
          initial run.
        * Otherwise, we will return the base loader, :class:`LoadMixin`, which
          can potentially be shared by more than one dataclass.

    """
    try:
        return dataclass_to_loader(class_or_instance)

    except KeyError:

        if hasattr(class_or_instance, _LOAD_HOOKS):
            return set_class_loader(class_or_instance, class_or_instance)

        elif create:
            cls_loader = create_new_class(class_or_instance, (base_cls, ))
            return set_class_loader(class_or_instance, cls_loader)

        return set_class_loader(class_or_instance, base_cls)


def fromdict(cls: Type[T], d: JSONObject) -> T:
    """
    Converts a Python dictionary object to a dataclass instance.

    Iterates over each dataclass field recursively; lists, dicts, and nested
    dataclasses will likewise be initialized as expected.

    When directly invoking this function, an optional Meta configuration for
    the dataclass can be specified via ``LoadMeta``; by default, this will
    apply recursively to any nested dataclasses. Here's a sample usage of this
    below::

        >>> LoadMeta(key_transform='CAMEL').bind_to(MyClass)
        >>> fromdict(MyClass, {"myStr": "value"})

    """
    try:
        load = CLASS_TO_LOAD_FUNC[cls]
    except KeyError:
        load = load_func_for_dataclass(cls)

    return load(d)


def fromlist(cls: Type[T], list_of_dict: List[JSONObject]) -> List[T]:
    """
    Converts a Python list object to a list of dataclass instances.

    Iterates over each dataclass field recursively; lists, dicts, and nested
    dataclasses will likewise be initialized as expected.

    """
    try:
        load = CLASS_TO_LOAD_FUNC[cls]
    except KeyError:
        load = load_func_for_dataclass(cls)

    return [load(d) for d in list_of_dict]


def load_func_for_dataclass(
        cls: Type[T],
        is_main_class: bool = True,
        config: Optional[META] = None,
        loader_cls=LoadMixin,
) -> Callable[[JSONObject], T]:

    # TODO dynamically generate for multiple nested classes at once

    # Tuple describing the fields of this dataclass.
    cls_fields = dataclass_fields(cls)

    cls_init_fields = dataclass_init_fields(cls)

    field_to_default = dataclass_field_to_default(cls)

    has_defaults = True if field_to_default else False

    # Get the loader for the class, or create a new one as needed.
    cls_loader = get_loader(cls, base_cls=loader_cls)

    # Get the meta config for the class, or the default config otherwise.
    meta = get_meta(cls)

    if is_main_class:  # we are being run for the main dataclass
        # If the `recursive` flag is enabled and a Meta config is provided,
        # apply the Meta recursively to any nested classes.
        if meta.recursive and meta is not AbstractMeta:
            config = meta

    # we are being run for a nested dataclass
    elif config:
        # we want to apply the meta config from the main dataclass
        # recursively.
        meta = meta | config
        meta.bind_to(cls, is_default=False)

    # This contains a mapping of the original field name to the parser for its
    # annotated type; the item lookup *can* be case-insensitive.
    try:
        field_to_parser = dataclass_field_to_load_parser(cls_loader, cls, config)
    except RecursionError:
        if meta.recursive_classes:
            # recursion-safe loader is already in use; something else must have gone wrong
            raise
        else:
            raise RecursiveClassError(cls) from None

    # A cached mapping of each key in a JSON or dictionary object to the
    # resolved dataclass field name; useful so we don't need to do a case
    # transformation (via regex) each time.
    json_to_field = json_field_to_dataclass_field(cls)

    field_to_path = dataclass_field_to_json_path(cls)
    num_paths = len(field_to_path)
    has_json_paths = True if num_paths else False

    catch_all_field = json_to_field.get(CATCH_ALL)
    has_catch_all = catch_all_field is not None

    # Fix for using `auto_assign_tags` and `raise_on_unknown_json_key` together
    # See https://github.com/rnag/dataclass-wizard/issues/137
    has_tag_assigned = meta.tag is not None
    if (has_tag_assigned and
            # Ensure `tag_key` isn't a dataclass field before assigning an
            # `ExplicitNull`, as assigning it directly can cause issues.
            # See https://github.com/rnag/dataclass-wizard/issues/148
            meta.tag_key not in field_to_parser):
        json_to_field[meta.tag_key] = ExplicitNull

    _locals = {
        'cls': cls,
        # 'py_case': cls_loader.transform_json_field,
        # 'field_to_parser': field_to_parser,
        # 'json_to_field': json_to_field,
        'ExplicitNull': ExplicitNull,
        'MISSING': MISSING,
    }

    _globals = {
        'cls_fields': cls_fields,
        'LOG': LOG,
        'MissingData': MissingData,
        'MissingFields': MissingFields,
        # TODO Common types
        'defaultdict': defaultdict,
        'deque': deque,
        'namedtuple': namedtuple,
    }

    # Initialize the FuncBuilder
    fn_gen = FunctionBuilder()

    if has_json_paths:
        # loop_over_o = num_paths != len(cls_init_fields)
        _locals['safe_get'] = safe_get
    # else:
        # loop_over_o = True

    extras: Extras = {'config': config, 'locals': _locals}

    fn_name = f'__dataclass_wizard_from_dict_{cls.__name__}__'
    with fn_gen.function(fn_name, ['o']):

        _pre_from_dict_method = getattr(cls, '_pre_from_dict', None)
        if _pre_from_dict_method is not None:
            _locals['__pre_from_dict__'] = _pre_from_dict_method
            fn_gen.add_line('o = __pre_from_dict__(o)')

        # Need to create a separate dictionary to copy over the constructor
        # args, as we don't want to mutate the original dictionary object.
        if has_defaults:
            fn_gen.add_line('init_kwargs = {}')
        if has_catch_all:
            fn_gen.add_line('catch_all = {}')

        if has_json_paths:

            with fn_gen.try_():
                for field, path in field_to_path.items():
                    if field in field_to_default:
                        default_value = f'_default_{field}'
                        _locals[default_value] = field_to_default[field]
                        extra_args = f', {default_value}'
                    else:
                        extra_args = ''
                    fn_gen.add_line(f'field={field!r}; init_kwargs[field] = field_to_parser[field](safe_get(o, {path!r}{extra_args}))')


            # TODO raise some useful message like (ex. on IndexError):
            #       Field "my_str" of type tuple[float, str] in A2 has invalid value ['123']

            with fn_gen.except_(ParseError, 'e'):
                # We run into a parsing error while loading the field value;
                # Add additional info on the Exception object before re-raising it.
                fn_gen.add_line("e.class_name, e.field_name, e.json_object, e.fields = cls, field, o, cls_fields")
                fn_gen.add_line("raise")

        # if loop_over_o:
        # This try-block is here in case the object `o` is None.
        with fn_gen.try_():
            # Loop over the dictionary object
            # with fn_gen.for_('json_key in o'):
            req_field_and_var = []
            for i, f in enumerate(cls_init_fields):
                val = f'v1'
                name = f.name
                var = f'__{name}'

                # parser = f'_parser{i}'
                # _locals[parser] = field_to_parser[name]

                string = blah(cls_loader, cls, extras, f)

                if name in field_to_default:
                    default = default_val = field_to_default[name]
                    if not is_builtin(default):
                        default = f'_dflt{i}'
                        _locals[default] = default_val
                    fn_gen.add_line(f"field={name!r}; {val}=o.get(field, {default}); init_kwargs[field] = {string}")

                else:
                    req_field_and_var.append(f'{name}={var}')
                    # fn_gen.add_line(f"field={name!r}; {val}=o[field]")
                    fn_gen.add_line(f"field={name!r}; {val}=o.get(field, MISSING)")
                    with fn_gen.if_(f'{val} is MISSING'):
                        # TODO
                        fn_gen.add_line('pass')
                    with fn_gen.else_():
                        fn_gen.add_line(f'{var} = {string}')
                # Note: pass the original cased field to the class constructor;
                # don't use the lowercase result from `py_case`
                # fn_gen.add_line("init_kwargs[field] = field_to_parser[field](o[json_key])")

            # with fn_gen.try_():
            #     # Get the resolved dataclass field name
            #     fn_gen.add_line("field = json_to_field[json_key]")
            #
            # with fn_gen.except_(KeyError):
            #     fn_gen.add_line('# Lookup Field for JSON Key')
            #     # Determines the dataclass field which a JSON key should map to.
            #     # Note this logic only runs the initial time, i.e. the first time
            #     # we encounter the key in a JSON object.
            #     #
            #     # :raises UnknownJSONKey: If there is no resolved field name for the
            #     #   JSON key, and`raise_on_unknown_json_key` is enabled in the Meta
            #     #   config for the class.
            #
            #     # Short path: an identical-cased field name exists for the JSON key
            #     with fn_gen.if_('json_key in field_to_parser'):
            #         fn_gen.add_line("field = json_to_field[json_key] = json_key")
            #
            #     with fn_gen.else_():
            #         # Transform JSON field name (typically camel-cased) to the
            #         # snake-cased variant which is convention in Python.
            #         fn_gen.add_line("py_field = py_case(json_key)")
            #
            #         with fn_gen.try_():
            #             # Do a case-insensitive lookup of the dataclass field, and
            #             # cache the mapping, so we have it for next time
            #             fn_gen.add_line("field "
            #                             "= json_to_field[json_key] "
            #                             "= field_to_parser.get_key(py_field)")
            #
            #         with fn_gen.except_(KeyError):
            #             # Else, we see an unknown field in the dictionary object
            #             fn_gen.add_line("field = json_to_field[json_key] = ExplicitNull")
            #             fn_gen.add_line("LOG.warning('JSON field %r missing from dataclass schema, "
            #                             "class=%r, parsed field=%r',json_key,cls,py_field)")
            #
            #             # Raise an error here (if needed)
            #             if meta.raise_on_unknown_json_key:
            #                 _globals['UnknownJSONKey'] = UnknownJSONKey
            #                 fn_gen.add_line("raise UnknownJSONKey(json_key, o, cls, cls_fields) from None")

            # Exclude JSON keys that don't map to any fields.
            # with fn_gen.if_('field is not ExplicitNull'):


            if has_catch_all:
                line = 'catch_all[json_key] = o[json_key]'
                if has_tag_assigned:
                    with fn_gen.elif_(f'json_key != {meta.tag_key!r}'):
                        fn_gen.add_line(line)
                else:
                    with fn_gen.else_():
                        fn_gen.add_line(line)

        with fn_gen.except_(ParseError, 'e'):
            # We run into a parsing error while loading the field value;
            # Add additional info on the Exception object before re-raising it.
            #
            # First confirm these values are not already set by an
            # inner dataclass. If so, it likely makes it easier to
            # debug the cause. Note that this should already be
            # handled by the `setter` methods.
            fn_gen.add_line("e.class_name, e.field_name, e.json_object = cls, field, o")
            fn_gen.add_line("raise")

        # with fn_gen.except_(TypeError):
            # If the object `o` is None, then raise an error with
            # the relevant info included.
            # with fn_gen.if_('o is None'):
            #     fn_gen.add_line("raise MissingData(cls) from None")
            #
            # # Check if the object `o` is some other type than what we expect -
            # # for example, we could be passed in a `list` type instead.
            # with fn_gen.if_('not isinstance(o, dict)'):
            #     fn_gen.add_line("e = TypeError('Incorrect type for field')")
            #     fn_gen.add_line("raise ParseError(e, o, dict, cls, desired_type=dict) from None")

            # Else, just re-raise the error.
            # fn_gen.add_line("raise")

        if has_catch_all:
            if catch_all_field.endswith('?'):  # Default value
                with fn_gen.if_('catch_all'):
                    fn_gen.add_line(f'init_kwargs[{catch_all_field.rstrip("?")!r}] = catch_all')
            else:
                fn_gen.add_line(f'init_kwargs[{catch_all_field!r}] = catch_all')

        # Now pass the arguments to the constructor method, and return
        # the new dataclass instance. If there are any missing fields,
        # we raise them here.

        # with fn_gen.try_():
        if has_defaults:
            req_field_and_var.append('**init_kwargs')
        init_parts = ', '.join(req_field_and_var)
        fn_gen.add_line(f"return cls({init_parts})")

        # with fn_gen.except_(TypeError, 'e'):
            # fn_gen.add_line("raise MissingFields(e, o, cls, init_kwargs, cls_fields) from None")

    functions = fn_gen.create_functions(
        locals=_locals, globals=_globals
    )

    cls_fromdict = functions[fn_name]

    # Save the load function for the main dataclass, so we don't need to run
    # this logic each time.
    if is_main_class:
        # Check if the class has a `from_dict`, and it's
        # a class method bound to `fromdict`.
        if ((from_dict := getattr(cls, 'from_dict', None)) is not None
                and getattr(from_dict, '__func__', None) is fromdict):
            _set_new_attribute(cls, 'from_dict', cls_fromdict)
        CLASS_TO_LOAD_FUNC[cls] = cls_fromdict

    return cls_fromdict


def blah(cls_loader,
        cls,
        config: Extras, f):

    field_type = f.type = eval_forward_ref_if_needed(f.type, cls)

    # i = 1

    # return blah_inner(
    #     field_type, cls, config
    # )

    return cls_loader.get_string_for_annotation(
        TypeInfo(field_type), cls, config
    )

