from collections import defaultdict
from dataclasses import Field
from typing import Any, Callable

from .abstractions import W, AbstractLoader, AbstractDumper, AbstractParser
from .bases import META
from .models import Condition
from .type_def import ExplicitNullType, T
from .utils.dict_helper import DictWithLowerStore
from .utils.object_path import PathType


# A cached mapping of dataclass to the list of fields, as returned by
# `dataclasses.fields()`.
FIELDS: dict[type, tuple[Field, ...]] = {}

# A cached mapping of dataclass to a mapping of field name
# to default value, as returned by `dataclasses.fields()`.
FIELD_TO_DEFAULT: dict[type, dict[str, Any]] = {}

# Mapping of main dataclass to its `load` function.
CLASS_TO_LOAD_FUNC: dict[type, Any] = {}

# Mapping of main dataclass to its `dump` function.
CLASS_TO_DUMP_FUNC: dict[type, Any] = {}

# A mapping of dataclass to its loader.
CLASS_TO_LOADER: dict[type, type[AbstractLoader]] = {}

# A mapping of dataclass to its dumper.
CLASS_TO_DUMPER: dict[type, type[AbstractDumper]] = {}

# A cached mapping of a dataclass to each of its case-insensitive field names
# and load hook.
FIELD_NAME_TO_LOAD_PARSER: dict[type, DictWithLowerStore[str, AbstractParser]] = {}

# Since the dump process doesn't use Parsers currently, we use a sentinel
# mapping to confirm if we need to setup the dump config for a dataclass
# on an initial run.
IS_DUMP_CONFIG_SETUP: dict[type, bool] = {}

# A cached mapping, per dataclass, of JSON field to instance field name
JSON_FIELD_TO_DATACLASS_FIELD: dict[type, dict[str, str | ExplicitNullType]] = defaultdict(dict)

# A cached mapping, per dataclass, of instance field name to JSON path
DATACLASS_FIELD_TO_JSON_PATH: dict[type, dict[str, PathType]] = defaultdict(dict)

# A cached mapping, per dataclass, of instance field name to JSON field
DATACLASS_FIELD_TO_JSON_FIELD: dict[type, dict[str, str]] = defaultdict(dict)

# A cached mapping, per dataclass, of instance field name to `SkipIf` condition
DATACLASS_FIELD_TO_SKIP_IF: dict[type, dict[str, Condition]] = defaultdict(dict)

# A mapping of dataclass name to its Meta initializer (defined in
# :class:`bases.BaseJSONWizardMeta`), which is only set when the
# :class:`JSONSerializable.Meta` is sub-classed.
META_INITIALIZER: dict[str, Callable[[type[W]], None]] = {}

# Mapping of dataclass to its Meta inner class, which will only be set when
# the :class:`JSONSerializable.Meta` is sub-classed.
_META: dict[type, META] = {}


def dataclass_to_loader(cls: type) -> type[AbstractLoader]:
    """
    Returns the loader for a dataclass.
    """


def dataclass_to_dumper(cls: type) -> type[AbstractDumper]:
    """
    Returns the dumper for a dataclass.
    """


def set_class_loader(class_or_instance, loader: type[AbstractLoader]):
    """
    Set (and return) the loader for a dataclass.
    """


def set_class_dumper(cls: type, dumper: type[AbstractDumper]):
    """
    Set (and return) the dumper for a dataclass.
    """


def json_field_to_dataclass_field(cls: type) -> dict[str, str | ExplicitNullType]:
    """
    Returns a mapping of JSON field to dataclass field.
    """


def dataclass_field_to_json_path(cls: type) -> dict[str, PathType]:
    """
    Returns a mapping of dataclass field to JSON path.
    """


def dataclass_field_to_json_field(cls: type) -> dict[str, str]:
    """
    Returns a mapping of dataclass field to JSON field.
    """


def dataclass_field_to_skip_if(cls: type) -> dict[str, Condition]:
    """
    Returns a mapping of dataclass field to SkipIf condition.
    """


def dataclass_field_to_load_parser(
        cls_loader: type[AbstractLoader],
        cls: type,
        config: META,
        save: bool = True) -> DictWithLowerStore[str, AbstractParser]:
    """
    Returns a mapping of each lower-cased field name to its annotated type.
    """


def _setup_load_config_for_cls(cls_loader: type[AbstractLoader],
                               cls: type,
                               config: META,
                               save: bool = True
                               ) -> DictWithLowerStore[str, AbstractParser]:
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


def setup_dump_config_for_cls_if_needed(cls: type) -> None:
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


def call_meta_initializer_if_needed(cls: type[W]) -> None:
    """
    Calls the Meta initializer when the inner :class:`Meta` is sub-classed.
    """


def get_meta(cls: type) -> META:
    """
    Retrieves the Meta config for the :class:`AbstractJSONWizard` subclass.

    This config is set when the inner :class:`Meta` is sub-classed.
    """


def dataclass_fields(cls: type) -> tuple[Field, ...]:
    """
    Cache the `dataclasses.fields()` call for each class, as overall that
    ends up around 5x faster than making a fresh call each time.

    """


def dataclass_init_fields(cls: type) -> tuple[Field, ...]:
    """Get only the dataclass fields that would be passed into the constructor."""


def dataclass_field_names(cls: type) -> tuple[str, ...]:
    """Get the names of all dataclass fields"""


def dataclass_field_to_default(cls: type) -> dict[str, Any]:
    """Get default values for the (optional) dataclass fields."""


def is_builtin_class(cls: type) -> bool:
    """Check if a class is a builtin in Python."""


def is_builtin(o: Any) -> bool:
    """Check if an object/singleton/class is a builtin in Python."""


def create_new_class(
        class_or_instance, bases: tuple[T, ...],
        suffix: str | None = None, attr_dict=None) -> T:
    """
    Create (dynamically) and return a new class that sub-classes from a list
    of `bases`.
    """


def get_class_name(class_or_instance) -> str:
    """Return the fully qualified name of a class."""


def get_outer_class_name(inner_cls, default=None, raise_: bool = True) -> str:
    """
    Attempt to return the fully qualified name of the outer (enclosing) class,
    given a reference to the inner class.

    If any errors occur - such as when `inner_cls` is not a real inner
    class - then an error will be raised if `raise_` is true, and if not
    we will return `default` instead.

    """


def get_class(obj: Any) -> type:
    """Get the class for an object `obj`"""


def is_subclass(obj: Any, base_cls: type) -> bool:
    """Check if `obj` is a sub-class of `base_cls`"""


def is_subclass_safe(cls, class_or_tuple) -> bool:
    """Check if `obj` is a sub-class of `base_cls` (safer version)"""
