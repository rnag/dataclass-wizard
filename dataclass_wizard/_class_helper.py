from __future__ import annotations

from dataclasses import MISSING
from weakref import WeakKeyDictionary, WeakSet

from ._type_def import ExplicitNull
from ._type_utils import get_class, get_class_name, per_cls
from .constants import CATCH_ALL, PACKAGE_NAME
from .errors import InvalidConditionError
from .models import CatchAll, Field
from .utils._dataclass_compat import SEEN_DEFAULT, dataclass_fields
from .utils._typing_compat import (
    eval_forward_ref_if_needed,
    get_args,
    is_annotated,
)

# A mapping of dataclass to its loader.
CLASS_TO_LOADER = WeakKeyDictionary()

# A mapping of dataclass to its dumper.
CLASS_TO_DUMPER = WeakKeyDictionary()

# We use a sentinel mapping to confirm if we need to set up the load
# config for a dataclass on an initial run.
IS_CONFIG_SETUP = WeakSet()

# Load: A cached mapping, per dataclass, of instance field name to alias path
DATACLASS_FIELD_TO_ALIAS_PATH_FOR_LOAD = WeakKeyDictionary()

# Dump: A cached mapping, per dataclass, of instance field name to alias path
DATACLASS_FIELD_TO_ALIAS_PATH_FOR_DUMP = WeakKeyDictionary()

# Load: A cached mapping, per dataclass, of instance field name to alias
DATACLASS_FIELD_TO_ALIAS_FOR_LOAD = WeakKeyDictionary()

# Load: A cached mapping, per dataclass, of instance field name to env var
DATACLASS_FIELD_TO_ENV_FOR_LOAD = WeakKeyDictionary()

# Dump: A cached mapping, per dataclass, of instance field name to alias
DATACLASS_FIELD_TO_ALIAS_FOR_DUMP = WeakKeyDictionary()

# A cached mapping, per dataclass, of instance field name to `SkipIf` condition
DATACLASS_FIELD_TO_SKIP_IF = WeakKeyDictionary()

# Cache: owner class -> its `Meta` inner class (only present when subclassed)
META_INITIALIZER = {}


def set_class_loader(cls_to_loader, class_or_instance, loader):

    cls = get_class(class_or_instance)
    loader_cls = get_class(loader)

    cls_to_loader[cls] = loader_cls

    return loader_cls


def set_class_dumper(cls_to_dumper, class_or_instance, dumper):

    cls = get_class(class_or_instance)
    dumper_cls = get_class(dumper)

    cls_to_dumper[cls] = dumper_cls

    return dumper_cls


def dataclass_field_to_skip_if(cls):
    return per_cls(DATACLASS_FIELD_TO_SKIP_IF, cls)


def resolve_dataclass_field_to_alias_for_dump(cls):

    if cls not in IS_CONFIG_SETUP:
        setup_config_for_cls(cls)

    return DATACLASS_FIELD_TO_ALIAS_FOR_DUMP[cls]


def resolve_dataclass_field_to_alias_for_load(cls):

    if cls not in IS_CONFIG_SETUP:
        setup_config_for_cls(cls)

    return DATACLASS_FIELD_TO_ALIAS_FOR_LOAD[cls]


def resolve_dataclass_field_to_env_for_load(cls):

    if cls not in IS_CONFIG_SETUP:
        setup_config_for_cls(cls)

    return DATACLASS_FIELD_TO_ENV_FOR_LOAD[cls]


def _process_field(name: str,
                   f: Field,
                   set_paths: bool,
                   init: bool,
                   load_dataclass_field_to_path,
                   dump_dataclass_field_to_path,
                   load_dataclass_field_to_alias,
                   load_dataclass_field_to_env,
                   dump_dataclass_field_to_alias):
    """Process a :class:`Field` for a dataclass field."""

    if f.path is not None:
        if set_paths:
            if init and f.load_alias is not ExplicitNull:
                load_dataclass_field_to_path[name] = f.path
            if not f.skip and f.dump_alias is not ExplicitNull:
                dump_dataclass_field_to_path[name] = f.path[0]
        # TODO I forget why this is needed :o
        if f.skip:
            dump_dataclass_field_to_alias[name] = ExplicitNull
        elif f.dump_alias is not ExplicitNull:
            dump_dataclass_field_to_alias[name] = ''

    else:
        if init:
            if f.load_alias is not None:
                load_dataclass_field_to_alias[name] = f.load_alias
            if f.env_vars is not None:
                load_dataclass_field_to_env[name] = f.env_vars
        if f.skip:
            dump_dataclass_field_to_alias[name] = ExplicitNull
        elif (dump := f.dump_alias) is not None:
            dump_dataclass_field_to_alias[name] = dump if isinstance(dump, str) else dump[0]



# Set up load and dump config for dataclass
def setup_config_for_cls(cls):
    load_dataclass_field_to_alias = per_cls(DATACLASS_FIELD_TO_ALIAS_FOR_LOAD, cls)
    load_dataclass_field_to_env = per_cls(DATACLASS_FIELD_TO_ENV_FOR_LOAD, cls)
    dump_dataclass_field_to_alias = per_cls(DATACLASS_FIELD_TO_ALIAS_FOR_DUMP, cls)

    dataclass_field_to_path = per_cls(DATACLASS_FIELD_TO_ALIAS_PATH_FOR_LOAD, cls)
    dump_dataclass_field_to_path = per_cls(DATACLASS_FIELD_TO_ALIAS_PATH_FOR_DUMP, cls)

    set_paths = False if dataclass_field_to_path else True
    field_to_skip_if = per_cls(DATACLASS_FIELD_TO_SKIP_IF, cls)
    seen_default = False

    for f in dataclass_fields(cls):
        init = f.init
        field_type = f.type = eval_forward_ref_if_needed(f.type, cls)

        if (init and not seen_default
            and (f.default is not MISSING
                 or f.default_factory is not MISSING)):
            seen_default = True

        # isinstance(f, Field) == True

        # Check if the field is a known `Field` subclass. If so, update
        # the class-specific mapping of JSON key to dataclass field name.
        if isinstance(f, Field):
            _process_field(f.name, f, set_paths, init,
                           dataclass_field_to_path,
                           dump_dataclass_field_to_path,
                           load_dataclass_field_to_alias,
                           load_dataclass_field_to_env,
                           dump_dataclass_field_to_alias)

        elif f.metadata:
            if value := f.metadata.get('__remapping__'):
                if isinstance(value, Field):
                    _process_field(f.name, value, set_paths, init,
                                   dataclass_field_to_path,
                                   dump_dataclass_field_to_path,
                                   load_dataclass_field_to_alias,
                                   load_dataclass_field_to_env,
                                   dump_dataclass_field_to_alias)
            elif value := f.metadata.get('__skip_if__'):
                if getattr(value, '__dcw_condition__', False):
                    field_to_skip_if[f.name] = value

        # Check for a "Catch All" field
        if field_type is CatchAll:
            load_dataclass_field_to_alias[CATCH_ALL] \
                = load_dataclass_field_to_env[CATCH_ALL] \
                = dump_dataclass_field_to_alias[CATCH_ALL] \
                = f'{f.name}{"" if f.default is MISSING else "?"}'

        # Check if the field annotation is an `Annotated` type. If so,
        # look for any `Field` objects in the arguments; for each object,
        # call `_process_field`.
        elif is_annotated(field_type):
            for extra in get_args(field_type)[1:]:
                if isinstance(extra, Field):
                    _process_field(f.name, extra, set_paths, init,
                                   dataclass_field_to_path,
                                   dump_dataclass_field_to_path,
                                   load_dataclass_field_to_alias,
                                   load_dataclass_field_to_env,
                                   dump_dataclass_field_to_alias)
                elif getattr(extra, '__dcw_condition__', False):
                    field_to_skip_if[f.name] = extra
                    if not getattr(extra, '_wrapped', False):
                        raise InvalidConditionError(cls, f.name) from None

    SEEN_DEFAULT[cls] = seen_default

    IS_CONFIG_SETUP.add(cls)


def call_meta_initializer_if_needed(cls, package_name=PACKAGE_NAME):
    """
    Calls the Meta initializer when the inner :class:`Meta` is sub-classed.
    """
    # TODO add tests

    # skip classes provided by this library
    if cls.__module__.startswith(f'{package_name}.'):
        return

    cls_name = get_class_name(cls)

    if cls_name in META_INITIALIZER:
        META_INITIALIZER[cls_name](cls)

    # Get the last immediate superclass
    base = cls.__base__

    # skip base `object` and classes provided by this library
    if (base is not object
            and not base.__module__.startswith(f'{package_name}.')):

        base_cls_name = get_class_name(base)

        if base_cls_name in META_INITIALIZER:
            META_INITIALIZER[base_cls_name](cls)
