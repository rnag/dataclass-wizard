from typing import Callable

from .class_helper import (CLASS_TO_LOAD_FUNC,
                           CLASS_TO_DUMP_FUNC)
# noinspection PyUnresolvedReferences
from .constants import _LOAD_HOOKS, _DUMP_HOOKS
from .type_def import T, JSONObject


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
        dump = _get_dump_fn_for_dataclass(cls)

    return dump(o, dict_factory, exclude, **kwargs)


def fromdict(cls: type[T], d: JSONObject) -> T:
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
        load = _get_load_fn_for_dataclass(cls)

    return load(d)


def fromlist(cls: type[T], list_of_dict: list[JSONObject]) -> list[T]:
    """
    Converts a Python list object to a list of dataclass instances.

    Iterates over each dataclass field recursively; lists, dicts, and nested
    dataclasses will likewise be initialized as expected.

    """
    try:
        load = CLASS_TO_LOAD_FUNC[cls]
    except KeyError:
        load = _get_load_fn_for_dataclass(cls)

    return [load(d) for d in list_of_dict]


def _get_load_fn_for_dataclass(cls: type[T]) -> Callable[[JSONObject], T]:
    # TODO
    from .loaders import load_func_for_dataclass as V1_load_func_for_dataclass
    # noinspection PyTypeChecker
    load = V1_load_func_for_dataclass(cls)

    # noinspection PyTypeChecker
    return load


def _get_dump_fn_for_dataclass(cls: type[T]) -> Callable[[JSONObject], T]:
    # TODO
    from .dumpers import dump_func_for_dataclass as V1_dump_func_for_dataclass
    # noinspection PyTypeChecker
    dump = V1_dump_func_for_dataclass(cls)

    # noinspection PyTypeChecker
    return dump
