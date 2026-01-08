__all__ = ['normalize',
           'possible_json_keys',
           'possible_env_vars',
           'repl_or_with_union']

from typing import Iterable, Dict, List

from ._string_case import to_camel_case, to_lisp_case, to_snake_case
from ..enums import EnvKeyStrategy


def normalize(string: str) -> str:
    """
    Normalize a string - typically a dataclass field name - for comparison
    purposes.
    """
    return string.replace('-', '').replace('_', '').upper()


def possible_json_keys(field: str) -> list[str]:
    """
    Maps a dataclass field name to its possible keys in a JSON object.

    This function checks multiple naming conventions (e.g., camelCase,
    PascalCase, kebab-case, etc.) to find the matching key in the JSON
    object `o`. It also caches the mapping for future use.

    Args:
        field (str): The dataclass field name to map.

    Returns:
        list[str]: The possible JSON keys for the given field.
    """
    possible_keys = []

    # `camelCase`
    _key = to_camel_case(field)
    possible_keys.append(_key)

    # `PascalCase`: same as `camelCase` but first letter is capitalized
    _key = _key[0].upper() + _key[1:]
    possible_keys.append(_key)

    # `kebab-case`
    _key = to_lisp_case(field)
    possible_keys.append(_key)

    # `Upper-Kebab`: same as `kebab-case`, each word is title-cased
    _key = _key.title()
    possible_keys.append(_key)

    # `Upper_Snake`
    _key = _key.replace('-', '_')
    possible_keys.append(_key)

    # `snake_case`
    _key = _key.lower()
    possible_keys.append(_key)

    # remove 1:1 field mapping from possible keys,
    # as that's the first thing we check.
    if field in possible_keys:
        possible_keys.remove(field)

    return possible_keys


def possible_env_vars(field: str, lookup_strat: 'EnvKeyStrategy') -> list[str]:
    """
    Maps a dataclass field name to its possible var names in an env.

    This function checks multiple naming conventions (e.g., camelCase,
    PascalCase, kebab-case, etc.) to find the matching key in the JSON
    object `o`. It also caches the mapping for future use.

    Args:
        field (str): The dataclass field name to map.
        lookup_strat (EnvKeyStrategy): The environment key strategy to use.

    Returns:
        list[str]: The possible JSON keys for the given field.
    """
    _is_field_first = lookup_strat is EnvKeyStrategy.FIELD_FIRST
    possible_keys = [field] if _is_field_first else []

    # `snake_case`
    _snake = to_snake_case(field)

    # `Upper_Snake`
    _screaming_snake = _snake.upper()

    possible_keys.append(_screaming_snake)

    if not _is_field_first or field != _snake:
        possible_keys.append(_snake)

    return possible_keys


# Constants
OPEN_BRACKET = '['
CLOSE_BRACKET = ']'
COMMA = ','
OR = '|'

# Replace any OR (|) characters in a forward-declared annotation (i.e. string)
# with a `typing.Union` declaration. See below article for more info.
#
# https://stackoverflow.com/q/69606986/10237506


def repl_or_with_union(s: str):
    """
    Replace all occurrences of PEP 604- style annotations (i.e. like `X | Y`)
    with the Union type from the `typing` module, i.e. like `Union[X, Y]`.

    This is a recursive function that splits a complex annotation in order to
    traverse and parse it, i.e. one that is declared as follows:

      dict[str | Optional[int], list[list[str] | tuple[int | bool] | None]]
    """
    return _repl_or_with_union_inner(s.replace(' ', ''))


def _repl_or_with_union_inner(s: str):

    # If there is no '|' character in the annotation part, we just return it.
    if OR not in s:
        return s

    # Checking for brackets like `List[int | str]`.
    if OPEN_BRACKET in s:

        # Get any indices of COMMA or OR outside a braced expression.
        indices = _outer_comma_and_pipe_indices(s)

        outer_commas = indices[COMMA]
        outer_pipes = indices[OR]

        # We need to check if there are any commas *outside* a bracketed
        # expression. For example, the following cases are what we're looking
        # for here:
        #     value[test], dict[str | int, tuple[bool, str]]
        #     dict[str | int, str], value[test]
        # But we want to ignore cases like these, where all commas are nested
        # within a bracketed expression:
        #     dict[str | int, Union[int, str]]
        if outer_commas:
            return COMMA.join(
                [_repl_or_with_union_inner(i)
                 for i in _sub_strings(s, outer_commas)])

        # We need to check if there are any pipes *outside* a bracketed
        # expression. For example:
        #     value | dict[str | int, list[int | str]]
        #     dict[str, tuple[int | str]] | value
        # But we want to ignore cases like these, where all pipes are
        # nested within the a bracketed expression:
        #     dict[str | int, list[int | str]]
        if outer_pipes:
            or_parts = [_repl_or_with_union_inner(i)
                        for i in _sub_strings(s, outer_pipes)]

            return f'Union{OPEN_BRACKET}{COMMA.join(or_parts)}{CLOSE_BRACKET}'

        # At this point, we know that the annotation does not have an outer
        # COMMA or PIPE expression. We also know that the following syntax
        # is invalid: `SomeType[str][bool]`. Therefore, knowing this, we can
        # assume there is only one outer start and end brace. For example,
        # like `SomeType[str | int, list[dict[str, int | bool]]]`.

        first_start_bracket = s.index(OPEN_BRACKET)
        last_end_bracket = s.rindex(CLOSE_BRACKET)

        # Replace the value enclosed in the outermost brackets
        bracketed_val = _repl_or_with_union_inner(
            s[first_start_bracket + 1:last_end_bracket])

        start_val = s[:first_start_bracket]
        end_val = s[last_end_bracket + 1:]

        return f'{start_val}{OPEN_BRACKET}{bracketed_val}{CLOSE_BRACKET}{end_val}'

    elif COMMA in s:
        # We are dealing with a string like `int | str, float | None`
        return COMMA.join([_repl_or_with_union_inner(i)
                           for i in s.split(COMMA)])

    # We are dealing with a string like `int | str`
    return f'Union{OPEN_BRACKET}{s.replace(OR, COMMA)}{CLOSE_BRACKET}'


def _sub_strings(s: str, split_indices: Iterable[int]):
    """Split a string on the specified indices, and return the split parts."""
    prev = -1

    for idx in split_indices:
        yield s[prev+1:idx]
        prev = idx

    yield s[prev+1:]


def _outer_comma_and_pipe_indices(s: str) -> Dict[str, List[int]]:
    """Return any indices of ',' and '|' that are outside of braces."""
    indices = {OR: [], COMMA: []}
    brace_dict = {OPEN_BRACKET: 1, CLOSE_BRACKET: -1}
    brace_count = 0

    for i, char in enumerate(s):
        if char in brace_dict:
            brace_count += brace_dict[char]
        elif not brace_count and char in indices:
            indices[char].append(i)

    return indices
