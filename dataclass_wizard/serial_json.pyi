import json
from typing import AnyStr, Collection, Callable, Protocol, dataclass_transform

from .abstractions import AbstractJSONWizard, W
from .bases_meta import BaseJSONWizardMeta
from .enums import LetterCase
from .v1.enums import KeyCase
from .type_def import Decoder, Encoder, JSONObject, ListOfJSONObject


# A handy alias in case it comes in useful to anyone :)
JSONWizard = JSONSerializable


class SerializerHookMixin(Protocol):
    @classmethod
    def _pre_from_dict(cls: type[W], o: JSONObject) -> JSONObject:
        """
        Optional hook that runs before the dataclass instance is
        loaded, and before it is converted from a dictionary object
        via :meth:`from_dict`.

        To override this, subclasses need to implement this method.
        A simple example is shown below:

        >>> from dataclasses import dataclass
        >>> from dataclass_wizard import JSONWizard
        >>> from dataclass_wizard.type_def import JSONObject
        >>>
        >>>
        >>> @dataclass
        >>> class MyClass(JSONWizard):
        >>>     a_bool: bool
        >>>
        >>>     @classmethod
        >>>     def _pre_from_dict(cls, o: JSONObject) -> JSONObject:
        >>>         # o = o.copy()  # Copying the `dict` object is optional
        >>>         o['a_bool'] = True  # Add a new key/value pair
        >>>         return o
        >>>
        >>> c = MyClass.from_dict({})
        >>> assert c == MyClass(a_bool=True)
        """
        ...

    def _pre_dict(self):
        # noinspection PyDunderSlots, PyUnresolvedReferences
        """
                Optional hook that runs before the dataclass instance is processed and
                before it is converted to a dictionary object via :meth:`to_dict`.

                To override this, subclasses need to extend from :class:`DumpMixIn`
                and implement this method. A simple example is shown below:

                >>> from dataclasses import dataclass
                >>> from dataclass_wizard import JSONWizard
                >>>
                >>>
                >>> @dataclass
                >>> class MyClass(JSONWizard):
                >>>     my_str: str
                >>>
                >>>     def _pre_dict(self):
                >>>         self.my_str = self.my_str.swapcase()
                >>>
                >>> assert MyClass('test').to_dict() == {'myStr': 'TEST'}
                """
        ...


class JSONPyWizard(JSONSerializable, SerializerHookMixin):
    """Helper for JSONWizard that ensures dumping to JSON keeps keys as-is."""

    def __init_subclass__(cls,
                          str: bool = True,
                          debug: bool | str | int = False,
                          key_case: KeyCase | str | None = None,
                          _key_transform: LetterCase | str | None = None):
        """Bind child class to DumpMeta with no key transformation."""


@dataclass_transform()
class JSONSerializable(AbstractJSONWizard, SerializerHookMixin):
    """
    Mixin class to allow a `dataclass` sub-class to be easily converted
    to and from JSON.

    """
    __slots__ = ()

    class Meta(BaseJSONWizardMeta):
        """
        Inner meta class that can be extended by sub-classes for additional
        customization with the JSON load / dump process.
        """
        __slots__ = ()

        # Class attribute to enable detection of the class type.
        __is_inner_meta__ = True

        def __init_subclass__(cls):
            # Set the `__init_subclass__` method here, so we can ensure it
            # doesn't run for the `JSONSerializable.Meta` class.
            ...
    @classmethod
    def from_json(cls: type[W], string: AnyStr, *,
                  decoder: Decoder = json.loads,
                  **decoder_kwargs) -> W | list[W]:
        """
        Converts a JSON `string` to an instance of the dataclass, or a list of
        the dataclass instances.
        """
        ...

    @classmethod
    def from_list(cls: type[W], o: ListOfJSONObject) -> list[W]:
        """
        Converts a Python `list` object to a list of the dataclass instances.
        """
        # alias: fromlist(cls, o)
        ...

    @classmethod
    def from_dict(cls: type[W], o: JSONObject) -> W:
        # alias: fromdict(cls, o)
        ...

    def to_dict(self: W,
                *,
                dict_factory=dict,
                exclude: Collection[str] | None = None,
                skip_defaults: bool | None = None,
                ) -> JSONObject:
        """
        Converts the dataclass instance to a Python dictionary object that is
        JSON serializable.

        Example usage:

          @dataclass
          class C(JSONWizard):
              x: int
              y: int
              z: bool = True

          c = C(1, 2, True)
          assert c.to_dict(skip_defaults=True) == {'x': 1, 'y': 2}

        If given, 'dict_factory' will be used instead of built-in dict.
        The function applies recursively to field values that are
        dataclass instances. This will also look into built-in containers:
        tuples, lists, and dicts.
        """
        # alias: asdict(self)
        ...

    def to_json(self: W, *,
                encoder: Encoder = json.dumps,
                **encoder_kwargs) -> AnyStr:
        """
        Converts the dataclass instance to a JSON `string` representation.
        """
        ...

    @classmethod
    def list_to_json(cls: type[W],
                     instances: list[W],
                     encoder: Encoder = json.dumps,
                     **encoder_kwargs) -> AnyStr:
        """
        Converts a ``list`` of dataclass instances to a JSON `string`
        representation.
        """
        ...

    # noinspection PyShadowingBuiltins
    def __init_subclass__(cls,
                          str: bool = True,
                          debug: bool | str | int = False,
                          key_case: KeyCase | str | None = None,
                          _key_transform: LetterCase | str | None = None):
        """
        Checks for optional settings and flags that may be passed in by the
        sub-class, and calls the Meta initializer when :class:`Meta` is sub-classed.

        :param str: True to add a default ``__str__`` method to the subclass.
        :param debug: True to enable debug mode and setup logging, so that
          this library's DEBUG (and above) log messages are visible. If
          ``debug`` is a string or integer, it is assumed to be the desired
          "minimum logging level", and will be passed to ``logging.setLevel``.

        """
        ...


def _str_fn() -> Callable[[W], str]:
    """
    Converts the dataclass instance to a *prettified* JSON string
    representation, when the `str()` method is invoked.
    """
    ...
