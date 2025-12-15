from enum import Enum

from ..utils.string_conv import (to_camel_case,
                                 to_lisp_case,
                                 to_pascal_case,
                                 to_snake_case)
from ..utils.wrappers import FuncWrapper


class KeyAction(Enum):
    """
    Specifies how to handle unknown keys encountered during deserialization.

    Actions:
    - `IGNORE`: Skip unknown keys silently.
    - `RAISE`: Raise an exception upon encountering the first unknown key.
    - `WARN`: Log a warning for each unknown key.

    For capturing unknown keys (e.g., including them in a dataclass), use the `CatchAll` field.
    More details: https://dcw.ritviknag.com/en/latest/common_use_cases/handling_unknown_json_keys.html#capturing-unknown-keys-with-catchall
    """
    IGNORE = 0  # Silently skip unknown keys.
    RAISE = 1   # Raise an exception for the first unknown key.
    WARN = 2    # Log a warning for each unknown key.
    # INCLUDE = 3


class KeyCase(Enum):
    """
    Defines transformations for string keys, commonly used for mapping JSON keys to dataclass fields.

    Key transformations:

    - `CAMEL`: Converts snake_case to camelCase.
      Example: `my_field_name` -> `myFieldName`
    - `PASCAL`: Converts snake_case to PascalCase (UpperCamelCase).
      Example: `my_field_name` -> `MyFieldName`
    - `KEBAB`: Converts camelCase or snake_case to kebab-case.
      Example: `myFieldName` -> `my-field-name`
    - `SNAKE`: Converts camelCase to snake_case.
      Example: `myFieldName` -> `my_field_name`
    - `AUTO`: Automatically maps JSON keys to dataclass fields by
        attempting all valid key casing transforms at runtime.
      Example: `My-Field-Name` -> `my_field_name` (cached for future lookups)

    By default, no transformation is applied:
        * Example: `MY_FIELD_NAME` -> `MY_FIELD_NAME`
    """
    # Key casing options
    CAMEL = C = FuncWrapper(to_camel_case)    # Convert to `camelCase`
    PASCAL = P = FuncWrapper(to_pascal_case)  # Convert to `PascalCase`
    KEBAB = K = FuncWrapper(to_lisp_case)     # Convert to `kebab-case`
    SNAKE = S = FuncWrapper(to_snake_case)    # Convert to `snake_case`
    AUTO = A = None  # Attempt all valid casing transforms at runtime.

    def __call__(self, *args):
        """Apply the key transformation."""
        return self.value.f(*args)


class DateTimeTo(Enum):
    ISO = 0          # ISO 8601 string (default)
    TIMESTAMP = 1    # Unix timestamp (seconds)
