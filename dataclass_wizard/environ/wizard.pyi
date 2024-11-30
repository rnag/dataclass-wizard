import json
from dataclasses import Field
from typing import AnyStr, dataclass_transform, Collection, Sequence

from ..abstractions import AbstractEnvWizard, E
from ..bases_meta import BaseEnvWizardMeta
from ..enums import LetterCase
from ..errors import ParseError
from ..type_def import JSONObject, Encoder, EnvFileType


@dataclass_transform(kw_only_default=True)
class EnvWizard(AbstractEnvWizard):
    __slots__ = ()

    class Meta(BaseEnvWizardMeta):

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
                ) -> JSONObject: ...

    def to_json(self: E, *,
                encoder: Encoder = json.dumps,
                **encoder_kwargs) -> AnyStr: ...

    # stub for type hinting purposes.
    def __init__(self, *,
                 _env_file: EnvFileType = None,
                 _reload: bool = False,
                 _env_prefix:str=None,
                 _secrets_dir:EnvFileType | Sequence[EnvFileType]=None,
                 **init_kwargs) -> None: ...

    def __init_subclass__(cls, *, reload_env: bool = False,
                          debug: bool = False,
                          key_transform=LetterCase.NONE): ...

    @classmethod
    def _create_methods(cls) -> None: ...


def _add_missing_var(missing_vars: list,
                     name: str,
                     env_prefix: str | None,
                     var_name: str | None,
                     tp: type) -> None: ...


def _handle_parse_error(e: ParseError,
                        cls: type,
                        name: str,
                        env_prefix: str | None,
                        var_name: str | None): ...

def _get_var_name(name: str,
                  env_prefix: str | None,
                  var_name: str | None) -> str: ...
