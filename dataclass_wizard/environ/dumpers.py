
from typing import List, Any, Optional, Callable

from ..abstractions import E
from ..bases import META, AbstractEnvMeta
from ..class_helper import (
    dataclass_field_to_json_field,
    _CLASS_TO_DUMP_FUNC, _META,
)
from ..dumpers import get_dumper, _asdict_inner
from ..type_def import (
    ExplicitNull, JSONObject, T
)
from ..utils.string_conv import to_snake_case


def asdict(cls: E,
           *, dict_factory=dict,
           exclude: List[str] = None, **kwargs) -> JSONObject:
    """Return the fields of an `EnvWizard` subclass as a new dictionary
    mapping field names to field values.

    Example usage::

      class MyEnv(EnvWizard):
          x: int
          y: str

      serialized = asdict(MyEnv)

    When directly invoking this function, an optional Meta configuration for
    the `EnvWizard` subclass can be specified via ``DumpMeta``; by default,
    this will apply recursively to any nested subclasses. Here's a sample
    usage of this below::

        >>> DumpMeta(key_transform='CAMEL').bind_to(MyClass)
        >>> asdict(MyClass(my_str="value"))

    If given, 'dict_factory' will be used instead of built-in dict.
    The function applies recursively to field values that are
    `EnvWizard` subclasses. This will also look into built-in containers:
    tuples, lists, and dicts.
    """
    try:
        dump = _CLASS_TO_DUMP_FUNC[cls]
    except KeyError:
        dump = dump_func_for_env_subclass(cls)

    return dump(cls, dict_factory, exclude, None, **kwargs)


def dump_func_for_env_subclass(cls: E,
                               config: Optional[META] = None,
                               ) -> Callable[[E, Any, Any, Any], JSONObject]:

    # Get the dumper for the class, or create a new one as needed.
    cls_dumper = get_dumper(cls)

    # Get the meta config for the class, or the default config otherwise.
    #
    # Only add the key transform if Meta config has not been specified
    # for the `EnvWizard` subclass.
    if cls in _META:
        meta = _META[cls]
    else:
        meta = AbstractEnvMeta
        cls_dumper.transform_dataclass_field = to_snake_case

    # This contains the dump hooks for the Env subclass. If the class
    # sub-classes from `DumpMixIn`, these hooks could be customized.
    hooks = cls_dumper.__DUMP_HOOKS__

    # A cached mapping of each dataclass field to the resolved key name in a
    # JSON or dictionary object; useful so we don't need to do a case
    # transformation (via regex) each time.
    env_subclass_to_json_field = dataclass_field_to_json_field(cls)

    # A cached mapping of `EnvWizard` field name to its default value, either
    # via a `default` or `default_factory` argument.
    cls_dict = cls.__dict__
    field_to_default = {f: cls_dict[f] for f in cls.__fields__ if f in cls_dict}

    # A collection of field names in the dataclass.
    field_names = cls.__fields__.keys()

    def cls_asdict(obj: T, dict_factory=dict,
                   exclude: List[str] = None,
                   skip_defaults=meta.skip_defaults) -> JSONObject:
        """
        Serialize an `EnvWizard` subclass `cls` to a Python dictionary object.
        """

        # Call the optional hook that runs before we process the subclass
        cls_dumper.__pre_as_dict__(obj)

        # This a list that contains a mapping of each `EnvWizard` field to its
        # serialized value.
        result = []

        # Loop over the `EnvWizard` fields
        for field in field_names:

            # Get the resolved JSON field name
            try:
                json_field = env_subclass_to_json_field[field]

            except KeyError:
                # Normalize the Env field name (by default to camel
                # case)
                json_field = cls_dumper.transform_dataclass_field(field)
                env_subclass_to_json_field[field] = json_field

            # Exclude any fields that are explicitly ignored.
            if json_field is ExplicitNull:
                continue
            if exclude and field in exclude:
                continue

            # -- This line is *mostly* the same as in the original version --
            fv = getattr(obj, field)

            # Check if we need to strip defaults, and the field currently
            # is assigned a default value.
            #
            # TODO: maybe it makes sense to move this logic to a separate
            #   function, as it might be slightly more performant.
            if skip_defaults and field in field_to_default \
                    and fv == field_to_default[field]:
                continue

            value = _asdict_inner(fv, dict_factory, hooks, config, None)

            # -- This line is *mostly* the same as in the original version --
            result.append((json_field, value))

        # -- This line is the same as in the original version --
        return dict_factory(result)

    # In any case, save the dump function for the class, so we don't need to
    # run this logic each time.
    _CLASS_TO_DUMP_FUNC[cls] = cls_asdict

    return cls_asdict
