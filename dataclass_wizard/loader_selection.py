from typing import Callable, Optional

from .class_helper import (get_meta, CLASS_TO_LOAD_FUNC,
                           CLASS_TO_LOADER, CLASS_TO_V1_LOADER,
                           set_class_loader, create_new_class)
from .constants import _LOAD_HOOKS
from .type_def import T, JSONObject


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
