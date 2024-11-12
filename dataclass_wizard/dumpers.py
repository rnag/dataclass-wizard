"""
The implementation below uses code adapted from the `asdict` helper function
from the library Dataclasses (https://github.com/ericvsmith/dataclasses).

This library is available under the Apache 2.0 license, which can be
obtained from http://www.apache.org/licenses/LICENSE-2.0.


See the end of this file for the original Apache license from this library.
"""
from collections import defaultdict, deque
# noinspection PyProtectedMember,PyUnresolvedReferences
from dataclasses import _is_dataclass_instance
from datetime import datetime, time, date, timedelta
from decimal import Decimal
from enum import Enum
# noinspection PyProtectedMember,PyUnresolvedReferences
from typing import Type, List, Dict, Any, NamedTupleMeta, Optional, Callable
from uuid import UUID

from .abstractions import AbstractDumper
from .bases import BaseDumpHook, AbstractMeta, META
from .class_helper import (
    create_new_class,
    dataclass_field_names, dataclass_field_to_default,
    dataclass_field_to_json_field,
    dataclass_to_dumper, set_class_dumper,
    _CLASS_TO_DUMP_FUNC, setup_dump_config_for_cls_if_needed, get_meta,
    dataclass_field_to_load_parser,
)
from .constants import _DUMP_HOOKS, TAG
from .decorators import _alias
from .log import LOG
from .type_def import (
    ExplicitNull, NoneType, JSONObject,
    DD, LSQ, E, U, LT, NT, T
)
from .utils.code_builder import CodeBuilder
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
    cls.register_dump_hook(bytes, cls.default_dump_with)
    cls.register_dump_hook(bytearray, cls.default_dump_with)
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


def asdict(obj: T,
           *, cls=None, dict_factory=dict,
           exclude: List[str] = None, **kwargs) -> JSONObject:
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

    cls = cls or type(obj)

    try:
        dump = _CLASS_TO_DUMP_FUNC[cls]
    except KeyError:
        dump = dump_func_for_dataclass(cls)

    return dump(obj, dict_factory, exclude, **kwargs)


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

    # Set up the initial dump config for the dataclass.
    setup_dump_config_for_cls_if_needed(cls)

    # A cached mapping of each dataclass field to the resolved key name in a
    # JSON or dictionary object; useful so we don't need to do a case
    # transformation (via regex) each time.
    dataclass_to_json_field = dataclass_field_to_json_field(cls)

    # A cached mapping of dataclass field name to its default value, either
    # via a `default` or `default_factory` argument.
    field_to_default = dataclass_field_to_default(cls)

    # A collection of field names in the dataclass.
    field_names = dataclass_field_names(cls)

    # Check if we need to auto-assign tags for dataclasses in `Union` types.
    if meta.auto_assign_tags:
        # Unfortunately, we can't handle this as part of the dump process, as
        # we don't process the class annotations here. So instead, generate
        # the load parser for each field  (if needed), but don't cache the
        # result, as it's conceivable we might yet call `LoadMeta` later.
        from .loaders import get_loader
        cls_loader = get_loader(cls)
        # Use the cached result if it exists, but don't cache it ourselves.
        _ = dataclass_field_to_load_parser(
            cls_loader, cls, config, save=False)

    # Tag key to populate when a dataclass is in a `Union` with other types.
    tag_key = meta.tag_key or TAG

    _locals = {
        'cls': cls,
        # 'meta': meta,
        'config': config,
        'cls_dumper': cls_dumper,
        'field_names': field_names,
        'field_to_default': field_to_default,
        'dataclass_to_json_field': dataclass_to_json_field,

        # TODO maybe global?
        '_asdict_inner': _asdict_inner,
        'hooks': hooks,
        'nested_cls_to_dump_func': nested_cls_to_dump_func,
    }

    # TODO Unsure if dataclasses uses globals()?
    _globals = {

        'T': T,
        'ExplicitNull': ExplicitNull,
        'LOG': LOG,
    }

    # Initialize CodeBuilder
    cb = CodeBuilder()

    # Code for `cls_asdict`
    with cb.function('cls_asdict',
                ['obj:T',
                     'dict_factory=dict',
                     "exclude:'list[str]|None'=None",
                     f'skip_defaults:bool={meta.skip_defaults}'],
                     return_type='JSONObject'):

        if hasattr(cls_dumper, '__pre_as_dict__'):
            cb.add_line('cls_dumper.__pre_as_dict__(obj)')

        # Initialize result list to hold field mappings
        cb.add_line("result = []")

        if field_names:

            skip_field_assignments = []
            exclude_assignments_to_skip = []
            skip_default_assignments = []
            field_assignments = []

            # Loop over the dataclass fields
            for i, field in enumerate(field_names):
                skip_field = f'_skip_{i}'
                default_value = f'_default_{i}'

                skip_field_assignments.append(skip_field)
                exclude_assignments_to_skip.append(
                    f'{skip_field}={field!r} in exclude'
                )
                if field in field_to_default:
                    _locals[default_value] = field_to_default[field]
                    skip_default_assignments.append(
                        f"{skip_field} = {skip_field} or obj.{field} == {default_value}"
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
                    field_assignments.append(f"if not {skip_field}:")
                    field_assignments.append(f"  value = _asdict_inner(obj.{field}, dict_factory,"
                                             f" hooks, config, nested_cls_to_dump_func)")
                    field_assignments.append(f"  result.append(('{json_field}', value))")

            cb.add_line(f'{'='.join(skip_field_assignments)}=False')
            cb.add_line('if exclude is not None:')
            cb.increase_indent()
            cb.add_lines(*exclude_assignments_to_skip)
            cb.decrease_indent()

            if skip_default_assignments:
                cb.add_line('if skip_defaults:')
                cb.increase_indent()
                cb.add_lines(*skip_default_assignments)
                cb.decrease_indent()

            cb.add_lines(*field_assignments)

        # Return the final dictionary result
        if meta.tag:
            cb.add_line("result = dict_factory(result)")
            cb.add_line(f"result[{tag_key!r}] = {meta.tag!r}")
            # Return the result with the tag added
            cb.add_line("return result")
        else:
            cb.add_line("return dict_factory(result)")

    # Compile the code into a dynamic string
    cls_asdict = cb.compile_with_types(locals=_locals, globals=_globals)

    asdict_func = cls_asdict

    # In any case, save the dump function for the class, so we don't need to
    # run this logic each time.
    if is_main_class:
        _CLASS_TO_DUMP_FUNC[cls] = asdict_func
    else:
        nested_cls_to_dump_func[cls] = asdict_func

    return asdict_func


# NOTE: This method has been modified to accept `hook` and `meta` arguments,
# and the return type has been annotated as `Any`. The logic inside this
# method has also been heavily modified from the original implementation in
# `dataclasses`. However, I will call out specific lines where it is taken
# directly from the original version.
def _asdict_inner(obj, dict_factory, hooks, meta, cls_to_dump_func) -> Any:

    cls = type(obj)
    dump_hook = hooks.get(cls)
    hook_args = (obj, cls, dict_factory, hooks, meta, cls_to_dump_func)

    if dump_hook is not None:
        return dump_hook(*hook_args)

    if _is_dataclass_instance(obj):
        try:
            dump = cls_to_dump_func[cls]
        except KeyError:
            dump = dump_func_for_dataclass(cls, meta, cls_to_dump_func)
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
