__all__ = [
    'snake',
    'does_not_raise',
    'data_file_path',
    'PY310_OR_ABOVE',
    'PY311_OR_ABOVE',
    'PY312_OR_ABOVE',
    'TypedDict',
    # For compatibility with Python 3.9 and 3.10
    'Required',
    'NotRequired',
    'LiteralString',
]

import sys
# Ref: https://docs.pytest.org/en/6.2.x/example/parametrize.html#parametrizing-conditional-raising
from contextlib import nullcontext as does_not_raise
from pathlib import Path

from dataclass_wizard.utils.string_conv import to_snake_case


# Directory for test files
TEST_DATA_DIR = Path(__file__).resolve().parent / 'testdata'

# Check if we are running Python 3.10+
PY310_OR_ABOVE = sys.version_info[:2] >= (3, 10)

# Check if we are running Python 3.11+
PY311_OR_ABOVE = sys.version_info[:2] >= (3, 11)

# Check if we are running Python 3.12+
PY312_OR_ABOVE = sys.version_info[:2] >= (3, 12)

# Check if we are running Python 3.9 or 3.10
PY310_OR_EARLIER = not PY311_OR_ABOVE

# Weird, test cases for `TypedDict` fail in Python 3.9 & 3.10.15 (3.10:latest)
# So apparently, we need to use the one from `typing_extensions`.
if PY310_OR_EARLIER:
    from typing_extensions import TypedDict
else:
    from typing import TypedDict

# typing.Required and typing.NotRequired: Introduced in Python 3.11
if PY311_OR_ABOVE:
    from typing import Required
    from typing import NotRequired
    from typing import LiteralString
else:
    from typing_extensions import Required
    from typing_extensions import NotRequired
    from typing_extensions import LiteralString


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
