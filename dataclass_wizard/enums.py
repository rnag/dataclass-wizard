"""
Re-usable Enum definitions

"""
from enum import Enum

from .environ import lookups
from .utils.string_conv import *
from .utils.wrappers import FuncWrapper


class DateTimeTo(Enum):
    ISO_FORMAT = 0
    TIMESTAMP = 1


class LetterCase(Enum):

    # Converts strings (generally in snake case) to camel case.
    #   ex: `my_field_name` -> `myFieldName`
    CAMEL = FuncWrapper(to_camel_case)
    # Converts strings to "upper" camel case.
    #   ex: `my_field_name` -> `MyFieldName`
    PASCAL = FuncWrapper(to_pascal_case)
    # Converts strings (generally in camel or snake case) to lisp case.
    #   ex: `myFieldName` -> `my-field-name`
    LISP = FuncWrapper(to_lisp_case)
    # Converts strings (generally in camel case) to snake case.
    #   ex: `myFieldName` -> `my_field_name`
    SNAKE = FuncWrapper(to_snake_case)
    # Performs no conversion on strings.
    #   ex: `MY_FIELD_NAME` -> `MY_FIELD_NAME`
    NONE = FuncWrapper(lambda s: s)

    def __call__(self, *args):
        return self.value.f(*args)


class LetterCasePriority(Enum):
    """
    Helper Enum which determines which letter casing we want to
    *prioritize* when loading environment variable names.

    The default
    """
    SCREAMING_SNAKE = FuncWrapper(lookups.with_screaming_snake_case)
    SNAKE = FuncWrapper(lookups.with_snake_case)
    CAMEL = FuncWrapper(lookups.with_pascal_or_camel_case)
    PASCAL = FuncWrapper(lookups.with_pascal_or_camel_case)

    def __call__(self, *args):
        return self.value.f(*args)
