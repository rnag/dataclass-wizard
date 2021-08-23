__all__ = ['to_camel_case',
           'to_pascal_case',
           'to_lisp_case',
           'to_snake_case']

import re


def to_camel_case(string: str) -> str:
    """
    Convert a string to Camel Case.

    Examples::

        >>> to_camel_case("device_type")
        'deviceType'

    """
    string = replace_multi_with_single(
        string.replace('-', '_').replace(' ', '_'))

    return string[0].lower() + re.sub(
        r"(?:_)(.)", lambda m: m.group(1).upper(), string[1:])


def to_pascal_case(string):
    """
    Converts a string to Pascal Case (also known as "Upper Camel Case")

    Examples::

        >>> to_pascal_case("device_type")
        'DeviceType'

    """
    string = replace_multi_with_single(
        string.replace('-', '_').replace(' ', '_'))

    return string[0].upper() + re.sub(
        r"(?:_)(.)", lambda m: m.group(1).upper(), string[1:])


def to_lisp_case(string: str) -> str:
    """
    Make a hyphenated, lowercase form from the expression in the string.

    Example::

        >>> to_lisp_case("DeviceType")
        'device-type'

    """
    string = string.replace('_', '-').replace(' ', '-')
    # Short path: the field is already lower-cased, so we don't need to handle
    # for camel or title case.
    if string.islower():
        return replace_multi_with_single(string, '-')

    result = re.sub(
        r'((?!^)(?<!-)[A-Z][a-z]+|(?<=[a-z0-9])[A-Z])', r'-\1', string)

    return replace_multi_with_single(result.lower(), '-')


def to_snake_case(string: str) -> str:
    """
    Make an underscored, lowercase form from the expression in the string.

    Example::

        >>> to_snake_case("DeviceType")
        'device_type'

    """
    string = string.replace('-', '_').replace(' ', '_')
    # Short path: the field is already lower-cased, so we don't need to handle
    # for camel or title case.
    if string.islower():
        return replace_multi_with_single(string)

    result = re.sub(
        r'((?!^)(?<!_)[A-Z][a-z]+|(?<=[a-z0-9])[A-Z])', r'_\1', string)

    return replace_multi_with_single(result.lower())


def replace_multi_with_single(string: str, char='_') -> str:
    """
    Replace multiple consecutive occurrences of `char` with a single one.
    """
    rep = char + char
    while rep in string:
        string = string.replace(rep, char)

    return string


# Note: this is the initial helper function I came up with. This doesn't use
# regex for the string transformation, so it's actually faster than the
# implementation above. However, I do prefer the implementation with regex,
# because its a lot cleaner and more simple than this implementation.
# def to_snake_case_old(string: str):
#     """
#     Make an underscored, lowercase form from the expression in the string.
#     """
#     if len(string) < 2:
#         return string or ''
#
#     string = string.replace('-', '_')
#
#     if string.islower():
#         return replace_multi_with_single(string)
#
#     start_idx = 0
#
#     parts = []
#     for i, c in enumerate(string):
#         c: str
#         if c.isupper():
#             try:
#                 next_lower = string[i + 1].islower()
#             except IndexError:
#                 if string[i - 1].islower():
#                     parts.append(string[start_idx:i])
#                     parts.append(c)
#                 else:
#                     parts.append(string[start_idx:])
#                 break
#             else:
#                 if i == 0:
#                     continue
#
#                 if string[i - 1].islower():
#                     parts.append(string[start_idx:i])
#                     start_idx = i
#
#                 elif next_lower:
#                     parts.append(string[start_idx:i])
#                     start_idx = i
#     else:
#         parts.append(string[start_idx:i + 1])
#
#     result = '_'.join(parts).lower()
#
#     return replace_multi_with_single(result)
