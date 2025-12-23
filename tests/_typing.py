__all__ = [
    'PY310_OR_ABOVE',
    'PY311_OR_ABOVE',
    'PY312_OR_ABOVE',
    'TypedDict',
    # For compatibility with Python 3.9 and 3.10
    'Required',
    'NotRequired',
    'ReadOnly',
    'LiteralString',
]

import sys

from dataclass_wizard.constants import PY313_OR_ABOVE

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

if PY313_OR_ABOVE:
    from typing import ReadOnly
else:
    from typing_extensions import ReadOnly
