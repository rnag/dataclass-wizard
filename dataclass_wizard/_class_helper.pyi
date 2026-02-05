from typing import Any, Callable, Sequence, TypeVar
from weakref import WeakKeyDictionary, WeakSet

from ._abstractions import W, E, AbstractLoaderGenerator, AbstractDumperGenerator
from .constants import PACKAGE_NAME
from .models import Condition
from .utils._object_path import PathType

# A mapping of dataclass to its loader.
CLASS_TO_LOADER: WeakKeyDictionary[type, type[AbstractLoaderGenerator]]

# A mapping of dataclass to its dumper.
CLASS_TO_DUMPER: WeakKeyDictionary[type, type[AbstractDumperGenerator]]

# We use a sentinel mapping to confirm if we need to set up the load
# config for a dataclass on an initial run.
IS_CONFIG_SETUP: WeakSet[type]

# A cached mapping, per dataclass, of instance field name to JSON path
DATACLASS_FIELD_TO_ALIAS_PATH_FOR_LOAD: WeakKeyDictionary[type, dict[str, Sequence[PathType]]]

# Dump: A cached mapping, per dataclass, of instance field name to alias path
DATACLASS_FIELD_TO_ALIAS_PATH_FOR_DUMP: WeakKeyDictionary[type, dict[str, Sequence[PathType]]]

# A cached mapping, per dataclass, of instance field name to alias
DATACLASS_FIELD_TO_ALIAS_FOR_LOAD: WeakKeyDictionary[type, dict[str, Sequence[str]]]

# A cached mapping, per dataclass, of instance field name to env var
DATACLASS_FIELD_TO_ENV_FOR_LOAD: WeakKeyDictionary[type, dict[str, Sequence[str]]]

# A cached mapping, per dataclass, of instance field name to alias
DATACLASS_FIELD_TO_ALIAS_FOR_DUMP: WeakKeyDictionary[type, dict[str, str]]

# A cached mapping, per dataclass, of instance field name to `SkipIf` condition
DATACLASS_FIELD_TO_SKIP_IF: WeakKeyDictionary[type, dict[str, Condition]]

# Cache: owner class -> its `Meta` inner class (only present when subclassed)
META_INITIALIZER: dict[str, Callable[[type[W]], None]] = {}

def set_class_loader(cls_to_loader, class_or_instance, loader: type[AbstractLoaderGenerator]):
    """
    Set (and return) the loader for a dataclass.
    """

def set_class_dumper(cls: type, dumper: type[AbstractDumperGenerator]):
    """
    Set (and return) the dumper for a dataclass.
    """

def dataclass_field_to_skip_if(cls: type) -> dict[str, Condition]:
    """
    Returns a mapping of dataclass field to SkipIf condition.
    """

def resolve_dataclass_field_to_alias_for_dump(cls: type) -> dict[str, Sequence[str]]: ...
def resolve_dataclass_field_to_alias_for_load(cls: type) -> dict[str, Sequence[str]]: ...
def resolve_dataclass_field_to_env_for_load(cls: type) -> dict[str, Sequence[str]]: ...

def setup_config_for_cls(cls: type):
    """
    This function processes a class `cls` on an initial run, and sets up the
    load process for `cls` by iterating over each dataclass field. For each
    field, it performs the following tasks:

        * Check if the field's annotation is of type ``Annotated``. If so,
          we iterate over each ``Annotated`` argument and find any special
          :class:`JSON` objects (this can also be set via the helper function
          ``json_key``). Assuming we find it, the class-specific mapping of
          dataclass field name to JSON key is then updated with the input
          passed in to this object.

        * Check if the field type is a :class:`JSONField` object (this can
          also be set by the helper function ``json_field``). Assuming this is
          the case, the class-specific mapping of dataclass field name to
          JSON key is then updated with the input passed in to
          the :class:`JSON` attribute.
    """

def call_meta_initializer_if_needed(cls: type[W | E],
                                    package_name=PACKAGE_NAME) -> None:
    """
    Calls the Meta initializer when the inner :class:`Meta` is sub-classed.
    """
