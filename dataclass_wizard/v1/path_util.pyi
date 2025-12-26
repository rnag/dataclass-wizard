from os import PathLike
from typing import Sequence

from ._env import E


SecretsDir = str | PathLike[str]
SecretsDirs = SecretsDir | Sequence[SecretsDir] | None

Environ = dict[str, 'str | None']
SecretsFileMapping = dict[str, str]

EnvFilePath = str | PathLike[str]
EnvFilePaths = bool | EnvFilePath | Sequence[EnvFilePath] | None


def get_secrets_map(cls: E, secret_dirs: SecretsDirs, *, reload: bool = False) -> SecretsFileMapping: ...
def get_dotenv_map(cls: E, env_file: EnvFilePaths, *, reload: bool = False) -> Environ: ...

def read_secrets_dirs(dirs: SecretsDirs) -> SecretsFileMapping: ...
def dotenv_values(files: EnvFilePaths) -> Environ: ...
