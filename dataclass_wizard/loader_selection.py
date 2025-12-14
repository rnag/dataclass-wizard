from typing import Callable, Collection, Optional

from .class_helper import (get_meta, CLASS_TO_LOAD_FUNC,
                           CLASS_TO_LOADER, CLASS_TO_V1_LOADER,
                           set_class_loader, create_new_class, CLASS_TO_DUMP_FUNC, CLASS_TO_V1_DUMPER, set_class_dumper,
                           CLASS_TO_DUMPER)
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


def _get_load_fn_for_dataclass(cls: type[T], v1=None) -> Callable[[JSONObject], T]:
    meta = get_meta(cls)
    if v1 is None:
        v1 = getattr(meta, 'v1', False)

    if v1:
        from .v1.loaders import load_func_for_dataclass as V1_load_func_for_dataclass
        # noinspection PyTypeChecker
        load = V1_load_func_for_dataclass(cls)
    else:
        from .loaders import load_func_for_dataclass
        load = load_func_for_dataclass(cls)

    # noinspection PyTypeChecker
    return load


def _get_dump_fn_for_dataclass(cls: type[T], v1=None) -> Callable[[JSONObject], T]:
    if v1 is None:
        v1 = getattr(get_meta(cls), 'v1', False)

    if v1:
        from .v1.dumpers import dump_func_for_dataclass as V1_dump_func_for_dataclass
        # noinspection PyTypeChecker
        dump = V1_dump_func_for_dataclass(cls)
    else:
        from .dumpers import dump_func_for_dataclass
        dump = dump_func_for_dataclass(cls)

    # noinspection PyTypeChecker
    return dump


def get_dumper(class_or_instance=None, create=True,
               base_cls: T = None,
               v1: Optional[bool] = None) -> type[T]:
    """
    Get the dumper for the class, using the following logic:

        * Return the class if it's already a sub-class of :class:`DumpMixin`
        * If `create` is enabled (which is the default), a new sub-class of
          :class:`DumpMixin` for the class will be generated and cached on the
          initial run.
        * Otherwise, we will return the base loader, :class:`DumpMixin`, which
          can potentially be shared by more than one dataclass.

    """
    if v1 is None:
        v1 = getattr(get_meta(class_or_instance), 'v1', False)

    if v1:
        cls_to_dumper = CLASS_TO_V1_DUMPER
        if base_cls is None:
            from .v1.dumpers import DumpMixin as V1_DumpMixin
            base_cls = V1_DumpMixin
    else:
        cls_to_dumper = CLASS_TO_DUMPER
        if base_cls is None:
            from .dumpers import DumpMixin
            base_cls = DumpMixin

    try:
        return cls_to_dumper[class_or_instance]

    except KeyError:
        # TODO figure out type errors

        if hasattr(class_or_instance, _DUMP_HOOKS):
            return set_class_dumper(
                cls_to_dumper, class_or_instance, class_or_instance)

        elif create:
            cls_loader = create_new_class(class_or_instance, (base_cls, ))
            return set_class_dumper(
                cls_to_dumper, class_or_instance, cls_loader)

        return set_class_dumper(
            cls_to_dumper, class_or_instance, base_cls)


def get_loader(class_or_instance=None, create=True,
               base_cls: T = None,
               v1: Optional[bool] = None) -> type[T]:
    """
    Get the loader for the class, using the following logic:

        * Return the class if it's already a sub-class of :class:`LoadMixin`
        * If `create` is enabled (which is the default), a new sub-class of
          :class:`LoadMixin` for the class will be generated and cached on the
          initial run.
        * Otherwise, we will return the base loader, :class:`LoadMixin`, which
          can potentially be shared by more than one dataclass.

    """
    if v1 is None:
        v1 = getattr(get_meta(class_or_instance), 'v1', False)

    if v1:
        cls_to_loader = CLASS_TO_V1_LOADER
        if base_cls is None:
            from .v1.loaders import LoadMixin as V1_LoadMixin
            base_cls = V1_LoadMixin
    else:
        cls_to_loader = CLASS_TO_LOADER
        if base_cls is None:
            from .loaders import LoadMixin
            base_cls = LoadMixin

    try:
        return cls_to_loader[class_or_instance]

    except KeyError:

        if hasattr(class_or_instance, _LOAD_HOOKS):
            return set_class_loader(
                cls_to_loader, class_or_instance, class_or_instance)

        elif create:
            cls_loader = create_new_class(class_or_instance, (base_cls, ))
            return set_class_loader(
                cls_to_loader, class_or_instance, cls_loader)

        return set_class_loader(
            cls_to_loader, class_or_instance, base_cls)
