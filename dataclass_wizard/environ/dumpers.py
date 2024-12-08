
from typing import List, Any, Optional, Callable, Dict, Type

from .loaders import EnvLoader
from .. import EnvMeta
from ..bases import AbstractEnvMeta, META
from ..class_helper import (
    dataclass_field_to_default,
    dataclass_field_to_json_field,
    CLASS_TO_DUMP_FUNC, _META, dataclass_field_to_load_parser, dataclass_field_to_json_path, dataclass_field_names,
    dataclass_field_to_skip_if, is_builtin, setup_dump_config_for_cls_if_needed, get_meta,
)
from ..constants import CATCH_ALL, TAG
from ..dumpers import get_dumper, _asdict_inner
from ..enums import LetterCase
from ..errors import show_deprecation_warning
from ..models import Condition, get_skip_if_condition, finalize_skip_if
from ..type_def import ExplicitNull, JSONObject, T
from ..utils.dataclass_compat import _set_new_attribute
from ..utils.dict_helper import NestedDict
from ..utils.function_builder import FunctionBuilder


def asdict(o: T,
           *, cls=None,
           dict_factory=dict,
           exclude: 'Collection[str] | None' = None,
           **kwargs) -> JSONObject:
    # noinspection PyUnresolvedReferences
    """Return the fields of an instance of a `EnvWizard` subclass as a new
    dictionary mapping field names to field values.

    Example usage::

      class MyEnv(EnvWizard):
          x: int
          y: str

      env = MyEnv()
      serialized = asdict(env)

    When directly invoking this function, an optional Meta configuration for
    the `EnvWizard` subclass can be specified via ``EnvMeta``; by default,
    this will apply recursively to any nested subclasses. Here's a sample
    usage of this below::

        >>> EnvMeta(key_transform_with_dump='CAMEL').bind_to(MyClass)
        >>> asdict(MyClass(my_str="value"))

    If given, 'dict_factory' will be used instead of built-in dict.
    The function applies recursively to field values that are
    `EnvWizard` subclasses. This will also look into built-in containers:
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
        dump = dump_func_for_dataclass(cls)

    return dump(o, dict_factory, exclude, **kwargs)


def dump_func_for_dataclass(cls: Type['E'],
                            config: Optional[META] = None,
                            nested_cls_to_dump_func: Dict[Type, Any] = None,
                            ) -> Callable[['E', Any, Any, Any], JSONObject]:

    # TODO dynamically generate for multiple nested classes at once

    # Get the dumper for the class, or create a new one as needed.
    cls_dumper = get_dumper(cls)

    # Get the meta config for the class, or the default config otherwise.
    meta = get_meta(cls, AbstractEnvMeta)

    # Check if we're being run for the main dataclass or for a nested one.
    is_main_class = nested_cls_to_dump_func is None

    if is_main_class:  # we are being run for the main dataclass
        nested_cls_to_dump_func = {}
        # If the `recursive` flag is enabled and a Meta config is provided,
        # apply the Meta recursively to any nested classes.
        if meta.recursive and meta is not AbstractEnvMeta:
            config = meta

    # we are being run for a nested dataclass
    elif config:
        # we want to apply the meta config from the main dataclass
        # recursively.
        meta = meta | config
        meta.bind_to(cls, is_default=False)

    # This contains the dump hooks for the dataclass. If the class
    # sub-classes from `DumpMixIn`, these hooks could be customized.
    hooks = cls_dumper.__DUMP_HOOKS__

    # Set up the initial dump config for the dataclass.
    setup_dump_config_for_cls_if_needed(cls)

    # A cached mapping of each dataclass field to the resolved key name in a
    # JSON or dictionary object; useful so we don't need to do a case
    # transformation (via regex) each time.
    dataclass_to_json_field = dataclass_field_to_json_field(cls)

    # A cached mapping of dataclass field name to its default value, either
    # via a `default` or `default_factory` argument.
    field_to_default = dataclass_field_to_default(cls)

    # A cached mapping of dataclass field name to its SkipIf condition.
    field_to_skip_if = dataclass_field_to_skip_if(cls)

    # A collection of field names in the dataclass.
    field_names = dataclass_field_names(cls)

    # TODO: Check if we need to auto-assign tags for dataclasses in `Union` types.
    # if meta.auto_assign_tags:
    #     # Unfortunately, we can't handle this as part of the dump process, as
    #     # we don't process the class annotations here. So instead, generate
    #     # the load parser for each field  (if needed), but don't cache the
    #     # result, as it's conceivable we might yet call `LoadMeta` later.
    #     from ..loaders import get_loader
    #     cls_loader = get_loader(cls, base_cls=EnvLoader)
    #     # Use the cached result if it exists, but don't cache it ourselves.
    #     _ = dataclass_field_to_load_parser(
    #         cls_loader, cls, config, save=False)

    # Tag key to populate when a dataclass is in a `Union` with other types.
    # tag_key = meta.tag_key or TAG

    catch_all_field = dataclass_to_json_field.get(CATCH_ALL)
    has_catch_all = catch_all_field is not None

    field_to_path = dataclass_field_to_json_path(cls)
    num_paths = len(field_to_path)
    has_json_paths = True if num_paths else False

    skip_defaults = True if meta.skip_defaults or meta.skip_defaults_if else False

    _locals = {
        'config': config,
        'asdict': _asdict_inner,
        'hooks': hooks,
        'cls_to_asdict': nested_cls_to_dump_func,
        'cls_dump_fn': dump_func_for_dataclass,
    }

    _globals = {
        'T': T,
    }

    skip_if_condition = get_skip_if_condition(
        meta.skip_if, _locals, '_skip_value')

    skip_defaults_if_condition = get_skip_if_condition(
        meta.skip_defaults_if, _locals, '_skip_defaults_value')

    # Initialize FuncBuilder
    fn_gen = FunctionBuilder()

    # Code for `cls_asdict`
    with fn_gen.function('cls_asdict',
                         ['o:T',
                          'dict_factory=dict',
                          "exclude:'list[str]|None'=None",
                          f'skip_defaults:bool={skip_defaults}'],
                         'JSONObject',
                         _locals):

        if (
            _pre_dict := getattr(cls, '_pre_dict', None)
        ) is not None:
            # class defines a `_pre_dict()`
            _locals['__pre_dict__'] = _pre_dict
            fn_gen.add_line('__pre_dict__(o)')
        elif (
            _pre_dict := getattr(cls_dumper, '__pre_as_dict__', None)
        ) is not None:
            # deprecated since v0.28.0
            # subclass of `DumpMixin` defines a `__pre_as_dict__()`
            reason = "use `_pre_dict` instead - no need to subclass from DumpMixin"
            show_deprecation_warning(_pre_dict, reason)

            _locals['__pre_dict__'] = _pre_dict

            # Call the optional hook that runs before we process the dataclass
            fn_gen.add_line('__pre_dict__(o)')

        # Initialize result list to hold field mappings
        fn_gen.add_line("result = []")

        if has_json_paths:
            _locals['NestedDict'] = NestedDict
            fn_gen.add_line('paths = NestedDict()')

        if field_names:

            skip_field_assignments = []
            exclude_assignments = []
            skip_default_assignments = []
            field_assignments = []

            # Loop over the dataclass fields
            for i, field in enumerate(field_names):
                skip_field = f'_skip_{i}'
                skip_if_field = f'_skip_if_{i}'
                default_value = f'_default_{i}'

                skip_field_assignments.append(skip_field)
                exclude_assignments.append(
                    f'{skip_field}={field!r} in exclude'
                )
                if field in field_to_default:
                    if skip_defaults_if_condition:
                        _final_skip_if = finalize_skip_if(
                            meta.skip_defaults_if, f'o.{field}', skip_defaults_if_condition)
                        skip_default_assignments.append(
                            f"{skip_field} = {skip_field} or {_final_skip_if}"
                        )
                    else:
                        _locals[default_value] = field_to_default[field]
                        skip_default_assignments.append(
                            f"{skip_field} = {skip_field} or o.{field} == {default_value}"
                        )

                # Get the resolved JSON field name
                try:
                    json_field = dataclass_to_json_field[field]
                except KeyError:
                    # Normalize the dataclass field name (by default to camel
                    # case)
                    json_field = cls_dumper.transform_dataclass_field(field)
                    dataclass_to_json_field[field] = json_field

                # Exclude any dataclass fields that are explicitly ignored.
                if json_field is not ExplicitNull:
                    # If field has an explicit `SkipIf` condition
                    if field in field_to_skip_if:
                        _skip_condition = field_to_skip_if[field]
                        _skip_if = get_skip_if_condition(
                            _skip_condition, _locals, skip_if_field)
                        _final_skip_if = finalize_skip_if(
                            _skip_condition, f'o.{field}', _skip_if)
                        field_assignments.append(f'if not ({skip_field} or {_final_skip_if}):')
                    # If Meta `skip_if` has a value
                    elif skip_if_condition:
                        _final_skip_if = finalize_skip_if(
                            meta.skip_if, f'o.{field}', skip_if_condition)
                        field_assignments.append(f'if not ({skip_field} or {_final_skip_if}):')
                    # Else, proceed as normal
                    else:
                        field_assignments.append(f"if not {skip_field}:")

                    if json_field:
                        field_assignments.append(f"  result.append(('{json_field}',"
                                                 f"asdict(o.{field},dict_factory,hooks,config,cls_to_asdict,cls_dump_fn)))")
                    # Empty string, will be the case for a dataclass
                    # field which specifies a "JSON Path".
                    else:
                        path = field_to_path[field]
                        key_part = ''.join(f'[{p!r}]' for p in path)
                        field_assignments.append(
                            f'  paths{key_part} = asdict(o.{field},dict_factory,hooks,config,cls_to_asdict,cls_dump_fn)')

                elif has_catch_all and catch_all_field == field:
                    if field in field_to_default:
                        field_assignments.append(f"if o.{field} != {default_value} and not {skip_field}:")
                    else:
                        field_assignments.append(f"if not {skip_field}:")
                    field_assignments.append(f"  for k, v in o.{field}.items():")
                    field_assignments.append("    result.append((k,"
                                             "asdict(v,dict_factory,hooks,config,cls_to_asdict,cls_dump_fn)))")

            with fn_gen.if_('exclude is None'):
                fn_gen.add_line('='.join(skip_field_assignments) + '=False')
            with fn_gen.else_():
                fn_gen.add_line(';'.join(exclude_assignments))

            if skip_default_assignments:
                with fn_gen.if_('skip_defaults'):
                    fn_gen.add_lines(*skip_default_assignments)

            fn_gen.add_lines(*field_assignments)

        if has_json_paths:
            fn_gen.add_line("result and paths.update(result); result = paths")

        # Return the final dictionary result
        # if meta.tag:
        #     fn_gen.add_line("result = dict_factory(result)")
        #     fn_gen.add_line(f"result[{tag_key!r}] = {meta.tag!r}")
        #     # Return the result with the tag added
        #     fn_gen.add_line("return result")
        # else:
        fn_gen.add_line("return dict_factory(result)")

    # Compile the code into a dynamic string
    functions = fn_gen.create_functions(_globals)

    cls_asdict = functions['cls_asdict']

    asdict_func = cls_asdict

    # In any case, save the dump function for the class, so we don't need to
    # run this logic each time.
    if is_main_class:
        # Check if the class has a `to_dict`, and it's
        # equivalent to `asdict`.
        if getattr(cls, 'to_dict', None) is asdict:
            _set_new_attribute(cls, 'to_dict', asdict_func)
        CLASS_TO_DUMP_FUNC[cls] = asdict_func
    else:
        nested_cls_to_dump_func[cls] = asdict_func

    return asdict_func
