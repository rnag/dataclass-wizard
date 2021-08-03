"""
Re-usable Enum definitions

"""
from enum import Enum

from .utils.string_conv import *


class DateTimeTo(Enum):
    ISO_FORMAT = 0
    TIMESTAMP = 1


class LetterCase(Enum):
    # Converts strings (generally in snake case) to camel case.
    #   ex: `my_field_name` -> `myFieldName`
    CAMEL = to_camel_case
    # Converts strings to "upper" camel case.
    #   ex: `my_field_name` -> `MyFieldName`
    PASCAL = to_pascal_case
    # Converts strings (generally in camel case) to snake case.
    #   ex: `myFieldName` -> `my_field_name`
    SNAKE = to_snake_case
