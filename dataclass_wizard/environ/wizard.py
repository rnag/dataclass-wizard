import json
from dataclasses import MISSING, dataclass, fields, Field
from typing import AnyStr, Callable

from .dumpers import asdict
from .lookups import Env, lookup_exact, clean
from ..abstractions import AbstractEnvWizard
from ..bases import AbstractEnvMeta
from ..bases_meta import BaseEnvWizardMeta
from ..class_helper import (call_meta_initializer_if_needed, get_meta,
                            field_to_env_var, dataclass_field_to_json_field)
from ..decorators import cached_class_property, _alias
from ..enums import Extra
from ..environ.loaders import EnvLoader
from ..errors import ExtraData, MissingVars, ParseError
from ..loaders import get_loader
from ..log import LOG
from ..models import Extras, JSONField
from ..type_def import JSONObject, Encoder, EnvFileType, ExplicitNull
from ..helpers import create_fn, type_name


_to_dataclass = dataclass(init=False)


class EnvWizard(AbstractEnvWizard):
    __slots__ = ()

    class Meta(BaseEnvWizardMeta):
        """
        Inner meta class that can be extended by sub-classes for additional
        customization with the environment load process.
        """
        __slots__ = ()

        # Class attribute to enable detection of the class type.
        __is_inner_meta__ = True

        def __init_subclass__(cls):
            # Set the `__init_subclass__` method here, so we can ensure it
            # doesn't run for the `EnvWizard.Meta` class.
            return cls._init_subclass()

    # noinspection PyMethodParameters
    @cached_class_property
    def __fields__(cls: 'E') -> 'dict[str, Field]':
        cls_fields = {}
        field_to_var = field_to_env_var(cls)

        for field in fields(cls):
            name = field.name
            cls_fields[name] = field

            if isinstance(field, JSONField):
                if not field.json.dump:
                    field_to_json_key = dataclass_field_to_json_field(cls)
                    field_to_json_key[name] = ExplicitNull

                keys = field.json.keys
                if keys:
                    # minor optimization: convert a one-element tuple of `str` to `str`
                    field_to_var[name] = keys[0] if len(keys) == 1 else keys

        return cls_fields

    @_alias(asdict)
    def to_dict(self: 'E', exclude: 'list[str]' = None,
                skip_defaults: bool = False) -> JSONObject:
        """
        Converts the `EnvWizard` subclass to a Python dictionary object that
        is JSON serializable.
        """
        # alias: asdict(self)
        ...

    def to_json(self: 'E', *,
                encoder: Encoder = json.dumps,
                **encoder_kwargs) -> AnyStr:
        """
        Converts the `EnvWizard` subclass to a JSON `string` representation.
        """
        return encoder(asdict(self), **encoder_kwargs)

    # stub for type hinting purposes.
    def __init__(self, *,
                 _env_file: EnvFileType = None,
                 _reload_env: bool = False,
                 **init_kwargs) -> None:
        ...

    def __init_subclass__(cls, *, reload_env=False):

        if reload_env:  # reload cached var names from `os.environ` as needed.
            Env.reload()

        # apply the `@dataclass(init=False)` decorator to `cls`.
        _to_dataclass(cls)

        # Calls the Meta initializer when inner :class:`Meta` is sub-classed.
        call_meta_initializer_if_needed(cls)

        # create and set the `__init__()` method.
        cls.__init__ = cls._init_fn()

    @classmethod
    def _init_fn(cls) -> Callable:
        """
        Returns a generated ``__init__()`` constructor method for the
        :class:`EnvWizard` subclass, vis-à-vis how the ``dataclasses``
        module does it, with a few noticeable differences.
        """

        meta = get_meta(cls, base_cls=AbstractEnvMeta)
        cls_loader = get_loader(cls, base_cls=EnvLoader)

        # A cached mapping of each dataclass field name to its environment
        # variable name; useful so we don't need to do a case transformation
        # (via regex) each time.
        field_to_var = field_to_env_var(cls)

        # The function to case-transform and lookup variables defined in the
        # environment.
        get_env: 'Callable[[str], str | None]' = meta.key_lookup_with_load

        # noinspection PyArgumentList
        extras = Extras(config=None)

        cls_fields: 'dict[str, Field]' = cls.__fields__
        field_names = frozenset(cls_fields)

        _extra = meta.extra
        _meta_env_file = meta.env_file

        locals = {'Env': Env,
                  'EnvFileType': EnvFileType,
                  'MISSING': MISSING,
                  'ParseError': ParseError,
                  'field_names': field_names,
                  'get_env': get_env,
                  'lookup_exact': lookup_exact}

        globals = {'MissingVars': MissingVars,
                   'add_missing_var': _add_missing_var,
                   'cls': cls,
                   'fields_ordered': cls_fields.keys(),
                   'handle_parse_error': _handle_parse_error}

        # parameters to the `__init__()` method.
        init_params = ('self', '*',
                       '_env_file: EnvFileType = None',
                       '_reload_env: bool = False',
                       '**init_kwargs')

        init_body_lines = [
            # reload cached var names from `os.environ` as needed.
            'if _reload_env:',
            '  Env.reload()',
            # update environment with values in the "dot env" files as needed.
            'if _env_file:',
            '  Env.update_with_dotenv(_env_file)',
        ]

        add_line = init_body_lines.append

        if _meta_env_file:
            globals['_dotenv_values'] = Env.dotenv_values(_meta_env_file)
            add_line('elif _env_file is not False:')
            add_line('  Env.update_with_dotenv(dotenv_values=_dotenv_values)')

        # iterate over the dataclass fields and (attempt to) resolve
        # each one.
        add_line('missing_vars = []')
        add_line('has_kwargs = True if init_kwargs else False')

        for name, f in cls_fields.items():
            tp = globals[f'_type_{name}'] = f.type

            # retrieve value (if it exists) for the environment variable
            add_line(f'if has_kwargs and {name!r} in init_kwargs:')
            add_line(f'  value = init_kwargs[{name!r}]')
            add_line('  has_value = True')
            add_line('else:')
            env_var = field_to_var.get(name)
            if env_var:
                var_name = f'_var_{name}'
                globals[var_name] = env_var
                add_line(f'  value = lookup_exact({var_name})')
            else:
                add_line(f'  value = get_env({name!r})')
            add_line('  has_value = value is not MISSING')
            add_line('if has_value:')
            parser_name = f'_parser_{name}'
            globals[parser_name] = cls_loader.get_parser_for_annotation(
                tp, cls, extras)
            add_line('  try:')
            add_line(f'    self.{name} = {parser_name}(value)')
            add_line('  except ParseError as e:')
            add_line(f'    handle_parse_error(e, cls, {name!r}, {env_var!r})')
            # this `else` block means that a value was not received for the
            # field, either via keyword arguments or Environment.
            add_line('else:')
            # check if the field defines a `default` or `default_factory`
            # value; note this is similar to how `dataclasses` does it.
            default_name = f'_dflt_{name}'
            if f.default is not MISSING:
                globals[default_name] = f.default
                add_line(f'  self.{name} = {default_name}')
            elif f.default_factory is not MISSING:
                globals[default_name] = f.default_factory
                add_line(f'  self.{name} = {default_name}()')
            else:
                add_line(f'  add_missing_var(missing_vars, {name!r}, _type_{name})')

        # check for any required fields with missing values
        add_line('if missing_vars:')
        add_line('  raise MissingVars(cls, missing_vars) from None')

        # if keyword arguments are passed in, confirm that all there
        # aren't any "extra" keyword arguments
        if _extra is not Extra.IGNORE:
            add_line('if has_kwargs:')
            # get a list of keyword arguments that don't map to any fields
            add_line('  extra_kwargs = set(init_kwargs) - field_names')
            add_line('  if extra_kwargs:')
            # the default behavior is "DENY", so an error will be raised here.
            if _extra is None or _extra is Extra.DENY:
                globals['ExtraData'] = ExtraData
                add_line('    raise ExtraData(cls, extra_kwargs, list(fields_ordered)) from None')
            else:  # Extra.ALLOW
                # else, if we want to "ALLOW" extra keyword arguments, we need to
                # store those attributes in the instance.
                add_line('    for attr in extra_kwargs:')
                add_line('      setattr(self, attr, init_kwargs[attr])')

        # log the generated `__init__()` method definition, if the Meta's
        # `debug_enabled` flag is enabled.
        if meta.debug_enabled:
            LOG.info('%s.__init__() definition:\n---\ndef __init__(%s):\n  %s',
                     cls.__qualname__,
                     ', '.join(init_params),
                     '\n  '.join(init_body_lines))

        return create_fn('__init__',
                         init_params,
                         init_body_lines,
                         locals=locals,
                         globals=globals,
                         return_type=None)


def _add_missing_var(missing_vars: list, name: str, tp: type):
    # noinspection PyBroadException
    try:
        suggested = tp()
    except Exception:
        suggested = None
    tn = type_name(tp)
    missing_vars.append((name, tn, suggested))


def _handle_parse_error(e: ParseError,
                        cls: type, name: str,
                        var_name: 'str | None'):

    # We run into a parsing error while loading the field
    # value; Add additional info on the Exception object
    # before re-raising it.
    e.class_name = cls
    e.field_name = name
    if var_name is None:
        var_name = Env.cleaned_to_env.get(clean(name), name)
    e.kwargs['env_variable'] = var_name

    raise
