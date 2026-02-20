from typing import Any

class Condition:

    op: str         # Operator
    val: Any        # Value
    t_or_f: bool    # Truthy or falsy
    _wrapped: bool  # True if wrapped in `SkipIf()`

    def __init__(self, operator: str, value: Any):
        ...

    def __str__(self):
        ...

    def evaluate(self, other) -> bool:
        ...


# Aliases for conditions
# noinspection PyPep8Naming
def EQ(value: Any) -> Condition:
    """Create a condition for equality (==)."""


# noinspection PyPep8Naming
def NE(value: Any) -> Condition:
    """Create a condition for inequality (!=)."""


# noinspection PyPep8Naming
def LT(value: Any) -> Condition:
    """Create a condition for less than (<)."""


# noinspection PyPep8Naming
def LE(value: Any) -> Condition:
    """Create a condition for less than or equal to (<=)."""


# noinspection PyPep8Naming
def GT(value: Any) -> Condition:
    """Create a condition for greater than (>)."""


# noinspection PyPep8Naming
def GE(value: Any) -> Condition:
    """Create a condition for greater than or equal to (>=)."""


# noinspection PyPep8Naming
def IS(value: Any) -> Condition:
    """Create a condition for identity (is)."""


# noinspection PyPep8Naming
def IS_NOT(value: Any) -> Condition:
    """Create a condition for non-identity (is not)."""


# noinspection PyPep8Naming
def IS_TRUTHY() -> Condition:
    """Create a "truthy" condition for evaluation (if <var>)."""


# noinspection PyPep8Naming
def IS_FALSY() -> Condition:
    """Create a "falsy" condition for evaluation (if not <var>)."""


# noinspection PyPep8Naming
def SkipIf(condition: Condition) -> Condition:
    ...


SkipIfNone: Condition
