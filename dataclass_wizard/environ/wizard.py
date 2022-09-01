import json
from typing import Callable, ClassVar, Union, Dict, AnyStr

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
from ..models import Extras
from ..type_def import JSONObject, Encoder
from ..utils.type_helper import type_name
from ..utils.typing_compat import is_classvar, eval_forward_ref_if_needed


class EnvWizard(AbstractEnvWizard):
    __slots__ = ()

    __initialized: ClassVar[bool] = True

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
    def __fields__(cls: E) -> Dict[str, type]:
        cls_fields = {}

        for field, ann in cls.__annotations__.items():
            ann = eval_forward_ref_if_needed(ann, cls)

            # skip any variables annotated as `ClassVar`
            if not is_classvar(ann):
                cls_fields[field] = ann

        return cls_fields

    @classmethod
    @_alias(asdict)
    def to_dict(cls: E) -> JSONObject:
        """
        Converts the `EnvWizard` subclass to a Python dictionary object that
        is JSON serializable.
        """
        # alias: asdict(self)
        ...

    @classmethod
    def to_json(cls: E, *,
                encoder: Encoder = json.dumps,
                **encoder_kwargs) -> AnyStr:
        """
        Converts the `EnvWizard` subclass to a JSON `string` representation.
        """
        return encoder(asdict(cls), **encoder_kwargs)

    def __init__(self, *, reload_env=False):
        if self.__initialized:
            cls_name = self.__class__.__qualname__

            msg = f'class `{cls_name}` is already initialized. Disable `init`, as ' \
                  f'shown below, to use the `__init__()` method.\n\n' \
                  f'class {cls_name}(EnvWizard, init=False):\n' \
                  f'    ...'

            raise ValueError(msg)

        self.__init_subclass__(reload_env=reload_env)

    def __init_subclass__(cls: E, *, init=True, reload_env=False):
        super().__init_subclass__()

        if reload_env:  # reload cached var names from `os.environ` as needed.
            Env.reload()

        if not init:  # skip logic in `__init_subclass__()` if needed.
            cls.__initialized = False
            return

        # Calls the Meta initializer when inner :class:`Meta` is sub-classed.
        call_meta_initializer_if_needed(cls)

        meta = get_meta(cls, base_cls=AbstractEnvMeta)
        cls_loader = get_loader(cls, base_cls=EnvLoader)

        # A cached mapping of each key in a JSON or dictionary object to the
        # resolved dataclass field name; useful so we don't need to do a case
        # transformation (via regex) each time.
        field_to_var = field_to_env_var(cls)

        # The function to case-transform and lookup variables defined in the
        # environment.
        get_env: Callable[[str], Union[str, None]] = meta.key_lookup_with_load

        # Get type annotations for attributes in the class.
        cls_dict = cls.__dict__

        # noinspection PyArgumentList
        extras = Extras()
        missing_vars = []

        for field, ann in cls.__fields__.items():

            # retrieve value (if it exists) for the environment variable
            if field in field_to_var:
                env_var = field_to_var[field]
                value = lookup_exact(env_var)
            else:
                value = get_env(field)

            if value is not None:
                # noinspection PyTypeChecker
                parser = cls_loader.get_parser_for_annotation(ann, cls, extras)

                try:
                    parsed_val = parser(value)
                except ParseError as e:
                    # We run into a parsing error while loading the field
                    # value; Add additional info on the Exception object
                    # before re-raising it.
                    e.class_name = cls
                    e.field_name = field
                    var_name = Env.cleaned_to_env.get(clean(field)) \
                               or field_to_var.get(field, field)
                    e.kwargs['env_variable'] = var_name
                    raise
                else:
                    setattr(cls, field, parsed_val)

            elif field not in cls_dict:
                tn = type_name(ann)
                # noinspection PyBroadException
                try:
                    suggested = ann()
                except Exception:
                    suggested = None

                missing_vars.append((field, tn, suggested))

        if missing_vars:
            raise MissingVars(cls, missing_vars) from None
