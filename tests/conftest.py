__all__ = [
    'does_not_raise',
    'data_file_path',
    'PY36',
    'PY39_OR_ABOVE',
    'PY310_OR_ABOVE',
    # For compatibility with Python 3.6 and 3.7
    'Literal',
    'TypedDict',
    'Annotated',
    'Deque'
]

import sys
from pathlib import Path


# Directory for test files
TEST_DATA_DIR = Path(__file__).resolve().parent / 'testdata'

# Check if we are running Python 3.6
PY36 = sys.version_info[:2] == (3, 6)

# Check if we are running Python 3.9+
PY39_OR_ABOVE = sys.version_info[:2] >= (3, 9)

# Check if we are running Python 3.10+
PY310_OR_ABOVE = sys.version_info[:2] >= (3, 10)

# Ref: https://docs.pytest.org/en/6.2.x/example/parametrize.html#parametrizing-conditional-raising
if sys.version_info[:2] >= (3, 7):
    from contextlib import nullcontext as does_not_raise
else:
    from contextlib import ExitStack as does_not_raise

# TODO typing.Deque is deprecated since PY 3.9
#   https://docs.python.org/3/library/typing.html#typing.Deque
try:
    # Introduced in Python 3.6
    from typing import Deque
    # Introduced in Python 3.8
    from typing import Literal
    from typing import TypedDict
except ImportError:
    # Introduced in Python 3.6
    from typing_extensions import Deque
    # Introduced in Python 3.8
    from typing_extensions import Literal
    from typing_extensions import TypedDict

# typing.Annotated: Introduced in Python 3.9
if PY39_OR_ABOVE:
    from typing import Annotated
else:
    from typing_extensions import Annotated


def data_file_path(name: str) -> str:
    """Returns the full path to a test file."""
    return str((TEST_DATA_DIR / name).absolute())
