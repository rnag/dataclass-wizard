# TODO cleanup imports

import collections.abc as abc
from base64 import decodebytes
from collections import defaultdict, deque
from dataclasses import is_dataclass, MISSING, Field
from datetime import datetime, time, date, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
# noinspection PyUnresolvedReferences,PyProtectedMember
from typing import (
    Any, Type, Dict, List, Tuple, Iterable, Sequence, Union,
    NamedTupleMeta,
    SupportsFloat, AnyStr, Text, Callable, Optional, cast, Literal, Annotated
)
from uuid import UUID

from .models import Extras, TypeInfo, SIMPLE_TYPES, PatternBase

from ..abstractions import AbstractDumperGenerator
from ..bases import BaseLoadHook, AbstractMeta, BaseDumpHook, META
from ..class_helper import (
    v1_dataclass_field_to_alias, json_field_to_dataclass_field,
    CLASS_TO_LOAD_FUNC, dataclass_fields, get_meta, is_subclass_safe, DATACLASS_FIELD_TO_ALIAS_PATH_FOR_LOAD,
    dataclass_init_fields, dataclass_field_to_default, create_meta, dataclass_init_field_names, CLASS_TO_DUMP_FUNC,
)
from ..constants import CATCH_ALL, TAG, PACKAGE_NAME
from ..decorators import _identity
from .enums import KeyAction, KeyCase
from ..errors import (ParseError, MissingFields, UnknownKeysError,
                      MissingData, JSONWizardError)
from ..loader_selection import get_dumper, asdict
from ..log import LOG

from ..type_def import (
    DefFactory, NoneType, JSONObject,
    PyLiteralString,
    T
)
# noinspection PyProtectedMember
from ..utils.dataclass_compat import _set_new_attribute
from ..utils.function_builder import FunctionBuilder
from ..utils.object_path import safe_get
from ..utils.type_conv import (
    as_bool, as_datetime, as_date, as_time, as_int, as_timedelta,
)
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
    @_identity
    def default_load_to(tp: TypeInfo, extras: Extras) -> str:
        # identity: o
        return tp.v()

    @staticmethod
    def load_after_type_check(tp: TypeInfo, extras: Extras) -> str:
        ...
        # return f'{tp.v()} if instance({tp.v()}, {tp.t()}'

        # if isinstance(o, base_type):
        #     return o
        #
        # e = ValueError(f'data type is not a {base_type!s}')
        # raise ParseError(e, o, base_type)

    @staticmethod
    def dump_from_str(tp: TypeInfo, extras: Extras) -> str:
        # TODO skip None check if in Optional
        # return f'{tp.name}({tp.v()})'
        return f"'' if {(v := tp.v())} is None else {tp.name}({v})"

    @staticmethod
    def dump_from_int(tp: TypeInfo, extras: Extras) -> str:
        # TODO
        extras['locals'].setdefault('as_int', as_int)

        # TODO
        return f"as_int({tp.v()}, {tp.name})"

    @staticmethod
    def dump_from_float(tp: TypeInfo, extras: Extras) -> str:
        # alias: base_type(o)
        return f'{tp.name}({tp.v()})'

    @staticmethod
    def dump_from_bool(tp: TypeInfo, extras: Extras) -> str:
        extras['locals'].setdefault('as_bool', as_bool)
        return f"as_bool({tp.v()})"
        # Uncomment for efficiency!
        # extras['locals']['_T'] = _TRUTHY_VALUES
        # return f'{tp.v()} if (t := type({tp.v()})) is bool else ({tp.v()}.lower() in _T if t is str else {tp.v()} == 1)'

    @staticmethod
    def dump_from_bytes(tp: TypeInfo, extras: Extras) -> str:
        extras['locals'].setdefault('decodebytes', decodebytes)
        return f'decodebytes({tp.v()}.encode())'

    @staticmethod
    def dump_from_bytearray(tp: TypeInfo, extras: Extras) -> str:
        extras['locals'].setdefault('decodebytes', decodebytes)
        return f'{tp.name}(decodebytes({tp.v()}.encode()))'

    @staticmethod
    def dump_from_none(tp: TypeInfo, extras: Extras) -> str:
        return 'None'

    @staticmethod
    def dump_from_enum(tp: TypeInfo, extras: Extras) -> str:
        # alias: base_type(o)
        return tp.v()

    # dump_from_uuid = dump_from_enum
    @staticmethod
    def dump_from_uuid(tp: TypeInfo, extras: Extras):
        # alias: base_type(o)
        return tp.wrap_builtin(tp.v(), extras)

    @classmethod
    def dump_from_iterable(cls, tp: TypeInfo, extras: Extras):
        v, v_next, i_next = tp.v_and_next()
        gorg = tp.origin

        try:
            elem_type = tp.args[0]
        except:
            elem_type = Any

        string = cls.get_string_for_annotation(
            tp.replace(origin=elem_type, i=i_next), extras)

        # TODO
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
            args = (Any, ...)
            is_variadic = True

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

            string = cls.get_string_for_annotation(
                tp.replace(origin=args[0], i=i_next), extras)

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
            force_wrap = True

        else:
            string = ', '.join([
                cls.get_string_for_annotation(
                    tp.replace(origin=arg, index=k),
                    extras)
                for k, arg in enumerate(args)])

            result = f'({string}, )'
            force_wrap = False

        return tp.wrap(result, extras, force=force_wrap)

    @classmethod
    def dump_from_named_tuple(cls, tp: TypeInfo, extras: Extras):

        fn_gen = FunctionBuilder()

        extras_cp: Extras = extras.copy()
        extras_cp['locals'] = _locals = {
            'msg': "`dict` input is not supported for NamedTuple, use a dataclass instead."
        }

        fn_name = f'_load_{extras["cls_name"]}_nt_typed_{tp.name}'

        field_names = []
        result_list = []
        num_fields = 0
        # TODO set __annotations__?
        for x, y in tp.origin.__annotations__.items():
            result_list.append(cls.get_string_for_annotation(
                tp.replace(origin=y, index=num_fields), extras_cp))
            field_names.append(x)
            num_fields += 1

        with fn_gen.function(fn_name, ['v1'], None, _locals):
            fn_gen.add_line('fields = []')
            with fn_gen.try_():
                for i, string in enumerate(result_list):
                    fn_gen.add_line(f'fields.append({string})')
            with fn_gen.except_(IndexError):
                fn_gen.add_line('pass')
            with fn_gen.except_(KeyError):
                # Input object is a `dict`
                # TODO should we support dict for namedtuple?
                fn_gen.add_line('raise TypeError(msg) from None')
            fn_gen.add_line(f'return {tp.wrap("*fields", extras_cp, prefix="nt_")}')

        extras['fn_gen'] |= fn_gen

        return f'{fn_name}({tp.v()})'

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
        tp_k_next = tp.replace(origin=kt, i=i_next, prefix='k')
        string_k = cls.get_string_for_annotation(tp_k_next, extras)

        tp_v_next = tp.replace(origin=vt, i=i_next, prefix='v')
        string_v = cls.get_string_for_annotation(tp_v_next, extras)

        return f'{{{string_k}: {string_v} for {k_next}, {v_next} in {v}.items()}}'

    @classmethod
    def dump_from_dict(cls, tp: TypeInfo, extras: Extras):
        v, k_next, v_next, i_next = tp.v_and_next_k_v()

        try:
            kt, vt = tp.args
        except ValueError:
            # TODO
            kt = vt = Any

        result = cls._build_dict_comp(
            tp, v, i_next, k_next, v_next, kt, vt, extras)

        # TODO
        return tp.wrap(result, extras)

    @classmethod
    def dump_from_defaultdict(cls, tp: TypeInfo, extras: Extras):
        v, k_next, v_next, i_next = tp.v_and_next_k_v()
        default_factory: DefFactory

        try:
            kt, vt = tp.args
            default_factory = getattr(vt, '__origin__', vt)
        except ValueError:
            # TODO
            kt = vt = default_factory = Any

        result = cls._build_dict_comp(
            tp, v, i_next, k_next, v_next, kt, vt, extras)

        return tp.wrap_dd(default_factory, result, extras)

    @classmethod
    def dump_from_typed_dict(cls, tp: TypeInfo, extras: Extras):
        fn_gen = FunctionBuilder()

        req_keys, opt_keys = get_keys_for_typed_dict(tp.origin)

        extras_cp: Extras = extras.copy()
        extras_cp['locals'] = _locals = {}

        fn_name = f'_load_{extras["cls_name"]}_typeddict_{tp.name}'

        result_list = []
        # TODO set __annotations__?
        annotations = tp.origin.__annotations__

        # Set required keys for the `TypedDict`
        for k in req_keys:
            field_tp = annotations[k]
            field_name = repr(k)
            string = cls.get_string_for_annotation(
                tp.replace(origin=field_tp,
                           index=field_name), extras_cp)

            result_list.append(f'{field_name}: {string}')

        with fn_gen.function(fn_name, ['v1'], None, _locals):
            with fn_gen.try_():
                fn_gen.add_lines('result = {',
                                 *(f'  {r},' for r in result_list),
                                 '}')

                # Set optional keys for the `TypedDict` (if they exist)
                for k in opt_keys:
                    field_tp = annotations[k]
                    field_name = repr(k)
                    string = cls.get_string_for_annotation(
                        tp.replace(origin=field_tp,
                                   i=2), extras_cp)
                    with fn_gen.if_(f'(v2 := v1.get({field_name}, MISSING)) is not MISSING'):
                        fn_gen.add_line(f'result[{field_name}] = {string}')
                fn_gen.add_line('return result')
            with fn_gen.except_(Exception, 'e'):
                with fn_gen.if_('type(e) is KeyError'):
                    fn_gen.add_line('name = e.args[0]; e = KeyError(f"Missing required key: {name!r}")')
                with fn_gen.elif_('not isinstance(v1, dict)'):
                    fn_gen.add_line('e = TypeError("Incorrect type for object")')
                fn_gen.add_line('raise ParseError(e, v1, {}) from None')

        extras['fn_gen'] |= fn_gen

        return f'{fn_name}({tp.v()})'

    @classmethod
    def dump_from_union(cls, tp: TypeInfo, extras: Extras):
        fn_gen = FunctionBuilder()
        config = extras['config']

        tag_key = config.tag_key or TAG
        auto_assign_tags = config.auto_assign_tags

        fields = f'fields_{tp.field_i}'

        extras_cp: Extras = extras.copy()
        extras_cp['locals'] = _locals = {
            fields: tp.args,
            'tag_key': tag_key,
        }

        actual_cls = extras['cls']

        fn_name = f'dump_from_{extras["cls_name"]}_union_{tp.field_i}'

        # TODO handle dataclasses in union (tag)

        with fn_gen.function(fn_name, ['v1'], None, _locals):

            dataclass_tag_to_lines: dict[str, list] = {}

            type_checks = []
            try_parse_at_end = []

            for possible_tp in tp.args:

                possible_tp = eval_forward_ref_if_needed(possible_tp, actual_cls)

                tp_new = TypeInfo(possible_tp, field_i=tp.field_i)

                if possible_tp is NoneType:
                    with fn_gen.if_('v1 is None'):
                        fn_gen.add_line('return None')
                    continue

                if is_dataclass(possible_tp):
                    # we see a dataclass in `Union` declaration
                    meta = get_meta(possible_tp)
                    tag = meta.tag
                    assign_tags_to_cls = auto_assign_tags or meta.auto_assign_tags
                    cls_name = possible_tp.__name__

                    if assign_tags_to_cls and not tag:
                        tag = cls_name
                        # We don't want to mutate the base Meta class here
                        if meta is AbstractMeta:
                            create_meta(possible_tp, cls_name, tag=tag)
                        else:
                            meta.tag = cls_name

                    if tag:
                        string = cls.get_string_for_annotation(tp_new, extras_cp)

                        dataclass_tag_to_lines[tag] = [
                            f'if tag == {tag!r}:',
                            f'  return {string}'
                        ]
                        continue

                    elif not config.v1_unsafe_parse_dataclass_in_union:
                        e = ValueError(f'Cannot parse dataclass types in a Union without one of the following `Meta` settings:\n\n'
                                       '  * `auto_assign_tags = True`\n'
                                      f'    - Set on class `{extras["cls_name"]}`.\n\n'
                                      f'  * `tag = "{cls_name}"`\n'
                                      f'    - Set on class `{possible_tp.__qualname__}`.\n\n'
                                       '  * `v1_unsafe_parse_dataclass_in_union = True`\n'
                                      f'    - Set on class `{extras["cls_name"]}`\n\n'
                                       'For more information, refer to:\n'
                                       '  https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/dataclasses_in_union_types.html')
                        raise e from None

                string = cls.get_string_for_annotation(tp_new, extras_cp)

                try_parse_lines = [
                    'try:',
                   f'  return {string}',
                    'except Exception:',
                    '  pass',
                ]

                # TODO disable for dataclasses

                if possible_tp in SIMPLE_TYPES or is_subclass_safe(get_origin_v2(possible_tp), SIMPLE_TYPES):
                    tn = tp_new.type_name(extras_cp)
                    type_checks.extend([
                        f'if tp is {tn}:',
                        '  return v1'
                    ])
                    list_to_add = try_parse_at_end
                else:
                    list_to_add = type_checks

                list_to_add.extend(try_parse_lines)

            if dataclass_tag_to_lines:

                with fn_gen.try_():
                    fn_gen.add_line(f'tag = v1[tag_key]')

                with fn_gen.except_(Exception):
                    fn_gen.add_line('pass')

                with fn_gen.else_():

                    for lines in dataclass_tag_to_lines.values():
                        fn_gen.add_lines(*lines)

                    fn_gen.add_line(
                        "raise ParseError("
                        "TypeError('Object with tag was not in any of Union types'),"
                       f"v1,{fields},"
                        "input_tag=tag,"
                        "tag_key=tag_key,"
                       f"valid_tags={list(dataclass_tag_to_lines)})"
                    )

            fn_gen.add_line('tp = type(v1)')

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

        extras['fn_gen'] |= fn_gen

        return f'{fn_name}({tp.v()})'

    @staticmethod
    def dump_from_literal(tp: TypeInfo, extras: Extras):
        fn_gen = FunctionBuilder()

        fields = f'fields_{tp.field_i}'

        extras_cp: Extras = extras.copy()
        extras_cp['locals'] = _locals = {
            fields: frozenset(tp.args),
        }

        fn_name = f'dump_from_{extras["cls_name"]}_literal_{tp.field_i}'

        with fn_gen.function(fn_name, ['v1'], None, _locals):

            with fn_gen.if_(f'{tp.v()} in {fields}'):
                fn_gen.add_line('return v1')

            # No such Literal with the value of `o`
            fn_gen.add_line("e = ValueError('Value not in expected Literal values')")
            fn_gen.add_line(f'raise ParseError(e, v1, {fields}, '
                            f'allowed_values=list({fields}))')

        # TODO Checks for Literal equivalence, as mentioned here:
        #   https://www.python.org/dev/peps/pep-0586/#equivalence-of-two-literals

        # extras_cp['locals'][fields] = {
        #     a: type(a) for a in tp.args
        # }
        #
        # with fn_gen.function(fn_name, ['v1'], None, _locals):
        #
        #     with fn_gen.try_():
        #         with fn_gen.if_(f'type({tp.v()}) is {fields}[{tp.v()}]'):
        #             fn_gen.add_line('return v1')
        #
        #         # The value of `o` is in the ones defined for the Literal, but
        #         # also confirm the type matches the one defined for the Literal.
        #         fn_gen.add_line("e = TypeError('Value did not match expected type for the Literal')")
        #
        #         fn_gen.add_line('raise ParseError('
        #                         f'e, v1, {fields}, '
        #                         'have_type=type(v1), '
        #                         f'desired_type={fields}[v1], '
        #                         f'desired_value=next(v for v in {fields} if v == v1), '
        #                         f'allowed_values=list({fields})'
        #                         ')')
        #     with fn_gen.except_(KeyError):
        #         # No such Literal with the value of `o`
        #         fn_gen.add_line("e = ValueError('Value not in expected Literal values')")
        #         fn_gen.add_line('raise ParseError('
        #                         f'e, v1, {fields}, allowed_values=list({fields})'
        #                         f')')

        extras['fn_gen'] |= fn_gen

        return f'{fn_name}({tp.v()})'

    @staticmethod
    def dump_from_decimal(tp: TypeInfo, extras: Extras):
        s = f'str({tp.v()}) if isinstance({tp.v()}, float) else {tp.v()}'
        return tp.wrap_builtin(s, extras)

    # alias: base_type(o)
    dump_from_path = dump_from_uuid

    @staticmethod
    def dump_from_datetime(tp: TypeInfo, extras: Extras):
        # alias: as_datetime
        tp.ensure_in_locals(extras, as_datetime, datetime)
        return f'as_datetime({tp.v()}, {tp.name})'

    @staticmethod
    def dump_from_time(tp: TypeInfo, extras: Extras):
        # alias: as_time
        tp.ensure_in_locals(extras, as_time, time)
        return f'as_time({tp.v()}, {tp.name})'

    @staticmethod
    def dump_from_date(tp: TypeInfo, extras: Extras):
        # alias: as_date
        tp.ensure_in_locals(extras, as_date, date)
        return f'as_date({tp.v()}, {tp.name})'

    @staticmethod
    def dump_from_timedelta(tp: TypeInfo, extras: Extras):
        # alias: as_timedelta
        tp.ensure_in_locals(extras, as_timedelta, timedelta)
        return f'as_timedelta({tp.v()}, {tp.name})'

    @staticmethod
    def dump_from_dataclass(tp: TypeInfo, extras: Extras):
        fn_name = dump_func_for_dataclass(
            tp.origin, extras, False)

        return f'{fn_name}({tp.v()})'

    @classmethod
    def get_string_for_annotation(cls,
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
            load_hook = cls.load_to_str
            origin = str
            name = 'str'

        # -> Atomic, immutable types which don't require
        #    any iterative / recursive handling.
        elif origin in SIMPLE_TYPES or is_subclass_safe(origin, SIMPLE_TYPES):
            load_hook = hooks.get(origin)

        elif (load_hook := hooks.get(origin)) is not None:
            try:
                args = get_args(type_ann)
            except ValueError:
                args = Any,

        # -> Union[x]
        elif is_union(origin):
            load_hook = cls.load_to_union
            args = get_args(type_ann)

            # Special case for Optional[x], which is actually Union[x, None]
            if len(args) == 2 and NoneType in args:
                new_tp = tp.replace(origin=args[0], args=None, name=None)
                new_tp.in_optional = True

                string = cls.get_string_for_annotation(new_tp, extras)

                return f'None if {tp.v()} is None else {string}'

        # -> Literal[X, Y, ...]
        elif origin is Literal:
            load_hook = cls.load_to_literal
            args = get_args(type_ann)

        # https://stackoverflow.com/questions/76520264/dataclasswizard-after-upgrading-to-python3-11-is-not-working-as-expected
        elif origin is Any:
            load_hook = cls.default_load_to

        elif is_subclass_safe(origin, tuple) and hasattr(origin, '_fields'):

            if getattr(origin, '__annotations__', None):
                # Annotated as a `typing.NamedTuple` subtype
                load_hook = cls.load_to_named_tuple
            else:
                # Annotated as a `collections.namedtuple` subtype
                load_hook = cls.load_to_named_tuple_untyped

        elif is_typed_dict(origin):
            load_hook = cls.load_to_typed_dict

        elif is_dataclass(origin):
            # return a dynamically generated `fromdict`
            # for the `cls` (base_type)
            load_hook = cls.load_to_dataclass

        elif is_subclass_safe(origin, Enum):
            load_hook = cls.load_to_enum

        elif origin in (abc.Sequence, abc.MutableSequence, abc.Collection):
            if origin is abc.Sequence:
                load_hook = cls.load_to_tuple
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
                load_hook = cls.load_to_iterable
                # desired (non-generic) origin type
                name = 'list'
                origin = list
                # Get type arguments, e.g. `Sequence[int]` -> `int`
                try:
                    args = get_args(type_ann)
                except ValueError:
                    args = Any,

        elif isinstance(origin, PatternBase):
            load_hook = origin.load_to_pattern

        else:

            # TODO everything should use `get_origin_v2`
            try:
                args = get_args(type_ann)
            except ValueError:
                args = Any,

        if load_hook is None:
            # TODO END
            for t in hooks:
                if issubclass(origin, (t,)):
                    load_hook = hooks[t]
                    break

        tp.origin = origin
        tp.args = args
        tp.name = name

        if load_hook is not None:
            result = load_hook(tp, extras)
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

    missing_keys = [v1_dataclass_field_to_alias(cls)[field]
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
    fields = dataclass_fields(cls)

    cls_init_fields = dataclass_init_fields(cls, True)
    cls_init_field_names = dataclass_init_field_names(cls)

    field_to_default = dataclass_field_to_default(cls)

    has_defaults = True if field_to_default else False

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
            'fields': fields,
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
        new_locals['fields'] = fields

        # TODO need a way to auto-magically do this
        extras['cls'] = cls
        extras['cls_name'] = cls_name

    key_case: KeyCase | None = cls_dumper.transform_dataclass_field

    field_to_aliases = v1_dataclass_field_to_alias(cls)
    check_aliases = True if field_to_aliases else False

    field_to_path = DATACLASS_FIELD_TO_ALIAS_PATH_FOR_LOAD[cls]
    has_alias_paths = True if field_to_path else False

    # Fix for using `auto_assign_tags` and `raise_on_unknown_json_key` together
    # See https://github.com/rnag/dataclass-wizard/issues/137
    has_tag_assigned = meta.tag is not None
    if (has_tag_assigned and
        # Ensure `tag_key` isn't a dataclass field,
        # to avoid issues with our logic.
        # See https://github.com/rnag/dataclass-wizard/issues/148
        meta.tag_key not in cls_init_field_names):
            expect_tag_as_unknown_key = True
    else:
        expect_tag_as_unknown_key = False

    on_unknown_key = meta.v1_on_unknown_key

    catch_all_field = field_to_aliases.pop(CATCH_ALL, None)
    has_catch_all = catch_all_field is not None

    if has_catch_all:
        pre_assign = 'i+=1; '
        catch_all_field_stripped = catch_all_field.rstrip('?')
        catch_all_idx = cls_init_field_names.index(catch_all_field_stripped)
        # remove catch all field from list, so we don't iterate over it
        del cls_init_fields[catch_all_idx]
    else:
        pre_assign = ''
        catch_all_field_stripped = catch_all_idx = None

    if on_unknown_key is not None:
        should_raise = on_unknown_key is KeyAction.RAISE
        should_warn = on_unknown_key is KeyAction.WARN
        if should_warn or should_raise:
            pre_assign = 'i+=1; '
    else:
        should_raise = should_warn = None

    cls_name = cls.__name__

    with fn_gen.function(
            fn_name, [
            'o',
            'dict_factory=dict',
            'exclude=None',
        ], MISSING, new_locals):

        if (_pre_to_dict := getattr(cls, '_pre_to_dict', None)) is not None:
            new_locals['__pre_to_dict__'] = _pre_to_dict
            fn_gen.add_line('o = __pre_to_dict__(o)')

        # Need to create a separate dictionary to copy over the constructor
        # args, as we don't want to mutate the original dictionary object.
        if has_defaults:
            fn_gen.add_line('init_kwargs = {}')
        if pre_assign:
            fn_gen.add_line('i = 0')

        vars_for_fields = []

        if cls_init_fields:

            with fn_gen.try_():

                # if expect_tag_as_unknown_key and pre_assign:
                #     with fn_gen.if_(f'{meta.tag_key!r} in o'):
                #         fn_gen.add_line('i+=1')

                for i, f in enumerate(cls_init_fields):
                    val = 'v1'
                    name = f.name
                    var = f'__{name}'

                    if (check_aliases
                            and (key := field_to_aliases.get(name)) is not None
                            and name != key):
                        f_assign = f'field={name!r}; key={key!r}; {val}=o.{name}'

                    elif (has_alias_paths
                            and (path := field_to_path.get(name)) is not None):

                        if name in field_to_default:
                            f_assign = f'field={name!r}; {val}=safe_get(o, {path!r}, MISSING, False)'
                        else:
                            f_assign = f'field={name!r}; {val}=safe_get(o, {path!r})'

                        # TODO raise some useful message like (ex. on IndexError):
                        #       Field "my_str" of type tuple[float, str] in A2 has invalid value ['123']

                    elif key_case is None:
                        field_to_aliases[name] = name
                        f_assign = f'field={name!r}; {val}=o.{name}'
                    elif key_case is KeyCase.AUTO:
                        f_assign = f'field={name!r}; key=f2k.get(field); {val}=o.{name}'
                    else:
                        field_to_aliases[name] = key = key_case(name)
                        f_assign = f'field={name!r}; key={key!r}; {val}=o.{name}'

                    string = generate_field_code(cls_dumper, extras, f, i)

                    if name in field_to_default:
                        fn_gen.add_line(f_assign)

                        #with fn_gen.if_(f'{val} is not MISSING'):
                        fn_gen.add_line(f'{pre_assign}init_kwargs[field] = {string}')

                    else:
                        # TODO confirm this is ok
                        # vars_for_fields.append(f'{name}={var}')
                        vars_for_fields.append(var)
                        fn_gen.add_line(f_assign)

                        with fn_gen.if_(f'{val} is not MISSING'):
                            fn_gen.add_line(f'{pre_assign}{var} = {string}')

            # create a broad `except Exception` block, as we will be
            # re-raising all exception(s) as a custom `ParseError`.
            with fn_gen.except_(Exception, 'e', ParseError):
                fn_gen.add_line("re_raise(e, cls, o, fields, field, locals().get('v1'))")

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

        if has_defaults:
            vars_for_fields.append('**init_kwargs')

        init_parts = ', '.join(vars_for_fields)
        fn_gen.add_line(f"return dict_factory({init_parts})")

        # with fn_gen.try_():
        #     fn_gen.add_line(f"return cls({init_parts})")
        # with fn_gen.except_(UnboundLocalError):
        #     # raise `MissingFields`, as required dataclass fields
        #     # are not present in the input object `o`.
        #     fn_gen.add_line("raise_missing_fields(locals(), o, cls, fields)")

    # Save the load function for the main dataclass, so we don't need to run
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
                        field_i: int) -> 'str | TypeInfo':

    cls = extras['cls']
    field_type = field.type = eval_forward_ref_if_needed(field.type, cls)

    try:
        return cls_dumper.get_string_for_annotation(
            TypeInfo(field_type, field_i=field_i), extras
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

    # Check if the object `o` is some other type than what we expect -
    # for example, we could be passed in a `list` type instead.
    if not isinstance(o, dict):
      base_err = TypeError('Incorrect type for `to_dict()`')
      e = ParseError(base_err, o, dict, cls, desired_type=dict)

    add_fields = True
    if type(e) is not ParseError:
        if isinstance(e, JSONWizardError):
            add_fields = False
        else:
            tp = getattr(next((f for f in fields if f.name == field), None), 'type', Any)
            e = ParseError(e, value, tp)

    # We run into a parsing error while loading the field value;
    # Add additional info on the Exception object before re-raising it.
    #
    # First confirm these values are not already set by an
    # inner dataclass. If so, it likely makes it easier to
    # debug the cause. Note that this should already be
    # handled by the `setter` methods.
    if add_fields:
        e.class_name, e.fields, e.field_name, e.json_object = cls, fields, field, o
    else:
        e.class_name, e.field_name, e.json_object = cls, field, o

    raise e from None
