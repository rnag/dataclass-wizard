from os import PathLike, fspath, sep, altsep, getcwd
from os.path import isabs
from pathlib import Path
from typing import TYPE_CHECKING

from ..lazy_imports import dotenv

if TYPE_CHECKING:
    from ._path_util import Environ, SecretsFileMapping


def get_secrets_map(cls, secret_dirs, *, reload=False):
    if secret_dirs is None:
        return {}

    # Treat empty containers as empty; but empty string is likely a bug.
    if isinstance(secret_dirs, (str, PathLike)):
        if str(secret_dirs) == '':
            raise ValueError('secrets_dir cannot be an empty string')
        dirs = fspath(secret_dirs),
    else:
        dirs = tuple(fspath(d) for d in secret_dirs)

    # optionally normalize paths (realpath)
    key = dirs

    cache = getattr(cls, '_dw_secrets_cache', None)
    if cache is None:
        cache = cls._dw_secrets_cache = {}

    if not reload and key in cache:
        return cache[key]

    m = cache[key] = read_secrets_dirs(dirs)
    return m


def get_dotenv_map(cls, env_file, *, reload=False):
    if not env_file:
        return {}

    if env_file is True:
        files = '.env',
    elif isinstance(env_file, (str, PathLike)):
        files = fspath(env_file),
    else:
        files = tuple(fspath(f) for f in env_file)

    cwd = getcwd()
    key = (cwd, *files)

    cache = getattr(cls, '_dw_dotenv_cache', None)
    if cache is None:
        cache = cls._dw_dotenv_cache = {}

    if not reload and key in cache:
        return cache[key]

    m = cache[key] = dotenv_values(files)
    return m


def read_secrets_dirs(secret_dirs):
    out: SecretsFileMapping = {}

    for d in secret_dirs:
        if not isinstance(d, (str, PathLike)):
            raise TypeError(f'secrets_dir entries must be str/PathLike, got {type(d)!r}')

        p = Path(d)

        # Missing mount is common in Docker; treat as empty.
        if not p.exists():
            continue

        if p.is_file():
            raise ValueError(f'Secrets directory {p!r} is a file, not a directory.')
        if not p.is_dir():
            # broken symlink, device node, etc. -> ignore or raise; ignore is ok
            continue

        try:
            for f in p.iterdir():
                f: Path
                if not f.is_file():
                    continue
                # Docker secret files are typically single-line with trailing NL
                out[f.name] = f.read_text(encoding='utf-8').rstrip('\n')

        except OSError as e:
            # Permission issues, transient IO errors; choose raise vs ignore
            raise OSError(f'Failed reading secrets_dir {p!r}: {e}') from e

    return out


def dotenv_values(files):
    """
    Retrieve the values (environment variables) from a dotenv file,
    or a list/tuple of dotenv files.
    """
    if files is True:
        files = ['.env']
    elif isinstance(files, (str, PathLike)):
        files = [files]

    env: Environ = {}

    for f in files:
        f = fspath(f)

        # iterate backwards (from current directory) to find the
        # dotenv file
        #
        # If user gave a path (absolute or contains a separator), don't search.
        if isabs(f) or (sep in f) or (altsep and altsep in f):
            dotenv_path = f
        else:
            dotenv_path = dotenv.find_dotenv(f, usecwd=True)

        if not dotenv_path:  # not found
            continue

        # take environment variables from `.env` file
        env.update(dotenv.dotenv_values(dotenv_path))

    return env
