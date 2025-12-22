from os import PathLike
from typing import Sequence

SecretsDir = str | PathLike[str]
SecretsDirs = SecretsDir | Sequence[SecretsDir] | None

Environ = dict[str, 'str | None']
SecretsFileMapping = dict[str, str]

EnvFilePath = str | PathLike[str]
EnvFilePaths = bool | EnvFilePath | Sequence[EnvFilePath] | None

def read_secrets_dirs(dirs: SecretsDirs) -> SecretsFileMapping: ...

def dotenv_values(files: EnvFilePaths) -> Environ: ...
