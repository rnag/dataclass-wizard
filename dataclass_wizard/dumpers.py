"""
The implementation below uses code adapted from the `asdict` helper function
from the library Dataclasses (https://github.com/ericvsmith/dataclasses).

This library is available under the Apache 2.0 license, which can be
obtained from http://www.apache.org/licenses/LICENSE-2.0.


See the end of this file for the original Apache license from this library.
"""
from base64 import b64encode
from collections import defaultdict, deque
# noinspection PyProtectedMember,PyUnresolvedReferences
from dataclasses import _is_dataclass_instance
from datetime import datetime, time, date, timedelta
from decimal import Decimal
from enum import Enum
# noinspection PyProtectedMember,PyUnresolvedReferences
from typing import Type, List, Dict, Any, NamedTupleMeta, Optional, Callable, Collection
from uuid import UUID

from .abstractions import AbstractDumper
from .bases import BaseDumpHook, AbstractMeta, META
from .class_helper import (
    create_new_class,
    dataclass_field_names, dataclass_field_to_default,
    dataclass_field_to_json_field,
    dataclass_to_dumper, set_class_dumper,
    CLASS_TO_DUMP_FUNC, setup_dump_config_for_cls_if_needed, get_meta,
    dataclass_field_to_load_parser, dataclass_field_to_json_path, is_builtin, dataclass_field_to_skip_if,
    v1_dataclass_field_to_alias,
)
from .constants import _DUMP_HOOKS, TAG, CATCH_ALL
from .decorators import _alias
from .errors import show_deprecation_warning
from .loader_selection import _get_load_fn_for_dataclass
from .log import LOG
from .models import get_skip_if_condition, finalize_skip_if
from .type_def import (
    Buffer, ExplicitNull, NoneType, JSONObject,
    DD, LSQ, E, U, LT, NT, T
)
from .utils.dict_helper import NestedDict
from .utils.function_builder import FunctionBuilder
# noinspection PyProtectedMember
from .utils.dataclass_compat import _set_new_attribute
from .utils.string_conv import to_camel_case


class DumpMixin(AbstractDumper, BaseDumpHook):
    """
    This Mixin class derives its name from the eponymous `json.dumps`
    function. Essentially it contains helper methods to convert Python
    built-in types to a more 'JSON-friendly' version.

    """
    __slots__ = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        setup_default_dumper(cls)

    @staticmethod
    @_alias(to_camel_case)
    def transform_dataclass_field(string: str) -> str:
        # alias: to_camel_case
        ...

    @staticmethod
    def default_dump_with(o, *_):
        return str(o)

    @staticmethod
    def dump_with_null(o: None, *_):
        return o

    @staticmethod
    def dump_with_str(o: str, *_):
        return o

    @staticmethod
    def dump_with_bytes(o: Buffer, *_) -> str:
        return b64encode(o).decode()

    @staticmethod
    def dump_with_int(o: int, *_):
        return o

    @staticmethod
    def dump_with_float(o: float, *_):
        return o

    @staticmethod
    def dump_with_bool(o: bool, *_):
        return o

    @staticmethod
    def dump_with_enum(o: E, *_):
        return o.value

    @staticmethod
    def dump_with_uuid(o: U, *_):
        return o.hex

    @staticmethod
    def dump_with_list_or_tuple(o: LT, typ: Type[LT], *args):

        return typ(_asdict_inner(v, *args) for v in o)

    @staticmethod
    def dump_with_iterable(o: LSQ, _typ: Type[LSQ], *args):

        return list(_asdict_inner(v, *args) for v in o)

    @staticmethod
    def dump_with_named_tuple(o: NT, typ: Type[NT], *args):

        return typ(*[_asdict_inner(v, *args) for v in o])

    @staticmethod
    def dump_with_dict(o: Dict, typ: Type[Dict], *args):

        return typ((_asdict_inner(k, *args),
                    _asdict_inner(v, *args))
                   for k, v in o.items())

    @staticmethod
    def dump_with_defaultdict(o: DD, _typ: Type[DD], *args):

        return {_asdict_inner(k, *args):
                _asdict_inner(v, *args)
                for k, v in o.items()}

    @staticmethod
    def dump_with_decimal(o: Decimal, *_):
        return str(o)

    @staticmethod
    def dump_with_datetime(o: datetime, *_):
        return o.isoformat().replace('+00:00', 'Z', 1)

    @staticmethod
    def dump_with_time(o: time, *_):
        return o.isoformat().replace('+00:00', 'Z', 1)

    @staticmethod
    def dump_with_date(o: date, *_):
        return o.isoformat()

    @staticmethod
    def dump_with_timedelta(o: timedelta, *_):
        return str(o)


def setup_default_dumper(cls=DumpMixin):
    """
    Setup the default type hooks to use when converting `dataclass` instances
    to `str` (json)

    Note: `cls` must be :class:`DumpMixin` or a sub-class of it.
    """
    # Simple types
    cls.register_dump_hook(str, cls.dump_with_str)
    cls.register_dump_hook(int, cls.dump_with_int)
    cls.register_dump_hook(float, cls.dump_with_float)
    cls.register_dump_hook(bool, cls.dump_with_bool)
    cls.register_dump_hook(bytes, cls.dump_with_bytes)
    cls.register_dump_hook(bytearray, cls.dump_with_bytes)
    cls.register_dump_hook(NoneType, cls.dump_with_null)
    # Complex types
    cls.register_dump_hook(Enum, cls.dump_with_enum)
    cls.register_dump_hook(UUID, cls.dump_with_uuid)
    cls.register_dump_hook(set, cls.dump_with_iterable)
    cls.register_dump_hook(frozenset, cls.dump_with_iterable)
    cls.register_dump_hook(deque, cls.dump_with_iterable)
    cls.register_dump_hook(list, cls.dump_with_list_or_tuple)
    cls.register_dump_hook(tuple, cls.dump_with_list_or_tuple)
    cls.register_dump_hook(NamedTupleMeta, cls.dump_with_named_tuple)
    cls.register_dump_hook(defaultdict, cls.dump_with_defaultdict)
    cls.register_dump_hook(dict, cls.dump_with_dict)
    cls.register_dump_hook(Decimal, cls.dump_with_decimal)
    # Dates and times
    cls.register_dump_hook(datetime, cls.dump_with_datetime)
    cls.register_dump_hook(time, cls.dump_with_time)
    cls.register_dump_hook(date, cls.dump_with_date)
    cls.register_dump_hook(timedelta, cls.dump_with_timedelta)


def get_dumper(cls=None, create=True) -> Type[DumpMixin]:
    """
    Get the dumper for the class, using the following logic:

        * Return the class if it's already a sub-class of :class:`DumpMixin`
        * If `create` is enabled (which is the default), a new sub-class of
          :class:`DumpMixin` for the class will be generated and cached on the
          initial run.
        * Otherwise, we will return the base dumper, :class:`DumpMixin`, which
          can potentially be shared by more than one dataclass.

    """
    try:
        return dataclass_to_dumper(cls)

    except KeyError:

        if hasattr(cls, _DUMP_HOOKS):
            return set_class_dumper(cls, cls)

        elif create:
            cls_dumper = create_new_class(cls, (DumpMixin, ))
            return set_class_dumper(cls, cls_dumper)

        return set_class_dumper(cls, DumpMixin)


def asdict(o: T,
           *, cls=None,
           dict_factory=dict,
           exclude: 'Collection[str] | None' = None,
           **kwargs) -> JSONObject:
    # noinspection PyUnresolvedReferences
    """Return the fields of a dataclass instance as a new dictionary mapping
    field names to field values.

    Example usage:

      @dataclass
      class C:
          x: int
          y: int

      c = C(1, 2)
      assert asdict(c) == {'x': 1, 'y': 2}

    When directly invoking this function, an optional Meta configuration for
    the dataclass can be specified via ``DumpMeta``; by default, this will
    apply recursively to any nested dataclasses. Here's a sample usage of this
    below::

        >>> DumpMeta(key_transform='CAMEL').bind_to(MyClass)
        >>> asdict(MyClass(my_str="value"))

    If given, 'dict_factory' will be used instead of built-in dict.
    The function applies recursively to field values that are
    dataclass instances. This will also look into built-in containers:
    tuples, lists, and dicts.
    """
    # This likely won't be needed, as ``dataclasses.fields`` already has this
    # check.
    # if not _is_dataclass_instance(obj):
    #     raise TypeError("asdict() should be called on dataclass instances")

    cls = cls or type(o)

    try:
        dump = CLASS_TO_DUMP_FUNC[cls]
    except KeyError:
        dump = dump_func_for_dataclass(cls)

    return dump(o, dict_factory, exclude, **kwargs)


def dump_func_for_dataclass(cls: Type[T],
                            config: Optional[META] = None,
                            nested_cls_to_dump_func: Dict[Type, Any] = None,
                            ) -> Callable[[T, Any, Any, Any], JSONObject]:

    # TODO dynamically generate for multiple nested classes at once

    # Get the dumper for the class, or create a new one as needed.
    cls_dumper = get_dumper(cls)

    # Get the meta config for the class, or the default config otherwise.
    meta = get_meta(cls)

    # Check if we're being run for the main dataclass or for a nested one.
    is_main_class = nested_cls_to_dump_func is None

    if is_main_class:  # we are being run for the main dataclass
        nested_cls_to_dump_func = {}
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

    # This contains the dump hooks for the dataclass. If the class
    # sub-classes from `DumpMixIn`, these hooks could be customized.
    hooks = cls_dumper.__DUMP_HOOKS__

    # TODO this is temporary
    if meta.v1:
        _ = v1_dataclass_field_to_alias(cls)
    # Set up the initial dump config for the dataclass.
    setup_dump_config_for_cls_if_needed(cls)

    # A cached mapping of each dataclass field to the resolved key name in a
    # JSON or dictionary object; useful so we don't need to do a case
    # transformation (via regex) each time.
    dataclass_to_json_field = dataclass_field_to_json_field(cls)

    # A cached mapping of dataclass field name to its default value, either
    # via a `default` or `default_factory` argument.
    field_to_default = dataclass_field_to_default(cls)

    # A cached mapping of dataclass field name to its SkipIf condition.
    field_to_skip_if = dataclass_field_to_skip_if(cls)

    # A collection of field names in the dataclass.
    field_names = dataclass_field_names(cls)

    # Check if we need to auto-assign tags for dataclasses in `Union` types.
    if meta.auto_assign_tags:
        # Unfortunately, we can't handle this as part of the dump process, as
        # we don't process the class annotations here. So instead, generate
        # the load parser for each field  (if needed), but don't cache the
        # result, as it's conceivable we might yet call `LoadMeta` later.
        from .loader_selection import get_loader

        if meta.v1:
            # TODO there must be a better way to do this,
            #   this is just a temporary workaround.
            try:
                _ = _get_load_fn_for_dataclass(cls, v1=True)
            except Exception:
                pass
        else:
            cls_loader = get_loader(cls, v1=meta.v1)
            # Use the cached result if it exists, but don't cache it ourselves.
            _ = dataclass_field_to_load_parser(
                cls_loader, cls, config, save=False)

    # Tag key to populate when a dataclass is in a `Union` with other types.
    tag_key = meta.tag_key or TAG

    catch_all_field = dataclass_to_json_field.get(CATCH_ALL)
    has_catch_all = catch_all_field is not None

    field_to_path = dataclass_field_to_json_path(cls)
    num_paths = len(field_to_path)
    has_json_paths = True if num_paths else False

    skip_defaults = True if meta.skip_defaults or meta.skip_defaults_if else False

    _locals = {
        'config': config,
        'asdict': _asdict_inner,
        'hooks': hooks,
        'cls_to_asdict': nested_cls_to_dump_func,
    }

    _globals = {}

    skip_if_condition = get_skip_if_condition(
        meta.skip_if, _locals, '_skip_value')

    skip_defaults_if_condition = get_skip_if_condition(
        meta.skip_defaults_if, _locals, '_skip_defaults_value')

    # Initialize FuncBuilder
    fn_gen = FunctionBuilder()

    # Code for `cls_asdict`
    with fn_gen.function('cls_asdict',
                         ['o',
                          'dict_factory=dict',
                          "exclude:'list[str]|None'=None",
                          f'skip_defaults:bool={skip_defaults}'],
                         'JSONObject',
                         _locals):

        if (
            _pre_dict := getattr(cls, '_pre_dict', None)
        ) is not None:
            # class defines a `_pre_dict()`
            _locals['__pre_dict__'] = _pre_dict
            fn_gen.add_line('__pre_dict__(o)')
        elif (
            _pre_dict := getattr(cls_dumper, '__pre_as_dict__', None)
        ) is not None:
            # deprecated since v0.28.0
            # subclass of `DumpMixin` defines a `__pre_as_dict__()`
            reason = "use `_pre_dict` instead - no need to subclass from DumpMixin"
            show_deprecation_warning(_pre_dict, reason)

            _locals['__pre_dict__'] = _pre_dict

            # Call the optional hook that runs before we process the dataclass
            fn_gen.add_line('__pre_dict__(o)')

        # Initialize result list to hold field mappings
        fn_gen.add_line("result = []")

        if has_json_paths:
            _locals['NestedDict'] = NestedDict
            fn_gen.add_line('paths = NestedDict()')

        if field_names:

            skip_field_assignments = []
            exclude_assignments = []
            skip_default_assignments = []
            field_assignments = []

            # Loop over the dataclass fields
            for i, field in enumerate(field_names):
                skip_field = f'_skip_{i}'
                skip_if_field = f'_skip_if_{i}'
                default_value = f'_default_{i}'

                skip_field_assignments.append(skip_field)
                exclude_assignments.append(
                    f'{skip_field}={field!r} in exclude'
                )
                if field in field_to_default:
                    if skip_defaults_if_condition:
                        _final_skip_if = finalize_skip_if(
                            meta.skip_defaults_if, f'o.{field}', skip_defaults_if_condition)
                        skip_default_assignments.append(
                            f"{skip_field} = {skip_field} or {_final_skip_if}"
                        )
                    else:
                        _locals[default_value] = field_to_default[field]
                        skip_default_assignments.append(
                            f"{skip_field} = {skip_field} or o.{field} == {default_value}"
                        )

                # Get the resolved JSON field name
                try:
                    json_field = dataclass_to_json_field[field]
                except KeyError:
                    # Normalize the dataclass field name (by default to camel
                    # case)
                    json_field = cls_dumper.transform_dataclass_field(field)
                    dataclass_to_json_field[field] = json_field

                # Exclude any dataclass fields that are explicitly ignored.
                if json_field is not ExplicitNull:
                    # If field has an explicit `SkipIf` condition
                    if field in field_to_skip_if:
                        _skip_condition = field_to_skip_if[field]
                        _skip_if = get_skip_if_condition(
                            _skip_condition, _locals, skip_if_field)
                        _final_skip_if = finalize_skip_if(
                            _skip_condition, f'o.{field}', _skip_if)
                        field_assignments.append(f'if not ({skip_field} or {_final_skip_if}):')
                    # If Meta `skip_if` has a value
                    elif skip_if_condition:
                        _final_skip_if = finalize_skip_if(
                            meta.skip_if, f'o.{field}', skip_if_condition)
                        field_assignments.append(f'if not ({skip_field} or {_final_skip_if}):')
                    # Else, proceed as normal
                    else:
                        field_assignments.append(f"if not {skip_field}:")

                    if json_field:
                        field_assignments.append(f"  result.append(('{json_field}',"
                                                 f"asdict(o.{field},dict_factory,hooks,config,cls_to_asdict)))")
                    # Empty string, will be the case for a dataclass
                    # field which specifies a "JSON Path".
                    else:
                        path = field_to_path[field]
                        key_part = ''.join(f'[{p!r}]' for p in path)
                        field_assignments.append(
                            f'  paths{key_part} = asdict(o.{field},dict_factory,hooks,config,cls_to_asdict)')

                elif has_catch_all and catch_all_field == field:
                    if field in field_to_default:
                        field_assignments.append(f"if o.{field} != {default_value} and not {skip_field}:")
                    else:
                        field_assignments.append(f"if not {skip_field}:")
                    field_assignments.append(f"  for k, v in o.{field}.items():")
                    field_assignments.append("    result.append((k,"
                                             "asdict(v,dict_factory,hooks,config,cls_to_asdict)))")

            with fn_gen.if_('exclude is None'):
                fn_gen.add_line('='.join(skip_field_assignments) + '=False')
            with fn_gen.else_():
                fn_gen.add_line(';'.join(exclude_assignments))

            if skip_default_assignments:
                with fn_gen.if_('skip_defaults'):
                    fn_gen.add_lines(*skip_default_assignments)

            fn_gen.add_lines(*field_assignments)

        if has_json_paths:
            fn_gen.add_line("result and paths.update(result); result = paths")

        # Return the final dictionary result
        if meta.tag:
            fn_gen.add_line("result = dict_factory(result)")
            fn_gen.add_line(f"result[{tag_key!r}] = {meta.tag!r}")
            # Return the result with the tag added
            fn_gen.add_line("return result")
        else:
            fn_gen.add_line("return dict_factory(result)")

    # Compile the code into a dynamic string
    functions = fn_gen.create_functions(_globals)

    cls_asdict = functions['cls_asdict']

    asdict_func = cls_asdict

    # In any case, save the dump function for the class, so we don't need to
    # run this logic each time.
    if is_main_class:
        # Check if the class has a `to_dict`, and it's
        # equivalent to `asdict`.
        if getattr(cls, 'to_dict', None) is asdict:
            _set_new_attribute(cls, 'to_dict', asdict_func)
        CLASS_TO_DUMP_FUNC[cls] = asdict_func
    else:
        nested_cls_to_dump_func[cls] = asdict_func

    return asdict_func


# NOTE: This method has been modified to accept `hook` and `meta` arguments,
# and the return type has been annotated as `Any`. The logic inside this
# method has also been heavily modified from the original implementation in
# `dataclasses`. However, I will call out specific lines where it is taken
# directly from the original version.
def _asdict_inner(obj, dict_factory, hooks, meta, cls_to_dump_func,
                  # Added for `EnvWizard` (environ/dumpers.py)
                  dump_func_for_cls=dump_func_for_dataclass) -> Any:

    cls = type(obj)
    dump_hook = hooks.get(cls)
    hook_args = (obj, cls, dict_factory, hooks, meta, cls_to_dump_func)

    if dump_hook is not None:
        return dump_hook(*hook_args)

    if _is_dataclass_instance(obj):
        try:
            dump = cls_to_dump_func[cls]
        except KeyError:
            dump = dump_func_for_cls(cls, meta, cls_to_dump_func)
        # noinspection PyArgumentList
        return dump(obj, dict_factory=dict_factory)

    else:

        # -- The following `if` condition and comments are the same as in the original version --
        if isinstance(obj, tuple) and hasattr(obj, '_fields'):
            # obj is a namedtuple.  Recurse into it, but the returned
            # object is another namedtuple of the same type.  This is
            # similar to how other list- or tuple-derived classes are
            # treated (see below), but we just need to create them
            # differently because a namedtuple's __init__ needs to be
            # called differently (see bpo-34363).
            dump_hook = hooks[NamedTupleMeta]

        else:
            for t in hooks:
                if isinstance(obj, t):
                    # cache the hook for the subtype, so that next time this
                    # logic isn't run again.
                    dump_hook = hooks[cls] = hooks[t]
                    break
            else:
                LOG.warning('Using default dumper, object=%r, type=%r', obj, cls)

                # cache the hook for the custom type, so that next time this
                # logic isn't run again.
                dump_hook = hooks[cls] = DumpMixin.default_dump_with

        return dump_hook(*hook_args)


# Copyright 2017-2018 Eric V. Smith
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
