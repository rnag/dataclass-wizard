__all__ = [
    'snake',
    'does_not_raise',
    'data_file_path',
]

import sys
# Ref: https://docs.pytest.org/en/6.2.x/example/parametrize.html#parametrizing-conditional-raising
from contextlib import nullcontext as does_not_raise
from pathlib import Path

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
