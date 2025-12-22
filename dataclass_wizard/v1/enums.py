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


class EnvKeyStrategy(Enum):
    """
    Defines how environment variable names are resolved for dataclass fields.

    This controls *which keys are tried, and in what order*, when loading values
    from environment variables, `.env` files, or Docker secrets.

    Strategies:

    - `ENV` (default):
        Uses conventional environment variable naming.
        Tries SCREAMING_SNAKE_CASE first, then snake_case.

        Example:
            Field: ``my_field_name``
            Keys tried: ``MY_FIELD_NAME``, ``my_field_name``

    - `FIELD_FIRST`:
        Tries the field name as written first, then environment-style variants.

        Example:
            Field: ``myFieldName``
            Keys tried: ``myFieldName``, ``MY_FIELD_NAME``, ``my_field_name``

        Useful when working with `.env` files or non-Python naming conventions.

    - `STRICT`:
        Uses explicit keys only. No automatic key derivation is performed
        (no prefixing, no casing transforms, no fallback lookups).
        Only ``__init__()`` kwargs and explicit aliases are considered.

        Useful when you want configuration loading to be fully deterministic.

    """
    ENV = "env"             # `MY_FIELD` > `my_field`
    FIELD_FIRST = "field"   # try field name as written, then env-style (ENV)
    STRICT = "strict"       # explicit keys only (kwargs + aliases), no prefixes / transforms
    # TODO: Implement later, as time allows!
    # PREFIXED_EXACT = "prefixed_exact"  # kwargs > prefixed exact field > alias > missing


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


class EnvPrecedence(Enum):
    SECRETS_ENV_DOTENV = 'secrets > env > dotenv'  # default
    SECRETS_DOTENV_ENV = 'secrets > dotenv > env'  # dev-heavy
    ENV_ONLY = 'env-only'  # strict/prod
