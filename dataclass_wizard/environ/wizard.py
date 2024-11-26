import json
import logging
from dataclasses import MISSING, dataclass, fields, Field
from typing import AnyStr, Callable, dataclass_transform

from .dumpers import asdict
from .lookups import Env, lookup_exact, clean
from ..abstractions import AbstractEnvWizard
from ..bases import AbstractEnvMeta
from ..bases_meta import BaseEnvWizardMeta, LoadMeta, EnvMeta
from ..class_helper import (call_meta_initializer_if_needed, get_meta,
                            field_to_env_var, dataclass_field_to_json_field)
from ..decorators import cached_class_property, _alias
from ..environ.loaders import EnvLoader
from ..errors import ExtraData, MissingVars, ParseError, type_name
from ..loaders import get_loader
from ..models import Extras, JSONField
from ..type_def import JSONObject, Encoder, EnvFileType, ExplicitNull
from ..utils.function_builder import FunctionBuilder

_to_dataclass = dataclass(init=False)


@dataclass_transform(kw_only_default=True)
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

    # # stub for type hinting purposes.
    # def __init__(self, *,
    #              _env_file: EnvFileType = None,
    #              _reload_env: bool = False,
    #              **init_kwargs) -> None:
    #     ...

    def __init_subclass__(cls, *, reload_env=False, debug=False):

        if reload_env:  # reload cached var names from `os.environ` as needed.
            Env.reload()

        # apply the `@dataclass(init=False)` decorator to `cls`.
        _to_dataclass(cls)

        if debug:
            default_lvl = logging.DEBUG
            logging.basicConfig(level=default_lvl)
            # minimum logging level for logs by this library
            min_level = default_lvl if isinstance(debug, bool) else debug
            # set `debug_enabled` flag for the class's Meta
            EnvMeta(debug_enabled=min_level).bind_to(cls)

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

        _meta_env_file = meta.env_file

        _locals = {'Env': Env,
                   'EnvFileType': EnvFileType,
                   'MISSING': MISSING,
                   'ParseError': ParseError,
                   'field_names': field_names,
                   'get_env': get_env,
                   'lookup_exact': lookup_exact}

        _globals = {'MissingVars': MissingVars,
                    'add': _add_missing_var,
                    'cls': cls,
                    'fields_ordered': cls_fields.keys(),
                    'handle_err': _handle_parse_error}

        # parameters to the `__init__()` method.
        init_params = ['self',
                       'env_file:EnvFileType=None',
                       'reload_env:bool=False']

        fn_gen = FunctionBuilder()

        with fn_gen.function('__init__', init_params, None):
            # reload cached var names from `os.environ` as needed.
            with fn_gen.if_('reload_env'):
                fn_gen.add_line('Env.reload()')
            # update environment with values in the "dot env" files as needed.
            if _meta_env_file:
                fn = fn_gen.elif_
                _globals['_dotenv_values'] = Env.dotenv_values(_meta_env_file)
                with fn_gen.if_('env_file is None'):
                    fn_gen.add_line('Env.update_with_dotenv(dotenv_values=_dotenv_values)')
            else:
                fn = fn_gen.if_
            with fn('env_file'):
                fn_gen.add_line('Env.update_with_dotenv(env_file)')

            # iterate over the dataclass fields and (attempt to) resolve
            # each one.
            fn_gen.add_line('missing_vars = []')

            for name, f in cls_fields.items():
                type_field = f'_tp_{name}'
                tp = _globals[type_field] = f.type

                init_params.append(f'{name}:{type_field}=MISSING')

                # retrieve value (if it exists) for the environment variable

                env_var = field_to_var.get(name)
                if env_var:
                    part = f'({name} := lookup_exact({env_var!r}))'
                else:
                    part = f'({name} := get_env({name!r}))'

                with fn_gen.if_(f'{name} is not MISSING or {part} is not MISSING'):
                    parser_name = f'_parser_{name}'
                    _globals[parser_name] = cls_loader.get_parser_for_annotation(
                        tp, cls, extras)
                    with fn_gen.try_():
                        fn_gen.add_line(f'self.{name} = {parser_name}({name})')
                    with fn_gen.except_(ParseError, 'e'):
                        fn_gen.add_line(f'handle_err(e, cls, {name!r}, {env_var!r})')
                # this `else` block means that a value was not received for the
                # field, either via keyword arguments or Environment.
                with fn_gen.else_():
                    # check if the field defines a `default` or `default_factory`
                    # value; note this is similar to how `dataclasses` does it.
                    default_name = f'_dflt_{name}'
                    if f.default is not MISSING:
                        _globals[default_name] = f.default
                        fn_gen.add_line(f'self.{name} = {default_name}')
                    elif f.default_factory is not MISSING:
                        _globals[default_name] = f.default_factory
                        fn_gen.add_line(f'self.{name} = {default_name}()')
                    else:
                        fn_gen.add_line(f'add(missing_vars, {name!r}, {type_field})')

            # check for any required fields with missing values
            with fn_gen.if_('missing_vars'):
                fn_gen.add_line('raise MissingVars(cls, missing_vars) from None')

            # if keyword arguments are passed in, confirm that all there
            # aren't any "extra" keyword arguments
            # if _extra is not Extra.IGNORE:
                # with fn_gen.if_('has_kwargs'):
                #     # get a list of keyword arguments that don't map to any fields
                #     fn_gen.add_line('extra_kwargs = set(init_kwargs) - field_names')
                #     with fn_gen.if_('extra_kwargs'):
                #         # the default behavior is "DENY", so an error will be raised here.
                #         if _extra is None or _extra is Extra.DENY:
                #             _globals['ExtraData'] = ExtraData
                #             fn_gen.add_line('raise ExtraData(cls, extra_kwargs, list(fields_ordered)) from None')
                #         else:  # Extra.ALLOW
                #             # else, if we want to "ALLOW" extra keyword arguments, we need to
                #             # store those attributes in the instance.
                #             with fn_gen.for_('attr in extra_kwargs'):
                #                 fn_gen.add_line('setattr(self, attr, init_kwargs[attr])')

        functions = fn_gen.create_functions(globals=_globals, locals=_locals)

        return functions['__init__']


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
