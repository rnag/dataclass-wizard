class Condition:

    __dcw_condition__ = True
    __slots__ = (
        'op',
        'val',
        't_or_f',
        '_wrapped',
    )

    def __init__(self, operator, value):
        self.op = operator
        self.val = value
        self.t_or_f = operator in {'+', '!'}

    def __str__(self):
        return f"{self.op} {self.val!r}"

    def evaluate(self, other) -> bool:  # pragma: no cover
        # Optionally support runtime evaluation of the condition
        operators = {
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
            "is": lambda a, b: a is b,
            "is not": lambda a, b: a is not b,
            "+": lambda a, _: True if a else False,
            "!": lambda a, _: not a,
        }
        return operators[self.op](other, self.val)


# Aliases for conditions

# noinspection PyPep8Naming
def EQ(value): return Condition("==", value)
# noinspection PyPep8Naming
def NE(value): return Condition("!=", value)
# noinspection PyPep8Naming
def LT(value): return Condition("<", value)
# noinspection PyPep8Naming
def LE(value): return Condition("<=", value)
# noinspection PyPep8Naming
def GT(value): return Condition(">", value)
# noinspection PyPep8Naming
def GE(value): return Condition(">=", value)
# noinspection PyPep8Naming
def IS(value): return Condition("is", value)
# noinspection PyPep8Naming
def IS_NOT(value): return Condition("is not", value)
# noinspection PyPep8Naming
def IS_TRUTHY(): return Condition("+", None)
# noinspection PyPep8Naming
def IS_FALSY(): return Condition("!", None)


# noinspection PyPep8Naming
def SkipIf(condition):
    """
    Mark a condition to be used as a skip directive during serialization.
    """
    condition._wrapped = True  # Set a marker attribute
    return condition


# Convenience alias, to skip serializing field if value is None
SkipIfNone = SkipIf(IS(None))
