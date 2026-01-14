import json

from ..decorators import cached_property
from ..type_def import T, Encoder, FileEncoder


class Container(list[T]):
    """Convenience wrapper around a collection of dataclass instances.

    For all intents and purposes, this should behave exactly as a `list`
    object.

    Usage:

        >>> from dataclass_wizard.utils.containers import Container
        >>> from dataclass_wizard import fromlist
        >>> from dataclasses import make_dataclass
        >>>
        >>> A = make_dataclass('A', [('f1', str), ('f2', int)])
        >>> list_of_a = fromlist(A, [{'f1': 'hello', 'f2': 1}, {'f1': 'world', 'f2': 2}])
        >>> c = Container[A](list_of_a)
        >>> print(c.prettify())

    """

    __slots__ = ('__dict__',
                 '__orig_class__')

    @cached_property
    def __model__(self) -> type[T]:
        """
        Given a declaration like Container[T], this returns the subscripted
        value of the generic type T.
        """
        ...

    def __init_subclass__(cls,
                          str=False):
        ...

    def prettify(self, encoder: Encoder = json.dumps,
                 indent=2,
                 ensure_ascii=False,
                 **encoder_kwargs) -> str:
        """
        Convert the list of instances to a *prettified* JSON string.
        """
        ...

    def to_json(self, encoder: Encoder = json.dumps,
                **encoder_kwargs) -> str:
        """
        Convert the list of instances to a JSON string.
        """
        ...

    def to_json_file(self, file: str, mode: str = 'w',
                     encoder: FileEncoder = json.dump,
                     **encoder_kwargs) -> None:
        """
        Serializes the list of instances and writes it to a JSON file.
        """
        ...
