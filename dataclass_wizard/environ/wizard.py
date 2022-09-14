import json
from dataclasses import MISSING, dataclass, fields, Field
from typing import AnyStr, Callable

from .dumpers import asdict
from .lookups import Env, lookup_exact, clean
from ..abstractions import AbstractEnvWizard, E
from ..bases import AbstractEnvMeta
from ..bases_meta import BaseEnvWizardMeta
from ..class_helper import (call_meta_initializer_if_needed, get_meta,
                            field_to_env_var)
from ..decorators import cached_class_property, _alias
from ..enums import Extra
from ..environ.loaders import EnvLoader
from ..errors import ExtraData, MissingVars, ParseError
from ..loaders import get_loader
from ..models import Extras, JSONField
from ..type_def import JSONObject, Encoder, EnvFileType
from ..utils.type_helper import type_name


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
    def __fields__(cls: E) -> 'dict[str, Field]':
        cls_fields = {}
        field_to_var = field_to_env_var(cls)

        for field in fields(cls):
            name = field.name
            cls_fields[name] = field

            if isinstance(field, JSONField):
                keys = field.json.keys
                if keys:
                    # minor optimization: convert a one-element tuple of `str` to `str`
                    field_to_var[name] = keys[0] if len(keys) == 1 else keys

        return cls_fields

    @_alias(asdict)
    def to_dict(self: E, exclude: 'list[str]' = None,
                skip_defaults: bool = False) -> JSONObject:
        """
        Converts the `EnvWizard` subclass to a Python dictionary object that
        is JSON serializable.
        """
        # alias: asdict(self)
        ...

    def to_json(self: E, *,
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
        Returns an ``__init__()`` constructor method for the
        :class:`EnvWizard` subclass.

        TODO: might be a good idea to dynamically generate an __init__() here,
          as `dataclasses` does.
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
        extras = Extras()

        cls_fields: 'dict[str, Field]' = cls.__fields__
        field_names = frozenset(cls_fields)

        _extra = meta.extra
        _meta_env_file = meta.env_file

        _dotenv_values = Env.dotenv_values(_meta_env_file) if _meta_env_file else None

        def __init__(self, *, _env_file=None, _reload_env=False, **init_kwargs):

            # reload cached var names from `os.environ` as needed.
            if _reload_env:
                Env.reload()

            # update environment with values in the "dot env" files as needed.
            if _env_file:
                Env.update_with_dotenv(_env_file)

            elif _meta_env_file and _env_file is not False:
                Env.update_with_dotenv(dotenv_values=_dotenv_values)

            # iterate over the dataclass fields and (attempt to) resolve
            # each one.
            missing_vars = []

            for name, field in cls_fields.items():
                tp = field.type

                # retrieve value (if it exists) for the environment variable
                if name in init_kwargs:
                    value = init_kwargs[name]
                elif name in field_to_var:
                    env_var = field_to_var[name]
                    value = lookup_exact(env_var)
                else:
                    value = get_env(name)

                if value is not MISSING:
                    parser = cls_loader.get_parser_for_annotation(tp, cls, extras)

                    try:
                        parsed_val = parser(value)
                    except ParseError as e:
                        # We run into a parsing error while loading the field
                        # value; Add additional info on the Exception object
                        # before re-raising it.
                        e.class_name = cls
                        e.field_name = name
                        var_name = (Env.cleaned_to_env.get(clean(name))
                                    or field_to_var.get(name, name))
                        e.kwargs['env_variable'] = var_name

                        raise
                    else:
                        setattr(self, name, parsed_val)

                elif field.default is not MISSING:
                    setattr(self, name, field.default)

                elif field.default_factory is not MISSING:
                    setattr(self, name, field.default_factory())

                else:
                    tn = type_name(tp)
                    # noinspection PyBroadException
                    try:
                        suggested = tp()
                    except Exception:
                        suggested = None

                    missing_vars.append((name, tn, suggested))

            # check for any required fields with missing values
            if missing_vars:
                raise MissingVars(cls, missing_vars) from None

            # if keyword arguments are passed in, confirm that all there
            # aren't any "extra" keyword arguments
            if init_kwargs:

                # get a list of keyword arguments that don't map to any fields
                extra_kwargs = set(init_kwargs) - field_names

                if extra_kwargs:

                    # the default behavior is "DENY", so an error will be raised here.
                    if _extra is None or _extra is Extra.DENY:
                        raise ExtraData(cls, extra_kwargs, list(cls_fields)) from None
                    # else, if we want to "ALLOW" extra keyword arguments, we need to
                    # store those attributes in the instance.
                    elif _extra is Extra.ALLOW:
                        for attr in extra_kwargs:
                            setattr(self, attr, init_kwargs[attr])
                    # else, we ignore any extra keyword arguments that are passed in.

        return __init__
