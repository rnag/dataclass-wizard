from collections import defaultdict
from dataclasses import Field, fields
from typing import Dict, Tuple, Type, Union, Callable

from .abstractions import W
from .parsers import Parser
from .type_def import ExplicitNullType
from .utils.dict_helper import CaseInsensitiveDict


# A cached mapping of fully qualified class name to the list of fields, as
# returned by `dataclasses.fields()`.
_FIELDS: Dict[str, Tuple[Field]] = {}

# A cached mapping of a dataclass to each of its case-insensitive field names
# and load hook.
#
# Note: need to create a `ForwardRef` here, because Python 3.6 complains.
_FIELD_NAME_TO_LOAD_PARSER: Dict[str, 'CaseInsensitiveDict[str, Parser]'] = {}

# A cached mapping, per dataclass, of JSON field to instance field name
_JSON_FIELD_TO_DATACLASS_FIELD: Dict[
    str, Dict[str, Union[str, ExplicitNullType]]] = defaultdict(dict)

# A cached mapping, per dataclass, of instance field name to JSON field
_DATACLASS_FIELD_TO_JSON_FIELD: Dict[str, Dict[str, str]] = defaultdict(dict)

# A mapping of dataclass name to its Meta initializer (defined in
# :class:`bases.BaseJSONWizardMeta`), which is only set when the
# :class:`JSONSerializable.Meta` is sub-classed.
_META_INITIALIZER: Dict[
    str, Callable[[Type[W]], None]] = {}


def json_field_to_dataclass_field(class_or_instance):
    """
    Returns a mapping of JSON field to dataclass field.
    """
    name = get_class_name(class_or_instance)
    return _JSON_FIELD_TO_DATACLASS_FIELD[name]


def dataclass_field_to_json_field(class_or_instance):
    """
    Returns a mapping of dataclass field to JSON field.
    """
    name = get_class_name(class_or_instance)
    return _DATACLASS_FIELD_TO_JSON_FIELD[name]


def dataclass_field_to_load_parser(
        cls_loader, cls) -> 'CaseInsensitiveDict[str, Parser]':
    """
    Returns a mapping of each lower-cased field name to its annotated type.
    """
    name = get_class_name(cls)

    if name not in _FIELD_NAME_TO_LOAD_PARSER:
        # Lookup the Parser (dispatcher) for each field based on its annotated
        # type, and then cache it so we don't need to lookup each time.
        _FIELD_NAME_TO_LOAD_PARSER[name] = CaseInsensitiveDict(
            {f.name: cls_loader.get_parser_for_annotation(f.type, cls)
             for f in dataclass_fields(cls)})

    return _FIELD_NAME_TO_LOAD_PARSER[name]


def call_meta_initializer_if_needed(cls: Type[W]):
    """
    Calls the Meta initializer when the inner :class:`Meta` is sub-classed.
    """
    cls_name = cls.__name__

    if cls_name in _META_INITIALIZER:
        _META_INITIALIZER[cls_name](cls)


def dataclass_fields(class_or_instance) -> Tuple[Field]:
    """
    Cache the `dataclasses.fields()` call for each class, as overall that
    ends up around 5x faster than making a fresh call each time.

    """
    name = get_class_name(class_or_instance)

    if name not in _FIELDS:
        _FIELDS[name] = fields(class_or_instance)

    return _FIELDS[name]


def get_class_name(class_or_instance) -> str:
    """Return the fully qualified name of a class."""
    try:
        return class_or_instance.__qualname__
    except AttributeError:
        # We're dealing with a dataclass instance
        return type(class_or_instance).__qualname__


def get_outer_class_name(inner_cls, default=None, raise_=True):
    """
    Attempt to return the name of the outer (enclosing) class, given
    a reference to the inner class.

    If any errors occur - such as when `inner_cls` is not a real inner
    class - then an error will be raised if `raise_` is true, and if not
    we will return `default` instead.

    """
    try:
        return inner_cls.__qualname__.rsplit('.', 2)[-2]

    except IndexError:
        if raise_:
            raise
        return default


def get_class(obj):
    """Get the class for an object `obj`"""
    return obj if isinstance(obj, type) else type(obj)


def is_subclass(obj, base_cls: Type) -> bool:
    """Check if `obj` is a sub-class of `base_cls`"""
    cls = obj if isinstance(obj, type) else type(obj)
    return issubclass(cls, base_cls)
