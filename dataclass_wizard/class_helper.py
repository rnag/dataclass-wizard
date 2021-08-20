from collections import defaultdict
from dataclasses import Field, fields
from typing import Dict, Tuple, Type, Union, Callable, Optional

from .abstractions import W, AbstractLoader, AbstractDumper
from .models import JSONField, JSON
from .parsers import Parser
from .type_def import ExplicitNullType, T
from .utils.dict_helper import CaseInsensitiveDict
from .utils.typing_compat import is_annotated, get_args


# A cached mapping of fully qualified class name to the list of fields, as
# returned by `dataclasses.fields()`.
_FIELDS: Dict[str, Tuple[Field]] = {}

# A mapping of dataclass name to its loader.
_CLASS_TO_LOADER: Dict[str, Type[AbstractLoader]] = {}

# A mapping of dataclass name to its dumper.
_CLASS_TO_DUMPER: Dict[str, Type[AbstractDumper]] = {}

# A cached mapping of a dataclass to each of its case-insensitive field names
# and load hook.
#
# Note: need to create a `ForwardRef` here, because Python 3.6 complains.
_FIELD_NAME_TO_LOAD_PARSER: Dict[str, 'CaseInsensitiveDict[str, Parser]'] = {}

# Since the dump process doesn't use Parsers currently, we use a sentinel
# mapping to confirm if we need to setup the dump config for a dataclass
# on an initial run.
_IS_DUMP_CONFIG_SETUP: Dict[str, bool] = {}

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


def dataclass_to_loader(class_or_instance):
    """
    Returns the loader for a dataclass.
    """
    name = get_class_name(class_or_instance)
    return _CLASS_TO_LOADER[name]


def dataclass_to_dumper(class_or_instance):
    """
    Returns the dumper for a dataclass.
    """
    name = get_class_name(class_or_instance)
    return _CLASS_TO_DUMPER[name]


def set_class_loader(class_or_instance, loader: Type[AbstractLoader]):
    """
    Set (and return) the loader for a dataclass.
    """
    name = get_class_name(class_or_instance)
    _CLASS_TO_LOADER[name] = get_class(loader)

    return _CLASS_TO_LOADER[name]


def set_class_dumper(class_or_instance, dumper: Type[AbstractDumper]):
    """
    Set (and return) the dumper for a dataclass.
    """
    name = get_class_name(class_or_instance)
    _CLASS_TO_DUMPER[name] = get_class(dumper)

    return _CLASS_TO_DUMPER[name]


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
        _setup_load_config_for_cls(cls_loader, cls, name)

    return _FIELD_NAME_TO_LOAD_PARSER[name]


def _setup_load_config_for_cls(cls_loader, cls, name: str):
    """
    This function processes a class `cls` on an initial run, and sets up the
    load process for `cls` by iterating over each dataclass field. For each
    field, it performs the following tasks:

        * Lookup the Parser (dispatcher) for the field based on its type
          annotation, and then cache it so we don't need to lookup each time.

        * Check if the field's annotation is of type ``Annotated``. If so,
          we iterate over each ``Annotated`` argument and find any special
          :class:`JSON` objects (this can also be set via the helper function
          ``json_key``). Assuming we find it, the class-specific mapping of
          JSON key to dataclass field name is then updated with the input
          passed in to this object.

        * Check if the field type is a :class:`JSONField` object (this can
          also be set by the helper function ``json_field``). Assuming this is
          the case, the class-specific mapping of JSON key to dataclass field
          name is then updated with the input passed in to the :class:`JSON`
          attribute.
    """

    json_to_dataclass_field = _JSON_FIELD_TO_DATACLASS_FIELD[name]
    name_to_parser = {}

    for f in dataclass_fields(cls):

        # Lookup the Parser (dispatcher) for each field based on its annotated
        # type, and then cache it so we don't need to lookup each time.
        name_to_parser[f.name] = cls_loader.get_parser_for_annotation(
            f.type, cls)

        # Check if the field is a `JSONField` object. If so, update the
        # class-specific mapping of JSON key to dataclass field name.
        if isinstance(f, JSONField):
            for key in f.json.keys:
                json_to_dataclass_field[key] = f.name

        # Check if the field annotation is an `Annotated` type. If so,
        # look for any `JSON` objects in the arguments; for each object,
        # update the class-specific mapping of JSON key to dataclass field
        # name.
        if is_annotated(f.type):
            for extra in get_args(f.type)[1:]:
                if isinstance(extra, JSON):
                    for key in extra.keys:
                        json_to_dataclass_field[key] = f.name

    _FIELD_NAME_TO_LOAD_PARSER[name] = CaseInsensitiveDict(name_to_parser)


def setup_dump_config_for_cls_if_needed(cls):
    """
    This function processes a class `cls` on an initial run, and sets up the
    dump process for `cls` by iterating over each dataclass field. For each
    field, it performs the following tasks:

        * Check if the field's annotation is of type ``Annotated``. If so,
          we iterate over each ``Annotated`` argument and find any special
          :class:`JSON` objects (this can also be set via the helper function
          ``json_key``). Assuming we find it, the class-specific mapping of
          dataclass field name to JSON key is then updated with the input
          passed in to this object.

        * Check if the field type is a :class:`JSONField` object (this can
          also be set by the helper function ``json_field``). Assuming this is
          the case, the class-specific mapping of dataclass field name to JSON
          key is then updated with the input passed in to the :class:`JSON`
          attribute.
    """

    name = get_class_name(cls)

    if name in _IS_DUMP_CONFIG_SETUP:
        return

    dataclass_to_json_field = _DATACLASS_FIELD_TO_JSON_FIELD[name]

    for f in dataclass_fields(cls):

        # Check if the field is a `JSONField` object. If so, update the
        # class-specific mapping of dataclass field name to JSON key.
        if isinstance(f, JSONField) and f.json.all:
            dataclass_to_json_field[f.name] = f.json.keys[0]

        # Check if the field annotation is an `Annotated` type. If so,
        # look for any `JSON` objects in the arguments; for each object,
        # update the class-specific mapping of dataclass field name to JSON
        # key.
        if is_annotated(f.type):
            for extra in get_args(f.type)[1:]:
                if isinstance(extra, JSON) and extra.all:
                    dataclass_to_json_field[f.name] = extra.keys[0]

    # Mark the dataclass as processed, as the initial dump process is set up.
    _IS_DUMP_CONFIG_SETUP[name] = True


def call_meta_initializer_if_needed(cls: Type[W]):
    """
    Calls the Meta initializer when the inner :class:`Meta` is sub-classed.
    """
    cls_name = get_class_name(cls)

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


def create_new_class(
        class_or_instance, bases: Tuple[T, ...],
        suffix: Optional[str] = None, attr_dict=None) -> T:
    """
    Create (dynamically) and return a new class that sub-classes from a list
    of `bases`.
    """
    if not suffix and bases:
        suffix = get_class_name(bases[0])

    new_cls_name = f'{get_class_name(class_or_instance)}{suffix}'

    return type(
        new_cls_name,
        bases,
        attr_dict or {'__slots__': ()}
    )


def get_class_name(class_or_instance) -> str:
    """Return the fully qualified name of a class."""
    try:
        return class_or_instance.__qualname__
    except AttributeError:
        # We're dealing with a dataclass instance
        return type(class_or_instance).__qualname__


def get_outer_class_name(inner_cls, default=None, raise_=True):
    """
    Attempt to return the fully qualified name of the outer (enclosing) class,
    given a reference to the inner class.

    If any errors occur - such as when `inner_cls` is not a real inner
    class - then an error will be raised if `raise_` is true, and if not
    we will return `default` instead.

    """
    try:
        name = get_class_name(inner_cls).rsplit('.', 1)[-2]
        # This is mainly for our test cases, where we nest the class
        # definition in the test func. Either way, it's not a valid class.
        assert not name.endswith('<locals>')

    except (IndexError, AssertionError):
        if raise_:
            raise
        return default

    else:
        return name


def get_class(obj):
    """Get the class for an object `obj`"""
    return obj if isinstance(obj, type) else type(obj)


def is_subclass(obj, base_cls: Type) -> bool:
    """Check if `obj` is a sub-class of `base_cls`"""
    cls = obj if isinstance(obj, type) else type(obj)
    return issubclass(cls, base_cls)
