__all__ = [
    "does_not_raise",
    "data_file_path",
    "PY39_OR_ABOVE",
    "PY310_OR_ABOVE",
    "Literal",
    "TypedDict",
    "Annotated",
    "Deque",
]

import sys
from pathlib import Path


# Directory for test files
TEST_DATA_DIR = Path(__file__).resolve().parent / "testdata"

# Check if we are running Python 3.9+
PY39_OR_ABOVE = sys.version_info[:2] >= (3, 9)

# Check if we are running Python 3.10+
PY310_OR_ABOVE = sys.version_info[:2] >= (3, 10)

from contextlib import nullcontext as does_not_raise

try:
    from typing import Literal
    from typing import TypedDict
    from typing import Annotated
    from typing import Deque
except ImportError:
    from typing_extensions import Literal
    from typing_extensions import TypedDict
    from typing_extensions import Annotated
    from typing_extensions import Deque


def data_file_path(name: str) -> str:
    """Returns the full path to a test file."""
    return str((TEST_DATA_DIR / name).absolute())
