from dataclasses import MISSING
from typing import Any, Sequence, TypeAlias, Union

PathPart: TypeAlias = Union[str, int, float, bool]
PathType: TypeAlias = Sequence[PathPart]


def safe_get(data: dict | list,
             path: PathType,
             default=MISSING,
             raise_: bool = True) -> Any:
    """
    Retrieve a value from a nested structure safely.

    Traverses a nested structure (e.g., dictionaries or lists) following a sequence of keys or indices specified in `path`.
    Handles missing keys, out-of-bounds indices, or invalid types gracefully.

    Args:
        data (Any): The nested structure to traverse.
        path (Iterable): A sequence of keys or indices to follow.
        default (Any): The value to return if the path cannot be fully traversed.
                       If not provided and an error occurs, the exception is re-raised.
        raise_ (bool): True to raise an error on invalid path (default True).

    Returns:
        Any: The value at the specified path, or `default` if traversal fails.

    Raises:
        KeyError, IndexError, AttributeError, TypeError: If `default` is not provided
        and an error occurs during traversal.
    """
    ...


def v1_safe_get(data: dict | list,
                path: PathType,
                raise_: bool) -> Any:
    """
    Retrieve a value from a nested structure safely.

    Traverses a nested structure (e.g., dictionaries or lists) following a sequence of keys or indices specified in `path`.
    Handles missing keys, out-of-bounds indices, or invalid types gracefully.

    Args:
        data (Any): The nested structure to traverse.
        path (Iterable): A sequence of keys or indices to follow.
        raise_ (bool): True to raise an error on invalid path.

    Returns:
        Any: The value at the specified path, or `MISSING` if traversal fails.

    Raises:
        KeyError, IndexError, AttributeError, TypeError: If `default` is not provided
        and an error occurs during traversal.
    """
    ...


def _format_err(e: Exception,
                current_data: Any,
                path: PathType,
                current_path: PathPart):
    """Format and return a `ParseError`."""
    ...


def split_object_path(_input: str) -> PathType:
    """
    Parse a custom object path string into a list of components.

    This function interprets a custom object path syntax and breaks it into individual path components,
    including dictionary keys, list indices, attributes, and nested elements.
    It handles escaped characters and supports mixed types (e.g., strings, integers, floats, booleans).

    Args:
        _input (str): The object path string to parse.

    Returns:
        PathType: A list of components representing the parsed path. Components can be strings,
                  integers, floats, booleans, or other valid key/index types.

    Example:
        >>> split_object_path(r'''a[b][c]["d\\\"o\\\""][e].f[go]['1'].then."y\\e\\\"s"[1]["we can!"].five.2.3.[ok][4.56].[-7.89].'let\\'sd\\othisy\\'all!'.yeah.123.False['True'].thanks!''')
        ['a', 'b', 'c', 'd"o"', 'e', 'f', 'go', '1', 'then', 'y\\e"s', 1, 'we can!', 'five', 2, 3, 'ok', 4.56, -7.89,
         "let'sd\\othisy'all!", 'yeah', 123, False, 'True', 'thanks!']
    """
