from enum import Enum

from ..utils.string_conv import to_camel_case, to_pascal_case, to_lisp_case, to_snake_case
from ..utils.wrappers import FuncWrapper


class KeyAction(Enum):
    """
    Defines the action to take when an unknown key is encountered during deserialization.
    """
    IGNORE = 0  # Silently skip unknown keys.
    RAISE = 1   # Raise an exception for the first unknown key.
    WARN = 2    # Log a warning for each unknown key.
    # INCLUDE = 3


class KeyCase(Enum):
    """
    By default, performs no conversion on strings.
        ex: `MY_FIELD_NAME` -> `MY_FIELD_NAME`

    """
    # Converts strings (generally in snake case) to camel case.
    #   ex: `my_field_name` -> `myFieldName`
    CAMEL = C = FuncWrapper(to_camel_case)

    # Converts strings to "upper" camel case.
    #   ex: `my_field_name` -> `MyFieldName`
    PASCAL = P = FuncWrapper(to_pascal_case)
    # Converts strings (generally in camel or snake case) to lisp case.
    #   ex: `myFieldName` -> `my-field-name`
    KEBAB = K = FuncWrapper(to_lisp_case)
    # Converts strings (generally in camel case) to snake case.
    #   ex: `myFieldName` -> `my_field_name`
    SNAKE = S = FuncWrapper(to_snake_case)
    # Auto-maps JSON keys to dataclass fields.
    #
    # All valid key casing transforms are attempted at runtime,
    # and the result is cached for subsequent lookups.
    #   ex: `My-Field-Name` -> `my_field_name`
    AUTO = A = None

    def __call__(self, *args):
        return self.value.f(*args)
