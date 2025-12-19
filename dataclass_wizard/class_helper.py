from collections import defaultdict
from dataclasses import MISSING, fields
from typing import TYPE_CHECKING

from .bases import AbstractMeta
from .constants import CATCH_ALL, PACKAGE_NAME
from .errors import InvalidConditionError
from .models import JSONField, JSON, Extras, PatternedDT, CatchAll, Condition
from .type_def import ExplicitNull
from .utils.dict_helper import DictWithLowerStore
from .utils.typing_compat import (
    is_annotated, get_args, eval_forward_ref_if_needed
)

if TYPE_CHECKING:
    from .v1.models import Field

# A cached mapping of dataclass to the list of fields, as returned by
# `dataclasses.fields()`.
FIELDS = {}

# A cached mapping of dataclass to a mapping of field name
# to default value, as returned by `dataclasses.fields()`.
FIELD_TO_DEFAULT = {}

# Mapping of main dataclass to its `load` function.
CLASS_TO_LOAD_FUNC = {}

# Mapping of main dataclass to its `dump` function.
CLASS_TO_DUMP_FUNC = {}

# A mapping of dataclass to its loader.
CLASS_TO_LOADER = {}

# V1: A mapping of dataclass to its loader.
CLASS_TO_V1_LOADER = {}

# A mapping of dataclass to its dumper.
CLASS_TO_DUMPER = {}

# V1: A mapping of dataclass to its dumper.
CLASS_TO_V1_DUMPER = {}

# A cached mapping of a dataclass to each of its case-insensitive field names
# and load hook.
FIELD_NAME_TO_LOAD_PARSER = {}

# Since the load process in V1 doesn't use Parsers currently, we use a sentinel
# mapping to confirm if we need to setup the load config for a dataclass
# on an initial run.
IS_V1_CONFIG_SETUP = set()

# Since the dump process doesn't use Parsers currently, we use a sentinel
# mapping to confirm if we need to setup the dump config for a dataclass
# on an initial run.
IS_DUMP_CONFIG_SETUP = {}

# A cached mapping, per dataclass, of JSON field to instance field name
JSON_FIELD_TO_DATACLASS_FIELD = defaultdict(dict)

# A cached mapping, per dataclass, of instance field name to JSON path
DATACLASS_FIELD_TO_JSON_PATH = defaultdict(dict)

# V1 Load: A cached mapping, per dataclass, of instance field name to alias path
DATACLASS_FIELD_TO_ALIAS_PATH_FOR_LOAD = defaultdict(dict)

# V1 Dump: A cached mapping, per dataclass, of instance field name to alias path
DATACLASS_FIELD_TO_ALIAS_PATH_FOR_DUMP = defaultdict(dict)

# V1 Load: A cached mapping, per dataclass, of instance field name to alias
DATACLASS_FIELD_TO_ALIAS_FOR_LOAD = defaultdict(dict)

# V1 Dump: A cached mapping, per dataclass, of instance field name to alias
DATACLASS_FIELD_TO_ALIAS_FOR_DUMP: dict[type, dict[str, str]] = defaultdict(dict)

# A cached mapping, per dataclass, of instance field name to JSON field
DATACLASS_FIELD_TO_ALIAS = defaultdict(dict)

# A cached mapping, per dataclass, of instance field name to `SkipIf` condition
DATACLASS_FIELD_TO_SKIP_IF = defaultdict(dict)

# A cached mapping, per `EnvWizard` subclass, of field name to env variable
FIELD_TO_ENV_VAR = defaultdict(dict)

# A mapping of dataclass name to its Meta initializer (defined in
# :class:`bases.BaseJSONWizardMeta`), which is only set when the
# :class:`JSONSerializable.Meta` is sub-classed.
META_INITIALIZER = {}


# Mapping of dataclass to its Meta inner class, which will only be set when
# the :class:`JSONSerializable.Meta` is sub-classed.
_META = {}


def dataclass_to_dumper(cls):

    return CLASS_TO_DUMPER[cls]


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


def json_field_to_dataclass_field(cls):

    return JSON_FIELD_TO_DATACLASS_FIELD[cls]


def dataclass_field_to_json_path(cls):

    return DATACLASS_FIELD_TO_JSON_PATH[cls]


def dataclass_field_to_json_field(cls):

    return DATACLASS_FIELD_TO_ALIAS[cls]


def dataclass_field_to_skip_if(cls):

    return DATACLASS_FIELD_TO_SKIP_IF[cls]


def field_to_env_var(cls):
    """
    Returns a mapping of field in the `EnvWizard` subclass to env variable.
    """
    return FIELD_TO_ENV_VAR[cls]


def dataclass_field_to_load_parser(
        cls_loader,
        cls,
        config,
        save=True):

    if cls not in FIELD_NAME_TO_LOAD_PARSER:
        return _setup_load_config_for_cls(cls_loader, cls, config, save)

    return FIELD_NAME_TO_LOAD_PARSER[cls]


def _setup_load_config_for_cls(cls_loader,
                               cls,
                               config,
                               save=True
                               ):

    json_to_dataclass_field = JSON_FIELD_TO_DATACLASS_FIELD[cls]

    dataclass_field_to_path = DATACLASS_FIELD_TO_JSON_PATH[cls]
    set_paths = False if dataclass_field_to_path else True
    v1_disabled = config is None or not config.v1

    name_to_parser = {}

    for f in  dataclass_init_fields(cls):
        field_extras: Extras = {'config': config}

        field_type = f.type = eval_forward_ref_if_needed(f.type, cls)

        # isinstance(f, Field) == True

        # Check if the field is a known `Field` subclass. If so, update
        # the class-specific mapping of JSON key to dataclass field name.
        if isinstance(f, JSONField):

            if f.json.path:
                keys = f.json.keys
                json_to_dataclass_field[keys[0]] = ExplicitNull
                if set_paths:
                    dataclass_field_to_path[f.name] = keys
            else:
                for key in f.json.keys:
                    json_to_dataclass_field[key] = f.name

        elif f.metadata:
            if value := f.metadata.get('__remapping__'):
                if isinstance(value, JSON):
                    if value.path:
                        keys = value.keys
                        json_to_dataclass_field[keys[0]] = ExplicitNull
                        if set_paths:
                            dataclass_field_to_path[f.name] = keys
                    else:
                        for key in value.keys:
                            json_to_dataclass_field[key] = f.name

        # Check for a "Catch All" field
        if field_type is CatchAll:
            json_to_dataclass_field[CATCH_ALL] = (
                f'{f.name}{"" if f.default is MISSING else "?"}'
            )

        # Check if the field annotation is an `Annotated` type. If so,
        # look for any `JSON` objects in the arguments; for each object,
        # update the class-specific mapping of JSON key to dataclass field
        # name.
        elif is_annotated(field_type):
            ann_type, *extras = get_args(field_type)
            for extra in extras:
                if isinstance(extra, JSON):
                    if extra.path:
                        keys = extra.keys
                        json_to_dataclass_field[keys[0]] = ExplicitNull
                        if set_paths:
                            dataclass_field_to_path[f.name] = keys
                    else:
                        for key in extra.keys:
                            json_to_dataclass_field[key] = f.name
                elif isinstance(extra, PatternedDT):
                    field_extras['pattern'] = extra

        # Lookup the Parser (dispatcher) for each field based on its annotated
        # type, and then cache it so we don't need to lookup each time.
        #
        # Changed in v0.31.0: Get the __call__() method as defined
        # on `AbstractParser`, if it exists
        if v1_disabled:
            name_to_parser[f.name] = getattr(p := cls_loader.get_parser_for_annotation(
                field_type, cls, field_extras
            ), '__call__', p)

    if v1_disabled:
        parser_dict = DictWithLowerStore(name_to_parser)
        # only cache the load parser for the class if `save` is enabled
        if save:
            FIELD_NAME_TO_LOAD_PARSER[cls] = parser_dict

        return parser_dict

    return None


def setup_dump_config_for_cls_if_needed(cls):

    if cls in IS_DUMP_CONFIG_SETUP:
        return

    field_to_alias = DATACLASS_FIELD_TO_ALIAS[cls]

    field_to_path = DATACLASS_FIELD_TO_JSON_PATH[cls]
    set_paths = False if field_to_path else True

    dataclass_field_to_skip_if = DATACLASS_FIELD_TO_SKIP_IF[cls]

    for f in dataclass_fields(cls):

        field_type = f.type = eval_forward_ref_if_needed(f.type, cls)

        # isinstance(f, Field) == True

        # Check if the field is a known `Field` subclass. If so, update
        # the class-specific mapping of dataclass field name to JSON key.
        if isinstance(f, JSONField):
            if not f.json.dump:
                field_to_alias[f.name] = ExplicitNull
            elif f.json.all:
                keys = f.json.keys
                if f.json.path:
                    if set_paths:
                        field_to_path[f.name] = keys
                    field_to_alias[f.name] = ''
                else:
                    field_to_alias[f.name] = keys[0]

        elif f.metadata:
            if value := f.metadata.get('__remapping__'):
                if isinstance(value, JSON) and value.all:
                    keys = value.keys
                    if value.path:
                        if set_paths:
                            field_to_path[f.name] = keys
                        field_to_alias[f.name] = ''
                    else:
                        field_to_alias[f.name] = keys[0]
            elif value := f.metadata.get('__skip_if__'):
                if isinstance(value, Condition):
                    dataclass_field_to_skip_if[f.name] = value

        # Check for a "Catch All" field
        if field_type is CatchAll:
            field_to_alias[f.name] = ExplicitNull
            field_to_alias[CATCH_ALL] = f.name

        # Check if the field annotation is an `Annotated` type. If so,
        # look for any `JSON` objects in the arguments; for each object,
        # update the class-specific mapping of dataclass field name to JSON
        # key.
        if is_annotated(field_type):
            for extra in get_args(field_type)[1:]:
                if isinstance(extra, JSON):
                    if not extra.dump:
                        field_to_alias[f.name] = ExplicitNull
                    elif extra.all:
                        keys = extra.keys
                        if extra.path:
                            if set_paths:
                                field_to_path[f.name] = keys
                            field_to_alias[f.name] = ''
                        else:
                            field_to_alias[f.name] = keys[0]
                elif isinstance(extra, Condition):
                    if not getattr(extra, '_wrapped', False):
                        raise InvalidConditionError(cls, f.name) from None

                    dataclass_field_to_skip_if[f.name] = extra

    # Mark the dataclass as processed, as the initial dump process is set up.
    IS_DUMP_CONFIG_SETUP[cls] = True


def v1_dataclass_field_to_alias_for_dump(cls):

    if cls not in IS_V1_CONFIG_SETUP:
        _setup_v1_config_for_cls(cls)

    return DATACLASS_FIELD_TO_ALIAS_FOR_DUMP[cls]


def v1_dataclass_field_to_alias_for_load(
    cls,
    # cls_loader,
    # config,
    # save=True
):

    if cls not in IS_V1_CONFIG_SETUP:
        _setup_v1_config_for_cls(cls)

    return DATACLASS_FIELD_TO_ALIAS_FOR_LOAD[cls]

def _process_field(name: str,
                   f: 'Field',
                   set_paths: bool,
                   init: bool,
                   load_dataclass_field_to_path,
                   dump_dataclass_field_to_path,
                   load_dataclass_field_to_alias,
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
        if init and f.load_alias is not None:
            load_dataclass_field_to_alias[name] = f.load_alias
        if f.skip:
            dump_dataclass_field_to_alias[name] = ExplicitNull
        elif (dump := f.dump_alias) is not None:
            dump_dataclass_field_to_alias[name] = dump if isinstance(dump, str) else dump[0]



# Set up load and dump config for dataclass
def _setup_v1_config_for_cls(cls):
    from .v1.models import Field

    load_dataclass_field_to_alias = DATACLASS_FIELD_TO_ALIAS_FOR_LOAD[cls]
    dump_dataclass_field_to_alias = DATACLASS_FIELD_TO_ALIAS_FOR_DUMP[cls]

    dataclass_field_to_path = DATACLASS_FIELD_TO_ALIAS_PATH_FOR_LOAD[cls]
    dump_dataclass_field_to_path = DATACLASS_FIELD_TO_ALIAS_PATH_FOR_DUMP[cls]

    set_paths = False if dataclass_field_to_path else True
    dataclass_field_to_skip_if = DATACLASS_FIELD_TO_SKIP_IF[cls]

    for f in dataclass_fields(cls):
        init = f.init
        field_type = f.type = eval_forward_ref_if_needed(f.type, cls)

        # isinstance(f, Field) == True

        # Check if the field is a known `Field` subclass. If so, update
        # the class-specific mapping of JSON key to dataclass field name.
        if isinstance(f, Field):
            _process_field(f.name, f, set_paths, init,
                           dataclass_field_to_path,
                           dump_dataclass_field_to_path,
                           load_dataclass_field_to_alias,
                           dump_dataclass_field_to_alias)

        elif f.metadata:
            if value := f.metadata.get('__remapping__'):
                if isinstance(value, Field):
                    _process_field(f.name, value, set_paths, init,
                                   dataclass_field_to_path,
                                   dump_dataclass_field_to_path,
                                   load_dataclass_field_to_alias,
                                   dump_dataclass_field_to_alias)
            elif value := f.metadata.get('__skip_if__'):
                if isinstance(value, Condition):
                    dataclass_field_to_skip_if[f.name] = value

        # Check for a "Catch All" field
        if field_type is CatchAll:
            load_dataclass_field_to_alias[CATCH_ALL] \
                = dump_dataclass_field_to_alias[CATCH_ALL] \
                = f'{f.name}{"" if f.default is MISSING else "?"}'

        # Check if the field annotation is an `Annotated` type. If so,
        # look for any `JSON` objects in the arguments; for each object,
        # update the class-specific mapping of JSON key to dataclass field
        # name.
        elif is_annotated(field_type):
            for extra in get_args(field_type)[1:]:
                if isinstance(extra, Field):
                    _process_field(f.name, extra, set_paths, init,
                                   dataclass_field_to_path,
                                   dump_dataclass_field_to_path,
                                   load_dataclass_field_to_alias,
                                   dump_dataclass_field_to_alias)
                elif isinstance(extra, Condition):
                    dataclass_field_to_skip_if[f.name] = extra
                    if not getattr(extra, '_wrapped', False):
                        raise InvalidConditionError(cls, f.name) from None

    IS_V1_CONFIG_SETUP.add(cls)


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


def dataclass_fields(cls):

    if cls not in FIELDS:
        FIELDS[cls] = fields(cls)

    return FIELDS[cls]


def dataclass_init_fields(cls, as_list=False):
    init_fields = [f for f in dataclass_fields(cls) if f.init]
    return init_fields if as_list else tuple(init_fields)


def dataclass_field_names(cls):

    return tuple(f.name for f in dataclass_fields(cls))


def dataclass_init_field_names(cls):

    return tuple(f.name for f in dataclass_init_fields(cls))


def dataclass_field_to_default(cls):

    if cls not in FIELD_TO_DEFAULT:
        defaults = FIELD_TO_DEFAULT[cls] = {}
        for f in dataclass_fields(cls):
            if f.default is not MISSING:
                defaults[f.name] = f.default
            elif f.default_factory is not MISSING:
                defaults[f.name] = f.default_factory()

    return FIELD_TO_DEFAULT[cls]


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
