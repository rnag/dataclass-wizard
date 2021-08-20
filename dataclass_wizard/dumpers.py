"""
The implementation below uses code adapted from the `asdict` helper function
from the library Dataclasses (https://github.com/ericvsmith/dataclasses).

This library is available under the Apache 2.0 license, which can be
obtained from http://www.apache.org/licenses/LICENSE-2.0.


See the end of this file for the original Apache license from this library.
"""
from collections import defaultdict, deque
# noinspection PyProtectedMember
from dataclasses import _is_dataclass_instance
from datetime import datetime, time, date
from decimal import Decimal
from enum import Enum
from typing import Type, Dict, Any, NamedTupleMeta
from uuid import UUID

from .abstractions import AbstractDumper
from .bases import BaseDumpHook
from .class_helper import (
    create_new_class,
    dataclass_fields, dataclass_field_to_json_field,
    dataclass_to_dumper, set_class_dumper,
    setup_dump_config_for_cls_if_needed,
)
from .constants import _DUMP_HOOKS
from .log import LOG
from .type_def import NoneType, DD, LSQ, E, U, LT, NT
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
    def transform_dataclass_field(string: str) -> str:
        return to_camel_case(string)

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
    def dump_with_list_or_tuple(
            o: LT, typ: Type[LT], dict_factory, hooks):

        return typ(_asdict_inner(v, dict_factory, hooks) for v in o)

    @staticmethod
    def dump_with_iterable(
            o: LSQ, _typ: Type[LSQ], dict_factory, hooks):

        return list(_asdict_inner(v, dict_factory, hooks) for v in o)

    @staticmethod
    def dump_with_named_tuple(
            o: NT, typ: Type[NT], dict_factory, hooks):

        return typ(*[_asdict_inner(v, dict_factory, hooks) for v in o])

    @staticmethod
    def dump_with_dict(
            o: Dict, typ: Type[Dict], dict_factory, hooks):

        return typ((_asdict_inner(k, dict_factory, hooks),
                    _asdict_inner(v, dict_factory, hooks))
                   for k, v in o.items())

    @staticmethod
    def dump_with_defaultdict(
            o: DD, _typ: Type[DD], dict_factory, hooks):

        return {_asdict_inner(k, dict_factory, hooks):
                _asdict_inner(v, dict_factory, hooks)
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


def get_dumper(class_or_instance=None, create=False) -> Type[DumpMixin]:
    """
    Get the dumper for the class, using the following logic:

        * Return the class if it's already a sub-class of :class:`DumpMixin`
        * If `create` is enabled, a new sub-class of :class:`DumpMixin` for
          the class will be generated and cached on the initial run.
        * Otherwise, we will return the base dumper, :class:`DumpMixin`, which
          can potentially be shared by more than one dataclass.

    """
    try:
        return dataclass_to_dumper(class_or_instance)

    except KeyError:

        if hasattr(class_or_instance, _DUMP_HOOKS):
            return set_class_dumper(class_or_instance, class_or_instance)

        elif create:
            cls_dumper = create_new_class(class_or_instance, (DumpMixin, ))
            return set_class_dumper(class_or_instance, cls_dumper)

        return set_class_dumper(class_or_instance, DumpMixin)


def asdict(obj, *, dict_factory=dict) -> Dict[str, Any]:
    """Return the fields of a dataclass instance as a new dictionary mapping
    field names to field values.

    Example usage:

      @dataclass
      class C:
          x: int
          y: int

      c = C(1, 2)
      assert asdict(c) == {'x': 1, 'y': 2}

    If given, 'dict_factory' will be used instead of built-in dict.
    The function applies recursively to field values that are
    dataclass instances. This will also look into built-in containers:
    tuples, lists, and dicts.
    """
    if not _is_dataclass_instance(obj):
        raise TypeError("asdict() should be called on dataclass instances")

    # -- The following lines are added, and are not present in original implementation. --
    cls_dumper = get_dumper(obj)
    hooks = cls_dumper.__DUMP_HOOKS__

    # Pass the class reference itself, since we know we have an instance of
    # the class.
    setup_dump_config_for_cls_if_needed(type(obj))

    # Call the optional hook that runs before we process the dataclass
    cls_dumper.__pre_as_dict__(obj)
    # -- END --

    return _asdict_inner(obj, dict_factory, hooks)


# NOTE: This method has been modified to accept a `hook` argument, and the
# return type has been annotated as `Any`. The logic inside this method has
# also been heavily modified from the original implementation in
# `dataclasses`. However, I will call out specific lines where it is taken
# directly from the original version.
def _asdict_inner(obj, dict_factory, hooks) -> Any:

    typ = type(obj)
    dump_hook = hooks.get(typ)
    hook_args = (obj, typ, dict_factory, hooks)

    if dump_hook is not None:
        return dump_hook(*hook_args)

    # -- This check is the same as in the original version --
    if _is_dataclass_instance(obj):

        dataclass_to_json_field = dataclass_field_to_json_field(obj)
        cls_dumper = get_dumper(obj)
        result = []

        for f in dataclass_fields(obj):
            # -- This line is *mostly* the same as in the original version --
            value = _asdict_inner(getattr(obj, f.name), dict_factory, hooks)

            json_field = dataclass_to_json_field.get(f.name)
            if not json_field:
                # Normalize the dataclass field name (by default to camel
                # case)
                json_field = cls_dumper.transform_dataclass_field(f.name)
                dataclass_to_json_field[f.name] = json_field

            # -- This line is *mostly* the same as in the original version --
            result.append((json_field, value))
        # -- This line is the same as in the original version --
        return dict_factory(result)

    else:

        # -- The following `if` condition and comments are the same as in the original version --
        if isinstance(obj, tuple) and hasattr(obj, '_fields'):
            # obj is a namedtuple.  Recurse into it, but the returned
            # object is another namedtuple of the same type.  This is
            # similar to how other list- or tuple-derived classes are
            # treated (see below), but we just need to create them
            # differently because a namedtuple's __init__ needs to be
            # called differently (see bpo-34363).
            return hooks[NamedTupleMeta](*hook_args)

        else:
            for t in hooks:
                if isinstance(obj, t):
                    return hooks[t](*hook_args)

        LOG.warning('Using default dumper, object=%r, type=%r', obj, typ)

        return DumpMixin.default_dump_with(*hook_args)


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
