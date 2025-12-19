# TODO cleanup imports
from __future__ import annotations

import collections.abc as abc
from base64 import b64encode
from collections import defaultdict, deque
from dataclasses import _asdict_inner as __dataclasses_asdict_inner__, is_dataclass, MISSING, Field
from datetime import datetime, time, date, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
# noinspection PyUnresolvedReferences,PyProtectedMember
from typing import (
    Any, Type, Dict, List, Tuple, Iterable, Sequence, Union,
    NamedTupleMeta,
    SupportsFloat, AnyStr, Text, Callable, Optional, cast, Literal, Annotated, NamedTuple
)
from uuid import UUID

from .decorators import setup_recursive_safe_function, setup_recursive_safe_function_for_generic
from .enums import KeyCase, DateTimeTo
from .models import Extras, TypeInfo, SIMPLE_TYPES, PatternBase, UTC, ZERO, SCALAR_TYPES
from .type_conv import datetime_to_timestamp
from ..abstractions import AbstractDumperGenerator
from ..bases import AbstractMeta, BaseDumpHook, META
from ..class_helper import (
    v1_dataclass_field_to_alias_for_dump, dataclass_fields, get_meta, is_subclass_safe,
    DATACLASS_FIELD_TO_ALIAS_PATH_FOR_DUMP,
    dataclass_field_to_default, create_meta, CLASS_TO_DUMP_FUNC,
    dataclass_field_names, dataclass_field_to_skip_if,
)
from ..constants import CATCH_ALL, TAG, PACKAGE_NAME
from ..errors import (ParseError, MissingFields, MissingData, JSONWizardError)
from ..loader_selection import get_dumper, asdict
from ..log import LOG
from ..models import get_skip_if_condition, finalize_skip_if
from ..type_def import (
    DefFactory, NoneType, JSONObject,
    PyLiteralString,
    T, ExplicitNull
)
# noinspection PyProtectedMember
from ..utils.dataclass_compat import _set_new_attribute
from ..utils.dict_helper import NestedDict
from ..utils.function_builder import FunctionBuilder
from ..utils.typing_compat import (
    is_typed_dict, get_args, is_annotated,
    eval_forward_ref_if_needed, get_origin_v2, is_union,
    get_keys_for_typed_dict, is_typed_dict_type_qualifier,
)


class DumpMixin(AbstractDumperGenerator, BaseDumpHook):
    """
    This Mixin class derives its name from the eponymous `json.dumps`
    function. Essentially it contains helper methods to convert a `dataclass`
    to JSON strings (or a Python dictionary object).

    Refer to the :class:`AbstractDumper` class for documentation on any of the
    implemented methods.

    """
    __slots__ = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        setup_default_dumper(cls)

    transform_dataclass_field = None

    @staticmethod
    def default_dump_from(tp: TypeInfo, extras: Extras):
        # identity: o
        return tp.v()

    @staticmethod
    def dump_from_str(tp: TypeInfo, extras: Extras):
        return tp.v()

    @staticmethod
    def dump_from_int(tp: TypeInfo, extras: Extras):
        return tp.v()

    @staticmethod
    def dump_from_float(tp: TypeInfo, extras: Extras):
        return tp.v()

    @staticmethod
    def dump_from_bool(tp: TypeInfo, extras: Extras):
        return tp.v()

    @staticmethod
    def dump_from_bytes(tp: TypeInfo, extras: Extras):
        tp.ensure_in_locals(extras, b64encode)
        return f"b64encode({tp.v()}).decode('ascii')"

    @classmethod
    def dump_from_bytearray(cls, tp: TypeInfo, extras: Extras):
        tp.ensure_in_locals(extras, b64encode)
        return f"b64encode(bytes({tp.v()})).decode('ascii')"

    @staticmethod
    def dump_from_none(tp: TypeInfo, extras: Extras):
        return 'None'

    @staticmethod
    def dump_from_enum(tp: TypeInfo, extras: Extras):
        # alias: o.value
        return f'{tp.v()}.value'

    @staticmethod
    def dump_from_uuid(tp: TypeInfo, extras: Extras):
        # alias: o.hex
        return f'{tp.v()}.hex'

    @classmethod
    def dump_from_iterable(cls, tp: TypeInfo, extras: Extras):
        v, v_next, i_next = tp.v_and_next()
        gorg = tp.origin

        # noinspection PyBroadException
        try:
            elem_type = tp.args[0]
        except:
            elem_type = Any

        string = cls.dump_dispatcher_for_annotation(
            tp.replace(origin=elem_type, i=i_next, index=None, val_name=None), extras)

        if issubclass(gorg, (set, frozenset)):
            start_char = '{'
            end_char = '}'
        else:
            start_char = '['
            end_char = ']'

        result = f'{start_char}{string} for {v_next} in {v}{end_char}'

        return tp.wrap(result, extras)

    @classmethod
    def dump_from_tuple(cls, tp: TypeInfo, extras: Extras):
        args = tp.args

        # Determine the code string for the annotation

        # Check if the `Tuple` appears in the variadic form
        #   i.e. Tuple[str, ...]
        if args:
            is_variadic = args[-1] is ...
        else:
            # Annotated without args, as simply `tuple`
            args = (Any, ...)
            is_variadic = True

        if is_variadic:
            # Logic that handles the variadic form of :class:`Tuple`'s,
            # i.e. ``Tuple[str, ...]``
            #
            # Per `PEP 484`_, only **one** required type is allowed before the
            # ``Ellipsis``. That is, ``Tuple[int, ...]`` is valid whereas
            # ``Tuple[int, str, ...]`` would be invalid. `See here`_ for more info.
            #
            # .. _PEP 484: https://www.python.org/dev/peps/pep-0484/
            # .. _See here: https://github.com/python/typing/issues/180
            v, v_next, i_next = tp.v_and_next()

            # Given `Tuple[T, ...]`, we only need the generated string for `T`
            string = cls.dump_dispatcher_for_annotation(
                tp.replace(origin=args[0], i=i_next, index=None, val_name=None), extras)

            result = f'[{string} for {v_next} in {v}]'

            # Wrap because we need to create a tuple from list comprehension
            force_wrap = True
        else:
            string = ', '.join([
                cls.dump_dispatcher_for_annotation(
                    tp.replace(origin=arg, index=k, val_name=None),
                    extras)
                for k, arg in enumerate(args)])

            result = f'({string}, )'

            force_wrap = False

        return tp.wrap(result, extras, force=force_wrap)

    @classmethod
    @setup_recursive_safe_function(prefix='dump')
    def dump_from_named_tuple(cls, tp: TypeInfo, extras: Extras):
        fn_gen = extras['fn_gen']
        nt_tp = cast(NamedTuple, tp.origin)

        _locals = extras['locals']
        _locals['cls'] = nt_tp
        _locals['msg'] = "`dict` input is not supported for NamedTuple, use a dataclass instead."

        req_field_to_assign = {}
        field_assigns = []
        # noinspection PyProtectedMember
        optional_fields = set(nt_tp._field_defaults)
        has_optionals = True if optional_fields else False
        only_optionals = has_optionals and len(optional_fields) == len(nt_tp.__annotations__)
        num_fields = 0

        for field, field_tp in nt_tp.__annotations__.items():
            string = cls.dump_dispatcher_for_annotation(
                tp.replace(origin=field_tp, index=num_fields, val_name=None), extras)

            if has_optionals and field in optional_fields:
                field_assigns.append(string)
            else:
                req_field_to_assign[f'__{field}'] = string

            num_fields += 1

        params = ', '.join(req_field_to_assign)

        with fn_gen.try_():

            for field, string in req_field_to_assign.items():
                fn_gen.add_line(f'{field} = {string}')

            if has_optionals:
                opt_start = len(req_field_to_assign)
                fn_gen.add_line(f'L = len(v1); has_opt = L > {opt_start}')
                with fn_gen.if_(f'has_opt'):
                    fn_gen.add_line(f'fields = [{field_assigns.pop(0)}]')
                    for i, string in enumerate(field_assigns, start=opt_start + 1):
                        fn_gen.add_line(f'if L > {i}: fields.append({string})')

                    if only_optionals:
                        fn_gen.add_line(f'return cls(*fields)')
                    else:
                        fn_gen.add_line(f'return cls({params}, *fields)')

            fn_gen.add_line(f'return cls({params})')

        with fn_gen.except_(Exception, 'e'):
            with fn_gen.if_('(e_cls := e.__class__) is IndexError'):
                # raise `MissingFields`, as required NamedTuple fields
                # are not present in the input object `o`.
                fn_gen.add_line("raise_missing_fields(locals(), v1, cls, None)")
            with fn_gen.if_('e_cls is KeyError and type(v1) is dict'):
                # Input object is a `dict`
                # TODO should we support dict for namedtuple?
                fn_gen.add_line('raise TypeError(msg) from None')
            # re-raise
            fn_gen.add_line('raise e from None')

    @classmethod
    def dump_from_named_tuple_untyped(cls, tp: TypeInfo, extras: Extras):
        # Check if input object is `dict` or `list`.
        #
        # Assuming `Point` is a `namedtuple`, this performs
        # the equivalent logic as:
        #   Point(**x) if isinstance(x, dict) else Point(*x)
        v = tp.v()
        star, dbl_star = tp.multi_wrap(extras, 'nt_', f'*{v}', f'**{v}')
        return f'{dbl_star} if isinstance({v}, dict) else {star}'

    @classmethod
    def _build_dict_comp(cls, tp, v, i_next, k_next, v_next, kt, vt, extras):
        tp_k_next = tp.replace(origin=kt, i=i_next, prefix='k', index=None, val_name=None)
        string_k = cls.dump_dispatcher_for_annotation(tp_k_next, extras)

        tp_v_next = tp.replace(origin=vt, i=i_next, prefix='v', index=None, val_name=None)
        string_v = cls.dump_dispatcher_for_annotation(tp_v_next, extras)

        return f'{{{string_k}: {string_v} for {k_next}, {v_next} in {v}.items()}}'

    @classmethod
    def dump_from_dict(cls, tp: TypeInfo, extras: Extras):
        v, k_next, v_next, i_next = tp.v_and_next_k_v()

        try:
            kt, vt = tp.args
        except ValueError:
            # Annotated without two arguments,
            # e.g. like `dict[str]` or `dict`
            kt = vt = Any

        result = cls._build_dict_comp(
            tp, v, i_next, k_next, v_next, kt, vt, extras)

        return tp.wrap(result, extras)

    @classmethod
    def dump_from_defaultdict(cls, tp: TypeInfo, extras: Extras):
        v, k_next, v_next, i_next = tp.v_and_next_k_v()
        default_factory: DefFactory | None

        try:
            kt, vt = tp.args
            default_factory = getattr(vt, '__origin__', vt)
        except ValueError:
            # Annotated without two arguments,
            # e.g. like `defaultdict[str]` or `defaultdict`
            kt = vt = Any
            default_factory = NoneType

        result = cls._build_dict_comp(
            tp, v, i_next, k_next, v_next, kt, vt, extras)

        return tp.wrap_dd(default_factory, result, extras)

    @classmethod
    @setup_recursive_safe_function(prefix='dump')
    def dump_from_typed_dict(cls, tp: TypeInfo, extras: Extras):
        fn_gen = extras['fn_gen']

        req_keys, opt_keys = get_keys_for_typed_dict(tp.origin)

        result_list = []
        # TODO set __annotations__?
        td_annotations = tp.origin.__annotations__

        # Set required keys for the `TypedDict`
        for k in req_keys:
            field_tp = td_annotations[k]
            field_name = repr(k)
            string = cls.dump_dispatcher_for_annotation(
                tp.replace(origin=field_tp,
                           index=field_name,
                           val_name=None), extras)

            result_list.append(f'{field_name}: {string}')

        with fn_gen.try_():
            fn_gen.add_lines('result = {',
                             *(f'  {r},' for r in result_list),
                             '}')

            # Set optional keys for the `TypedDict` (if they exist)
            for k in opt_keys:
                field_tp = td_annotations[k]
                field_name = repr(k)
                string = cls.dump_dispatcher_for_annotation(
                    tp.replace(origin=field_tp, i=2, index=None, val_name=None), extras)
                with fn_gen.if_(f'(v2 := v1.get({field_name}, MISSING)) is not MISSING'):
                    fn_gen.add_line(f'result[{field_name}] = {string}')
            fn_gen.add_line('return result')

        with fn_gen.except_(Exception, 'e'):
            with fn_gen.if_('type(e) is KeyError'):
                fn_gen.add_line('name = e.args[0]; e = KeyError(f"Missing required key: {name!r}")')
            with fn_gen.elif_('not isinstance(v1, dict)'):
                fn_gen.add_line('e = TypeError("Incorrect type for object")')
            fn_gen.add_line('raise ParseError(e, v1, {}) from None')

    @classmethod
    @setup_recursive_safe_function_for_generic(None, prefix='dump')
    def dump_from_union(cls, tp: TypeInfo, extras: Extras):
        fn_gen = extras['fn_gen']
        config = extras['config']
        actual_cls = extras['cls']

        tag_key = config.tag_key or TAG
        auto_assign_tags = config.auto_assign_tags

        i = tp.field_i
        fields = f'fields_{i}'

        args = tp.args
        in_optional = NoneType in args

        _locals = extras['locals']
        _locals[fields] = args
        _locals['tag_key'] = tag_key

        type_checks = []
        try_parse_at_end = []
        dataclass_and_line = []
        has_dataclass = False

        for possible_tp in args:

            possible_tp = eval_forward_ref_if_needed(possible_tp, actual_cls)

            tp_new = TypeInfo(possible_tp, field_i=i)
            tp_new.in_optional = in_optional

            if possible_tp is NoneType:
                with fn_gen.if_('v1 is None'):
                    fn_gen.add_line('return None')
                continue

            if is_dataclass(possible_tp):
                has_dataclass = True
                # we see a dataclass in `Union` declaration
                meta = get_meta(possible_tp)
                cls_name = possible_tp.__name__

                tag = meta.tag
                assign_tags_to_cls = auto_assign_tags or meta.auto_assign_tags
                if assign_tags_to_cls and not tag:
                    tag = cls_name
                    # We don't want to mutate the base Meta class here
                    if meta is AbstractMeta:
                        create_meta(possible_tp, cls_name, tag=tag)
                    else:
                        meta.tag = cls_name

                if tag:
                    string = cls.dump_dispatcher_for_annotation(tp_new, extras)
                    dataclass_and_line.append(
                        (possible_tp, cls_name, tag,
                         f'result = {string}; result[tag_key] = {tag!r}; return result'))
                    continue

                # elif not config.v1_unsafe_parse_dataclass_in_union:
                #     e = ValueError('Cannot parse dataclass types in a Union without '
                #                    'one of the following `Meta` settings:\n\n'
                #                    '  * `auto_assign_tags = True`\n'
                #                    f'    - Set on class `{extras["cls_name"]}`.\n\n'
                #                    f'  * `tag = "{cls_name}"`\n'
                #                    f'    - Set on class `{possible_tp.__qualname__}`.\n\n'
                #                    '  * `v1_unsafe_parse_dataclass_in_union = True`\n'
                #                    f'    - Set on class `{extras["cls_name"]}`\n\n'
                #                    'For more information, refer to:\n'
                #                    '  https://dcw.ritviknag.com/en/latest/common_use_cases/dataclasses_in_union_types.html')
                #     raise e from None

            string = cls.dump_dispatcher_for_annotation(tp_new, extras)

            try_parse_lines = [
                'try:',
                f'  return {string}',
                'except Exception:',
                '  pass',
            ]

            # TODO disable for dataclasses

            if (possible_tp in SIMPLE_TYPES
                or is_subclass_safe(
                    get_origin_v2(possible_tp), SIMPLE_TYPES)):

                tn = tp_new.type_name(extras)
                type_checks.extend([
                    f'if tp is {tn}:',
                    '  return v1'
                ])
                list_to_add = try_parse_at_end
            else:
                list_to_add = type_checks

            list_to_add.extend(try_parse_lines)

        fn_gen.add_line('tp = type(v1)')

        if has_dataclass:
            var_to_dataclass = {}

            for i, (dataclass, name, tag, line) in enumerate(dataclass_and_line, start=1):
                cls_name = f'C{i}'
                var_to_dataclass[cls_name] = dataclass
                with fn_gen.if_(f'tp is {cls_name}', comment=f'{name} -> {tag!r}'):
                    fn_gen.add_line(line)

            tp.ensure_in_locals(extras, **var_to_dataclass)

            # fn_gen.add_line(
            #     "raise ParseError("
            #     "TypeError('Object with tag was not in any of Union types'),"
            #     f"v1,{fields},"
            #     "input_tag=tag,"
            #     "tag_key=tag_key,"
            #     f"valid_tags={list(dataclass_tag_to_lines)})"
            # )

        if type_checks:
            fn_gen.add_lines(*type_checks)

        if try_parse_at_end:
            fn_gen.add_lines(*try_parse_at_end)

        # Invalid type for Union
        fn_gen.add_line("raise ParseError("
                        "TypeError('Object was not in any of Union types'),"
                        f"v1,{fields},"
                        "tag_key=tag_key"
                        ")")

    @staticmethod
    def dump_from_literal(tp: TypeInfo, extras: Extras):
        return tp.v()

    @staticmethod
    def dump_from_decimal(tp: TypeInfo, extras: Extras):
        return f'str({tp.v()})'

    @staticmethod
    def dump_from_path(tp: TypeInfo, extras: Extras):
        return f'str({tp.v()})'

    @classmethod
    def dump_from_date(cls, tp: TypeInfo, extras: Extras):
        o = tp.v()

        if extras['config'].v1_dump_date_time_as is DateTimeTo.TIMESTAMP:
            tp.ensure_in_locals(extras, datetime, UTC=UTC)
            return f'int(datetime((v0 := {o}).year, v0.month, v0.day, tzinfo=UTC).timestamp())'

        return f'{o}.isoformat()'

    @classmethod
    def dump_from_datetime(cls, tp: TypeInfo, extras: Extras):
        o = tp.v()
        config = extras['config']

        if config.v1_dump_date_time_as is DateTimeTo.TIMESTAMP:
            naive_tz = config.v1_assume_naive_datetime_tz

            if naive_tz is None:
                def raise_naive():
                    raise ValueError('Naive datetime has no timezone; '
                                     'set v1_assume_naive_datetime_tz to '
                                     'define how it should be interpreted.')

                tp.ensure_in_locals(extras, raise_naive, ZERO=ZERO)
                return f'raise_naive() if (v0 := {o}).tzinfo is None else int(v0.timestamp()) if v0.utcoffset() == ZERO else int(v0.astimezone(UTC).timestamp())'

            else:
                tp.ensure_in_locals(extras, datetime_to_timestamp, assume_naive_tz=naive_tz)
                return f'datetime_to_timestamp({o}, assume_naive_tz)'

        # Safe: source is datetime.isoformat(); '+00:00' only appears for UTC
        return f"{o}.isoformat().replace('+00:00', 'Z', 1)"

    @staticmethod
    def dump_from_time(tp: TypeInfo, _extras: Extras):
        o = tp.v()
        # Safe: source is time.isoformat(); '+00:00' only appears for UTC
        return f"{o}.isoformat().replace('+00:00', 'Z', 1)"

    @staticmethod
    def dump_from_timedelta(tp: TypeInfo, extras: Extras):
        return f'str({tp.v()})'

    @staticmethod
    @setup_recursive_safe_function(
        fn_name=f'__{PACKAGE_NAME}_to_dict_{{cls_name}}__')
    def dump_from_dataclass(tp: TypeInfo, extras: Extras):
        dump_func_for_dataclass(tp.origin, extras)

    @classmethod
    def dump_dispatcher_for_annotation(cls,
                                       tp,
                                       extras):

        hooks = cls.__DUMP_HOOKS__

        # type_ann = tp.origin
        type_ann = eval_forward_ref_if_needed(tp.origin, extras['cls'])

        origin = get_origin_v2(type_ann)
        name = getattr(origin, '__name__', origin)
        args = None

        if is_annotated(type_ann):
            # Given `Annotated[T, ...]`, we only need `T`
            type_ann, *field_extras = get_args(type_ann)
            type_ann = eval_forward_ref_if_needed(type_ann, extras['cls'])
            origin = get_origin_v2(type_ann)
            name = getattr(origin, '__name__', origin)
            # Check for Custom Patterns for date / time / datetime
            for extra in field_extras:
                if isinstance(extra, PatternBase):
                    extras['pattern'] = extra

        elif is_typed_dict_type_qualifier(origin):
            # Given `Required[T]` or `NotRequired[T]`, we only need `T`
            type_ann = get_args(type_ann)[0]
            origin = get_origin_v2(type_ann)
            name = getattr(origin, '__name__', origin)

        # TypeAliasType: Type aliases are created through
        # the `type` statement
        if (value := getattr(origin, '__value__', None)) is not None:
            type_ann = value
            origin = get_origin_v2(type_ann)
            name = getattr(origin, '__name__', origin)

        # `LiteralString` enforces stricter rules at
        # type-checking but behaves like `str` at runtime.
        # TODO maybe add `load_to_literal_string`
        if origin is PyLiteralString:
            dump_hook = cls.dump_from_str
            origin = str
            name = 'str'

        # -> Atomic, immutable types which don't require
        #    any iterative / recursive handling.
        elif origin in SIMPLE_TYPES or is_subclass_safe(origin, SIMPLE_TYPES):
            dump_hook = hooks.get(origin)

        elif (dump_hook := hooks.get(origin)) is not None:
            try:
                args = get_args(type_ann)
            except ValueError:
                args = Any,

        # -> Union[x]
        elif is_union(origin):
            dump_hook = cls.dump_from_union
            args = get_args(type_ann)

            # Special case for Optional[x], which is actually Union[x, None]
            if len(args) == 2 and NoneType in args:
                origin = args[0]
                # optional simple type: (str, int, float, bool, Literal, Any)
                is_simple_type = origin in SCALAR_TYPES or origin is Any or origin is Literal

                val_name = None
                o = tp.v()

                if is_simple_type:
                    val_name = tp.val_name or 'v1'
                    o = tp.v()
                elif tp.val_name:
                    val_name = 'v0'
                    o = f'(v0 := {tp.v()})'
                new_tp = tp.replace(origin=origin, args=None, name=None, val_name=val_name)
                new_tp.in_optional = True

                string = cls.dump_dispatcher_for_annotation(new_tp, extras)

                return string if is_simple_type else f'None if {o} is None else {string}'

        # -> Literal[X, Y, ...]
        elif origin is Literal:
            dump_hook = cls.dump_from_literal
            args = get_args(type_ann)

        # https://stackoverflow.com/questions/76520264/dataclasswizard-after-upgrading-to-python3-11-is-not-working-as-expected
        elif origin is Any:
            dump_hook = cls.default_dump_from

        elif is_subclass_safe(origin, tuple) and hasattr(origin, '_fields'):

            if getattr(origin, '__annotations__', None):
                # Annotated as a `typing.NamedTuple` subtype
                dump_hook = cls.dump_from_named_tuple
            else:
                # Annotated as a `collections.namedtuple` subtype
                dump_hook = cls.dump_from_named_tuple_untyped

        elif is_typed_dict(origin):
            dump_hook = cls.dump_from_typed_dict

        elif is_dataclass(origin):
            # return a dynamically generated `asdict`
            # for the `cls` (base_type)
            dump_hook = cls.dump_from_dataclass

        elif is_subclass_safe(origin, Enum):
            dump_hook = cls.dump_from_enum

        elif origin in (abc.Sequence, abc.MutableSequence, abc.Collection):
            if origin is abc.Sequence:
                dump_hook = cls.dump_from_tuple
                # desired (non-generic) origin type
                name = 'tuple'
                origin = tuple
                # Re-map type arguments to variadic tuple format,
                # e.g. `Sequence[int]` -> `tuple[int, ...]`
                try:
                    args = (get_args(type_ann)[0], ...)
                except (IndexError, ValueError):
                    args = Any,
            else:
                dump_hook = cls.dump_from_iterable
                # desired (non-generic) origin type
                name = 'list'
                origin = list
                # Get type arguments, e.g. `Sequence[int]` -> `int`
                try:
                    args = get_args(type_ann)
                except ValueError:
                    args = Any,

        elif isinstance(origin, PatternBase):
            __base__ = origin.base

            if issubclass(__base__, datetime):
                dump_hook = cls.dump_from_datetime
                origin = datetime
            elif issubclass(__base__, date):
                dump_hook = cls.dump_from_date
                origin = date
            elif issubclass(__base__, time):
                dump_hook = cls.dump_from_time
                origin = time

        else:

            # TODO everything should use `get_origin_v2`
            try:
                args = get_args(type_ann)
            except ValueError:
                args = Any,

        if dump_hook is None:
            # TODO END
            for t in hooks:
                if issubclass(origin, (t,)):
                    dump_hook = hooks[t]
                    break

        tp.origin = origin
        tp.args = args
        tp.name = name

        if dump_hook is not None:
            result = dump_hook(tp, extras)
            return result

        # No matching hook is found for the type.
        # TODO do we want to add a `Meta` field to not raise
        #  an error but perform a default action?
        err = TypeError('Provided type is not currently supported.')
        pe = ParseError(
            err, origin, type_ann,
            resolution='Consider decorating the class with `@dataclass`',
            unsupported_type=origin
        )
        raise pe from None


def setup_default_dumper(cls=DumpMixin):
    """
    Setup the default type hooks to use when converting
    a `dataclass` instance to a `str` (json) or a
    Python `dict` object.

    Note: `cls` must be :class:`DumpMixIn` or a sub-class of it.
    """
    # TODO maybe `dict.update` might be better?

    # Technically a complex type, however check this
    # first, since `StrEnum` and `IntEnum` are subclasses
    # of `str` and `int`
    cls.register_dump_hook(Enum, cls.dump_from_enum)
    # Simple types
    cls.register_dump_hook(str, cls.dump_from_str)
    cls.register_dump_hook(float, cls.dump_from_float)
    cls.register_dump_hook(bool, cls.dump_from_bool)
    cls.register_dump_hook(int, cls.dump_from_int)
    cls.register_dump_hook(bytes, cls.dump_from_bytes)
    cls.register_dump_hook(bytearray, cls.dump_from_bytearray)
    cls.register_dump_hook(NoneType, cls.dump_from_none)
    # Complex types
    cls.register_dump_hook(UUID, cls.dump_from_uuid)
    cls.register_dump_hook(set, cls.dump_from_iterable)
    cls.register_dump_hook(frozenset, cls.dump_from_iterable)
    cls.register_dump_hook(deque, cls.dump_from_iterable)
    cls.register_dump_hook(list, cls.dump_from_iterable)
    cls.register_dump_hook(tuple, cls.dump_from_tuple)
    # `typing` Generics
    # cls.register_load_hook(Literal, cls.dump_from_literal)
    # noinspection PyTypeChecker
    cls.register_dump_hook(defaultdict, cls.dump_from_defaultdict)
    cls.register_dump_hook(dict, cls.dump_from_dict)
    cls.register_dump_hook(Decimal, cls.dump_from_decimal)
    cls.register_dump_hook(Path, cls.dump_from_path)
    # Dates and times
    cls.register_dump_hook(datetime, cls.dump_from_datetime)
    cls.register_dump_hook(time, cls.dump_from_time)
    cls.register_dump_hook(date, cls.dump_from_date)
    cls.register_dump_hook(timedelta, cls.dump_from_timedelta)


def check_and_raise_missing_fields(
    _locals, o, cls, fields: tuple[Field, ...]):

    missing_fields = [f.name for f in fields
                      if f.init
                      and f'__{f.name}' not in _locals
                      and (f.default is MISSING
                           and f.default_factory is MISSING)]

    missing_keys = [v1_dataclass_field_to_alias_for_dump(cls)[field]
                    for field in missing_fields]

    raise MissingFields(
        None, o, cls, fields, None, missing_fields,
        missing_keys
    ) from None


def dump_func_for_dataclass(
    cls: type,
    extras: Extras | None = None,
    dumper_cls=DumpMixin,
    base_meta_cls: type = AbstractMeta,
) -> Union[Callable[[T], JSONObject], str]:

    # TODO dynamically generate for multiple nested classes at once

    # Tuple describing the fields of this dataclass.
    cls_fields = dataclass_fields(cls)

    cls_fields_list = list(cls_fields)
    cls_field_names = dataclass_field_names(cls)

    # Get the loader for the class, or create a new one as needed.
    cls_dumper = get_dumper(cls, base_cls=dumper_cls, v1=True)

    cls_name = cls.__name__

    fn_name = f'__{PACKAGE_NAME}_to_dict_{cls_name}__'

    # Get the meta config for the class, or the default config otherwise.
    meta = get_meta(cls, base_meta_cls)

    if extras is None:  # we are being run for the main dataclass
        is_main_class = True

        # If the `recursive` flag is enabled and a Meta config is provided,
        # apply the Meta recursively to any nested classes.
        #
        # Else, just use the base `AbstractMeta`.
        config: META = meta if meta.recursive else base_meta_cls

        # Initialize the FuncBuilder
        fn_gen = FunctionBuilder()

        new_locals = {
            'cls': cls,
            'fields': cls_fields,
        }

        extras: Extras = {
            'config': config,
            'cls': cls,
            'cls_name': cls_name,
            'locals': new_locals,
            'recursion_guard': {cls: fn_name},
            'fn_gen': fn_gen,
        }

        _globals = {
            'MISSING': MISSING,
            'ParseError': ParseError,
            'raise_missing_fields': check_and_raise_missing_fields,
            're_raise': re_raise,
        }

    # we are being run for a nested dataclass
    else:
        is_main_class = False

        # config for nested dataclasses
        config = extras['config']

        # Initialize the FuncBuilder
        fn_gen = extras['fn_gen']

        if config is not base_meta_cls:
            # we want to apply the meta config from the main dataclass
            # recursively.
            meta = meta | config
            meta.bind_to(cls, is_default=False)

        new_locals = extras['locals']
        new_locals['fields'] = cls_fields

        # TODO need a way to auto-magically do this
        extras['cls'] = cls
        extras['cls_name'] = cls_name

    key_case: KeyCase | None = cls_dumper.transform_dataclass_field

    # TODO decide if different logic is needed for `AUTO` case
    if key_case is KeyCase.AUTO:
        key_case = None

    # A cached mapping of each dataclass field to the resolved key name in a
    # JSON or dictionary object; useful so we don't need to do a case
    # transformation (via regex) each time.
    field_to_alias = v1_dataclass_field_to_alias_for_dump(cls)
    check_aliases = True if field_to_alias else False

    field_to_path = DATACLASS_FIELD_TO_ALIAS_PATH_FOR_DUMP[cls]
    has_paths = True if field_to_path else False

    # A cached mapping of dataclass field name to its default value, either
    # via a `default` or `default_factory` argument.
    field_to_default = dataclass_field_to_default(cls)
    has_defaults = True if field_to_default else False

    # A cached mapping of dataclass field name to its SkipIf condition.
    field_to_skip_if = dataclass_field_to_skip_if(cls)

    skip_if_condition = get_skip_if_condition(
        meta.skip_if, new_locals, '_skip_value')
    skip_defaults_if_condition = get_skip_if_condition(
        meta.skip_defaults_if, new_locals, '_skip_defaults_value')

    skip_defaults = True if meta.skip_defaults else False
    skip_if = True if field_to_skip_if or skip_if_condition else False
    skip_any = True if skip_if or skip_defaults else False

    # Fix for using `auto_assign_tags` and `raise_on_unknown_json_key` together
    # See https://github.com/rnag/dataclass-wizard/issues/137
    # has_tag_assigned = meta.tag is not None
    # if (has_tag_assigned and
    #     # Ensure `tag_key` isn't a dataclass field,
    #     # to avoid issues with our logic.
    #     # See https://github.com/rnag/dataclass-wizard/issues/148
    #     meta.tag_key not in cls_field_names):
    #         expect_tag_as_unknown_key = True
    # else:
    #     expect_tag_as_unknown_key = False

    # Tag key to populate when a dataclass is in a `Union` with other types.
    # tag_key = meta.tag_key or TAG

    catch_all_name: 'str | None' = field_to_alias.pop(CATCH_ALL, None)
    has_catch_all = catch_all_name is not None

    if has_catch_all:
        catch_all_name_stripped = catch_all_name.rstrip('?')
        catch_all_idx = cls_field_names.index(catch_all_name_stripped)
        # remove catch all field from list, so we don't iterate over it
        # noinspection PyTypeChecker
        del cls_fields_list[catch_all_idx]
    else:
        catch_all_name_stripped = None

    # if on_unknown_key is not None:
    #     should_raise = on_unknown_key is KeyAction.RAISE
    #     should_warn = on_unknown_key is KeyAction.WARN
    #     if should_warn or should_raise:
    #         pre_assign = 'i+=1; '
    # else:
    #     should_raise = should_warn = None

    cls_name = cls.__name__

    with fn_gen.function(
            fn_name, [
            'o',
            'dict_factory=dict',
            "exclude:'list[str]|None'=None",
            f'skip_defaults:bool={skip_defaults}',
        ], MISSING, new_locals):

        if (_pre_to_dict := getattr(cls, '_pre_to_dict', None)) is not None:
            new_locals['__pre_to_dict__'] = _pre_to_dict
            fn_gen.add_line('o = __pre_to_dict__(o)')

        # Need to create a separate dictionary to copy over the constructor
        # args, as we don't want to mutate the original dictionary object.
        if has_defaults:
            fn_gen.add_line('add_defaults = not skip_defaults')

        if has_paths:
            new_locals['NestedDict'] = NestedDict
            fn_gen.add_line('paths = NestedDict()')

        required_field_assigns = []
        default_assigns = []
        path_assigns = []
        name_to_skip_condition = {}

        if cls_fields_list:

            with fn_gen.try_():

                for i, f in enumerate(cls_fields_list):
                    name = f.name
                    default = field_to_default.get(name, ExplicitNull)
                    has_default = default is not ExplicitNull
                    has_skip_if = False
                    # TODO: This is if we want to check if field is in `exclude`
                    #  (not huge performance gain)
                    # skip_field = f'_skip_{i}'
                    default_value = f'_default_{i}'

                    # Check for Field Aliases + Paths
                    # NOTE: `key` is used later, so we need to capture it.
                    if check_aliases and (key := field_to_alias.get(name)) is not None:
                        # special case: skip serialization for field, e.g. `Alias(..., skip=True)`
                        if key is ExplicitNull:
                            continue

                    elif key_case is None:
                        key = name

                    else:
                        key = key_case(name)

                    # If field has an explicit `SkipIf` condition
                    if skip_if:
                        has_skip_if = True
                        if (_skip_condition := field_to_skip_if.get(name)) is not None:
                            _skip_if = get_skip_if_condition(
                                _skip_condition, new_locals, condition_i=i)
                            _final_skip_if = finalize_skip_if(_skip_condition, 'v1', _skip_if)
                            name_to_skip_condition[name] = f'not ({_final_skip_if})'

                        # If Meta `skip_if` has a value
                        elif skip_if_condition:
                            _final_skip_if = finalize_skip_if(
                                meta.skip_if, 'v1', skip_if_condition)
                            name_to_skip_condition[name] = f'not ({_final_skip_if})'

                        # # Else, proceed as normal
                        # else:
                        #     field_assignments.append(f"if not {skip_field}:")


                    # A dataclass field which specifies a "JSON Path".
                    if has_paths and (
                        path := field_to_path.get(name)
                    ) is not None:  # AliasPath(...)

                        if has_default:
                            # with fn_gen.if_(val_is_found):
                            # with fn_gen.if_(f'{val} is not MISSING'):
                            new_locals[default_value] = default
                            string = generate_field_code(cls_dumper, extras, f, i)
                            key_part = ''.join(f'[{p!r}]' for p in path)
                            line = f'paths{key_part} = {string}'
                            default_assigns.append((name, key, default_value, line))
                        else:
                            key_part = ''.join(f'[{p!r}]' for p in path)
                            var_name = 'v1' if has_skip_if else f'o.{name}'
                            string = generate_field_code(cls_dumper, extras, f, i, var_name)
                            path_assigns.append((name, f'paths{key_part} = {string}'))

                        continue

                    if has_default:
                        # with fn_gen.if_(val_is_found):
                        # with fn_gen.if_(f'{val} is not MISSING'):
                        new_locals[default_value] = default
                        string = generate_field_code(cls_dumper, extras, f, i)
                        line = f'result[{key!r}] = {string}'
                        default_assigns.append((name, key, default_value, line))
                    else:
                        # TODO confirm this is ok
                        # vars_for_fields.append(f'{name}={var}')
                        if has_skip_if:
                            string = generate_field_code(cls_dumper, extras, f, i, 'v1')
                            line = f'result[{key!r}] = {string}'
                            default_assigns.append((name, ExplicitNull, ExplicitNull, line))
                        else:
                            string = generate_field_code(cls_dumper, extras, f, i, f'o.{name}')
                            required_field_assigns.append((name, key, string))

                # Add assignments for `AliasPath(...)`
                for (name, line) in path_assigns:
                    if (condition := name_to_skip_condition.get(name)) is not None:
                        fn_gen.add_line(f'v1 = o.{name}')
                        with fn_gen.if_(condition):
                            fn_gen.add_line(line)
                    else:
                        fn_gen.add_line(line)

                # Add required dataclass field assignments
                fn_gen.add_line('result = {')
                for (_, key, string) in required_field_assigns:
                    fn_gen.add_line(f'  {key!r}: {string},')
                fn_gen.add_line('}')

                # Add default (optional) dataclass field assignments
                for (name, key, default_name, line) in default_assigns:
                    fn_gen.add_line(f'v1 = o.{name}')
                    def_condition = f'add_defaults or v1 != {default_name}'

                    if skip_defaults_if_condition:
                        _final_skip_if = finalize_skip_if(
                            meta.skip_defaults_if, 'v1', skip_defaults_if_condition)
                        # TODO missing skip individual condition!!
                        with fn_gen.if_(f'(add_defaults or v1 != {default_name}) and not ({_final_skip_if})'):
                            fn_gen.add_line(line)

                    elif (condition := name_to_skip_condition.get(name)) is not None:
                        if default_name is ExplicitNull:  # Required field with skip condition
                            with fn_gen.if_(condition):
                                fn_gen.add_line(line)
                        else:
                            with fn_gen.if_(f'(add_defaults or v1 != {default_name}) and {condition}'):
                                fn_gen.add_line(line)

                    else:
                        with fn_gen.if_(def_condition):
                            fn_gen.add_line(line)

            # create a broad `except Exception` block, as we will be
            # re-raising all exception(s) as a custom `ParseError`.
            with fn_gen.except_(Exception, 'e', ParseError):
                fn_gen.add_line("re_raise(e, cls, o, fields, '<UNK>', locals().get('v0'))")

        # TODO
        # if has_catch_all:
        #     if expect_tag_as_unknown_key:
        #         # add an alias for the tag key, so we don't capture it
        #         field_to_alias['...'] = meta.tag_key
        #
        #     if 'f2k' in _locals:
        #         # If this is the case, then `AUTO` key transform mode is enabled
        #         # line = 'extra_keys = o.keys() - f2k.values()'
        #         aliases_var = 'f2k.values()'
        #
        #     else:
        #         aliases_var = 'aliases'
        #         _locals['aliases'] = set(field_to_alias.values())
        #
        #     catch_all_def = f'{{k: o[k] for k in o if k not in {aliases_var}}}'
        #
        #     if catch_all_field.endswith('?'):  # Default value
        #         with fn_gen.if_('len(o) != i'):
        #             fn_gen.add_line(f'init_kwargs[{catch_all_field_stripped!r}] = {catch_all_def}')
        #     else:
        #         var = f'__{catch_all_field_stripped}'
        #         fn_gen.add_line(f'{var} = {{}} if len(o) == i else {catch_all_def}')
        #         vars_for_fields.insert(catch_all_idx, var)
        #
        # elif should_warn or should_raise:
        #     if expect_tag_as_unknown_key:
        #         # add an alias for the tag key, so we don't raise an error when we see it
        #         field_to_alias['...'] = meta.tag_key
        #
        #     if 'f2k' in _locals:
        #         # If this is the case, then `AUTO` key transform mode is enabled
        #         line = 'extra_keys = o.keys() - f2k.values()'
        #     else:
        #         _locals['aliases'] = set(field_to_alias.values())
        #         line = 'extra_keys = set(o) - aliases'
        #
        #     with fn_gen.if_('len(o) != i'):
        #         fn_gen.add_line(line)
        #         if should_raise:
        #             # Raise an error here (if needed)
        #             _locals['UnknownKeysError'] = UnknownKeysError
        #             fn_gen.add_line("raise UnknownKeysError(extra_keys, o, cls, fields) from None")
        #         elif should_warn:
        #             # Show a warning here
        #             _locals['LOG'] = LOG
        #             fn_gen.add_line(r"LOG.warning('Found %d unknown keys %r not mapped to the dataclass schema.\n"
        #                                 r"  Class: %r\n  Dataclass fields: %r', len(extra_keys), extra_keys, cls.__qualname__, [f.name for f in fields])")

        # Now pass the arguments to the dict_factory method, and return
        # the new dict_factory instance.

        # if has_defaults:
        #     vars_for_fields.append('**init_kwargs')

        if has_catch_all:
            if (default := field_to_default.get(catch_all_name_stripped, ExplicitNull)) is not ExplicitNull:
                default_value = f'_default_{len(cls_fields_list)}'
                new_locals[default_value] = default
                condition = f"(v0 := o.{catch_all_name_stripped}) != {default_value}"

            else:
                condition = f'v0 := o.{catch_all_name_stripped}'

            with fn_gen.if_(condition):
                with fn_gen.for_(f"k, v in v0.items()"):
                    fn_gen.globals['__asdict_inner__'] = __dataclasses_asdict_inner__
                    fn_gen.add_line('result[k] = __asdict_inner__(v,dict_factory)')

        with fn_gen.if_('exclude is not None'):
            with fn_gen.for_('k in exclude'):
                fn_gen.add_line('del result[k]')

        if has_paths:
            fn_gen.add_line('result.update(paths)')

        fn_gen.add_line(f'return result if dict_factory is dict else dict_factory(result)')

        # with fn_gen.try_():
        #     fn_gen.add_line(f"return cls({init_parts})")
        # with fn_gen.except_(UnboundLocalError):
        #     # raise `MissingFields`, as required dataclass fields
        #     # are not present in the input object `o`.
        #     fn_gen.add_line("raise_missing_fields(locals(), o, cls, fields)")

    # Save the dump function for the main dataclass, so we don't need to run
    # this logic each time.
    if is_main_class:
        # noinspection PyUnboundLocalVariable
        functions = fn_gen.create_functions(_globals)

        cls_todict = functions[fn_name]

        # Check if the class has a `to_dict`, and it's
        # a class method bound to `todict`.
        if ((to_dict := getattr(cls, 'to_dict', None)) is not None
                and getattr(to_dict, '__func__', None) is asdict):

            LOG.debug("setattr(%s, 'to_dict', %s)", cls_name, fn_name)
            _set_new_attribute(cls, 'to_dict', cls_todict)

        _set_new_attribute(
            cls, f'__{PACKAGE_NAME}_to_dict__', cls_todict)
        LOG.debug(
            "setattr(%s, '__%s_to_dict__', %s)",
            cls_name, PACKAGE_NAME, fn_name)

        # TODO in `v1`, we will use class attribute (set above) instead.
        CLASS_TO_DUMP_FUNC[cls] = cls_todict

        return cls_todict


def generate_field_code(cls_dumper: DumpMixin,
                        extras: Extras,
                        field: Field,
                        field_i: int,
                        var_name=None) -> 'str | TypeInfo':

    cls = extras['cls']
    field_type = field.type = eval_forward_ref_if_needed(field.type, cls)

    try:
        return cls_dumper.dump_dispatcher_for_annotation(
            TypeInfo(field_type, field_i=field_i, val_name=var_name), extras
        )

    except ParseError as pe:
        pe.class_name = cls
        pe.field_name = field.name
        raise pe from None


def re_raise(e, cls, o, fields, field, value):
    # If the object `o` is None, then raise an error with
    # the relevant info included.
    if o is None:
      raise MissingData(cls) from None

    add_fields = True
    if type(e) is not ParseError:
        if isinstance(e, JSONWizardError):
            add_fields = False
        else:
            tp = getattr(next((f for f in fields if f.name == field), None), 'type', Any)
            e = ParseError(e, value, tp)

    # We run into a parsing error while dumping the field value;
    # Add additional info on the Exception object before re-raising it.
    #
    # First confirm these values are not already set by an
    # inner dataclass. If so, it likely makes it easier to
    # debug the cause. Note that this should already be
    # handled by the `setter` methods.
    if add_fields:
        e.class_name, e.fields, e.field_name, e.json_object = cls, fields, field, repr(o)
    else:
        e.class_name, e.field_name, e.json_object = cls, field, repr(o)

    raise e from None
