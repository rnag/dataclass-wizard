__all__ = [
    'does_not_raise',
    'data_file_path',
    'PY310_OR_ABOVE',
    'PY311_OR_ABOVE',
    'TypedDict',
    # For compatibility with Python 3.9 and 3.10
    'Required',
    'NotRequired'
]

import sys
# Ref: https://docs.pytest.org/en/6.2.x/example/parametrize.html#parametrizing-conditional-raising
from contextlib import nullcontext as does_not_raise
from pathlib import Path


# Directory for test files
TEST_DATA_DIR = Path(__file__).resolve().parent / 'testdata'

# Check if we are running Python 3.10+
PY310_OR_ABOVE = sys.version_info[:2] >= (3, 10)

# Check if we are running Python 3.11+
PY311_OR_ABOVE = sys.version_info[:2] >= (3, 11)

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
else:
    from typing_extensions import Required
    from typing_extensions import NotRequired


def data_file_path(name: str) -> str:
    """Returns the full path to a test file."""
    return str((TEST_DATA_DIR / name).absolute())
