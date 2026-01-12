from __future__ import annotations

from collections import defaultdict
from dataclasses import MISSING
from typing import TYPE_CHECKING

from .bases import AbstractMeta
from .constants import CATCH_ALL, PACKAGE_NAME
from .errors import InvalidConditionError
from .models import CatchAll, Condition
from .type_def import ExplicitNull
from .utils._dataclass_compat import dataclass_fields, SEEN_DEFAULT
from .utils._typing_compat import (eval_forward_ref_if_needed,
                                   get_args,
                                   is_annotated)

if TYPE_CHECKING:
    from .models import Field


# Mapping of main dataclass to its `load` function.
CLASS_TO_LOAD_FUNC = {}

# Mapping of main dataclass to its `dump` function.
CLASS_TO_DUMP_FUNC = {}

# V1: A mapping of dataclass to its loader.
CLASS_TO_LOADER = {}

# V1: A mapping of dataclass to its dumper.
CLASS_TO_DUMPER = {}

# Since the load process in V1 doesn't use Parsers currently, we use a sentinel
# mapping to confirm if we need to setup the load config for a dataclass
# on an initial run.
IS_CONFIG_SETUP = set()

# V1 Load: A cached mapping, per dataclass, of instance field name to alias path
DATACLASS_FIELD_TO_ALIAS_PATH_FOR_LOAD = defaultdict(dict)

# V1 Dump: A cached mapping, per dataclass, of instance field name to alias path
DATACLASS_FIELD_TO_ALIAS_PATH_FOR_DUMP = defaultdict(dict)

# V1 Load: A cached mapping, per dataclass, of instance field name to alias
DATACLASS_FIELD_TO_ALIAS_FOR_LOAD = defaultdict(dict)

# V1 Load: A cached mapping, per dataclass, of instance field name to env var
DATACLASS_FIELD_TO_ENV_FOR_LOAD = defaultdict(dict)

# V1 Dump: A cached mapping, per dataclass, of instance field name to alias
DATACLASS_FIELD_TO_ALIAS_FOR_DUMP: dict[type, dict[str, str]] = defaultdict(dict)

# A cached mapping, per dataclass, of instance field name to JSON field
DATACLASS_FIELD_TO_ALIAS = defaultdict(dict)

# A cached mapping, per dataclass, of instance field name to `SkipIf` condition
DATACLASS_FIELD_TO_SKIP_IF = defaultdict(dict)

# A mapping of dataclass name to its Meta initializer (defined in
# :class:`bases.BaseJSONWizardMeta`), which is only set when the
# :class:`JSONSerializable.Meta` is sub-classed.
META_INITIALIZER = {}


# Mapping of dataclass to its Meta inner class, which will only be set when
# the :class:`JSONSerializable.Meta` is sub-classed.
_META = {}


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


def dataclass_field_to_json_field(cls):

    return DATACLASS_FIELD_TO_ALIAS[cls]


def dataclass_field_to_skip_if(cls):

    return DATACLASS_FIELD_TO_SKIP_IF[cls]


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
                   f: 'Field',
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
    # TODO
    from .models import Field

    load_dataclass_field_to_alias = DATACLASS_FIELD_TO_ALIAS_FOR_LOAD[cls]
    load_dataclass_field_to_env = DATACLASS_FIELD_TO_ENV_FOR_LOAD[cls]
    dump_dataclass_field_to_alias = DATACLASS_FIELD_TO_ALIAS_FOR_DUMP[cls]

    dataclass_field_to_path = DATACLASS_FIELD_TO_ALIAS_PATH_FOR_LOAD[cls]
    dump_dataclass_field_to_path = DATACLASS_FIELD_TO_ALIAS_PATH_FOR_DUMP[cls]

    set_paths = False if dataclass_field_to_path else True
    dataclass_field_to_skip_if = DATACLASS_FIELD_TO_SKIP_IF[cls]
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
                if isinstance(value, Condition):
                    dataclass_field_to_skip_if[f.name] = value

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
                elif isinstance(extra, Condition):
                    dataclass_field_to_skip_if[f.name] = extra
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


def get_meta(cls, base_cls=AbstractMeta):
    """
    Retrieves the Meta config for the :class:`AbstractJSONWizard` subclass.

    This config is set when the inner :class:`Meta` is sub-classed.
    """
    return _META.get(cls, base_cls)


def create_meta(cls, cls_name=None, **kwargs):
    """
    Sets the Meta config for the :class:`AbstractJSONWizard` subclass.

    WARNING: Only use if the Meta config is undefined,
      e.g. `get_meta` for the `cls` returns `base_cls`.

    """
    from .bases_meta import BaseJSONWizardMeta

    cls_dict = {'__slots__': (), **kwargs}

    meta = type((cls_name or cls.__name__) + 'Meta',
                (BaseJSONWizardMeta, ),
                cls_dict)

    _META[cls] = meta


def is_builtin(o):

    # Fast path: check if object is a builtin singleton
    # TODO replace with `match` statement once we drop support for Python 3.9
    # match x:
    #     case None: pass
    #     case True: pass
    #     case False: pass
    #     case builtins.Ellipsis: pass
    if o in {None, True, False, ...}:
        return True

    return getattr(o, '__class__', o).__module__ == 'builtins'


def create_new_class(
        class_or_instance, bases,
        suffix=None, attr_dict=None):

    if not suffix and bases:
        suffix = get_class_name(bases[0])

    new_cls_name = f'{get_class_name(class_or_instance)}{suffix}'

    return type(
        new_cls_name,
        bases,
        attr_dict or {'__slots__': ()}
    )


def get_class_name(class_or_instance):

    try:
        return class_or_instance.__qualname__
    except AttributeError:
        # We're dealing with a dataclass instance
        return type(class_or_instance).__qualname__


def get_outer_class_name(inner_cls, default=None, raise_=True):

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

    return obj if isinstance(obj, type) else type(obj)


def is_subclass(obj, base_cls):

    cls = obj if isinstance(obj, type) else type(obj)
    return issubclass(cls, base_cls)


def is_subclass_safe(cls, class_or_tuple):

    try:
        return issubclass(cls, class_or_tuple)
    except TypeError:
        return False
