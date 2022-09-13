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
from ..environ.loaders import EnvLoader
from ..errors import MissingVars, ParseError
from ..loaders import get_loader
from ..models import Extras, JSONField
from ..type_def import JSONObject, Encoder
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
            cls_fields[field.name] = field

            if isinstance(field, JSONField):
                keys = field.json.keys
                if keys:
                    # minor optimization: tuple of `str` to `str`
                    field_to_var[field] = keys[0] if len(keys) == 1 else keys

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

    def __init_subclass__(cls: 'type[E]', *, init=True, reload_env=False):

        if reload_env:  # reload cached var names from `os.environ` as needed.
            Env.reload()

        # apply the `@dataclass` decorator to `cls`
        _to_dataclass(cls)

        # Calls the Meta initializer when inner :class:`Meta` is sub-classed.
        call_meta_initializer_if_needed(cls)

    def __init__(self, *, _reload_env=False, **init_kwargs):
        """
        TODO: need to maybe generate an __init__() here, as
        `dataclasses` does.
        """
        cls = self.__class__

        if _reload_env:  # reload cached var names from `os.environ` as needed.
            Env.reload()

        meta = get_meta(cls, base_cls=AbstractEnvMeta)
        cls_loader = get_loader(cls, base_cls=EnvLoader)

        # A cached mapping of each key in a JSON or dictionary object to the
        # resolved dataclass field name; useful so we don't need to do a case
        # transformation (via regex) each time.
        field_to_var = field_to_env_var(cls)

        # The function to case-transform and lookup variables defined in the
        # environment.
        get_env: 'Callable[[str], str | None]' = meta.key_lookup_with_load

        # noinspection PyArgumentList
        extras = Extras()
        missing_vars = []

        cls_fields: 'dict[str, Field]' = cls.__fields__

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

            if value is not None:
                # noinspection PyTypeChecker
                parser = cls_loader.get_parser_for_annotation(tp, cls, extras)

                try:
                    parsed_val = parser(value)
                except ParseError as e:
                    # We run into a parsing error while loading the field
                    # value; Add additional info on the Exception object
                    # before re-raising it.
                    e.class_name = cls
                    e.field_name = name
                    var_name = Env.cleaned_to_env.get(clean(name)) \
                               or field_to_var.get(name, name)
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

        if missing_vars:
            raise MissingVars(cls, missing_vars) from None
