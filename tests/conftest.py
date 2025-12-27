__all__ = [
    'snake',
    'does_not_raise',
    'data_file_path',
]

import sys
# Ref: https://docs.pytest.org/en/6.2.x/example/parametrize.html#parametrizing-conditional-raising
from contextlib import nullcontext as does_not_raise
from logging import getLogger
from pathlib import Path

import pytest

from dataclass_wizard.constants import PACKAGE_NAME
from dataclass_wizard.utils.string_conv import to_snake_case

from ._typing import PY312_OR_ABOVE


# Directory for test files
TEST_DATA_DIR = Path(__file__).resolve().parent / 'testdata'


# Ignore test files if the Python version is below 3.12
if not PY312_OR_ABOVE:
    print("Python version is below 3.12. Ignoring test files.")
    collect_ignore = [
        Path('unit', 'v1', 'test_union_as_type_alias_recursive.py').as_posix(),
    ]


@pytest.fixture
def restore_logger():
    logger = getLogger(PACKAGE_NAME)

    old_level = logger.level
    old_propagate = logger.propagate
    old_handlers = list(logger.handlers)

    yield logger

    # remove any new handlers
    for h in list(logger.handlers):
        if h not in old_handlers:
            logger.removeHandler(h)
            try:
                h.close()
            except Exception:
                pass

    # restore original handlers (in case code removed/changed them)
    logger.handlers[:] = old_handlers
    logger.setLevel(old_level)
    logger.propagate = old_propagate


def data_file_path(name: str) -> str:
    """Returns the full path to a test file."""
    return str((TEST_DATA_DIR / name).absolute())


def snake(d):
    """
    Helper function to snake-case all keys in a dictionary `d`.

    Useful for `v1`, which by default requires a 1:1 mapping of
    JSON key to dataclass field.
    """
    return {to_snake_case(k): v for k, v in d.items()}
