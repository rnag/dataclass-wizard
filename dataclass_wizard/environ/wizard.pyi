import json
from dataclasses import Field
from typing import AnyStr, dataclass_transform, Collection

from ..abstractions import AbstractEnvWizard, E
from ..bases_meta import BaseEnvWizardMeta
from ..errors import ParseError
from ..type_def import JSONObject, Encoder, EnvFileType


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

    __fields__: dict[str, Field]

    def to_dict(self: E,
                *,
                dict_factory=dict,
                exclude: Collection[str] | None = None,
                skip_defaults: bool | None = None,
                ) -> JSONObject:
        """
        Converts the `EnvWizard` subclass to a Python dictionary object that is
        JSON serializable.

        Example usage:

          class C(EnvWizard):
              x: int
              y: int
              z: bool = True

          c = C(x=1, y=2, z=True)
          assert c.to_dict(skip_defaults=True) == {'x': 1, 'y': 2}

        If given, 'dict_factory' will be used instead of built-in dict.
        The function applies recursively to field values that are
        dataclass instances. This will also look into built-in containers:
        tuples, lists, and dicts.
        """
        # alias: asdict(self)
        ...

    def to_json(self: E, *,
                encoder: Encoder = json.dumps,
                **encoder_kwargs) -> AnyStr:
        """
        Converts the `EnvWizard` subclass to a JSON `string` representation.
        """
        ...

    # stub for type hinting purposes.
    def __init__(self, *,
                 env_file: EnvFileType = None,
                 reload_env: bool = False,
                 **init_kwargs) -> None:
        ...

    def __init_subclass__(cls, *, reload_env: bool = False, debug: bool = False):
        ...

    @classmethod
    def _create_methods(cls) -> None:
        """
        Generates methods such as the ``__init__()`` constructor method
        and ``dict()`` for the :class:`EnvWizard` subclass, vis-à-vis
        how the ``dataclasses`` module does it, with a few noticeable
        differences.
        """


def _add_missing_var(missing_vars: list, name: str, tp: type) -> None:
    ...


def _handle_parse_error(e: ParseError,
                        cls: type, name: str,
                        var_name: str | None):
    ...
