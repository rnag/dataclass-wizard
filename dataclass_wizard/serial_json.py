import json
# noinspection PyProtectedMember
from dataclasses import _create_fn, _set_new_attribute
from typing import Type, Dict, Any, List, Union

from .abstractions import AbstractJSONWizard, W
from .bases_meta import BaseJSONWizardMeta
from .class_helper import call_meta_initializer_if_needed
from .dumpers import asdict
from .loaders import fromdict


class JSONSerializable(AbstractJSONWizard):
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

        def __init_subclass__(cls):
            # Set the `__init_subclass__` method here, so we can ensure it
            # doesn't run for the `JSONSerializable.Meta` class.
            return cls._init_subclass()

    @classmethod
    def from_json(cls: Type[W], string: str) -> Union[W, List[W]]:
        """
        Converts a JSON `string` to an instance of the dataclass, or a list of
        the dataclass instances.
        """
        o = json.loads(string)

        return cls.from_dict(o) if isinstance(o, dict) else cls.from_list(o)

    @classmethod
    def from_list(cls: Type[W], o: List[Dict[str, Any]]) -> List[W]:
        """
        Converts a Python `list` object to a list of the dataclass instances.
        """
        return [fromdict(cls, d) for d in o]

    @classmethod
    def from_dict(cls: Type[W], o: Dict[str, Any]) -> W:
        """
        Converts a Python `dict` object to an instance of the dataclass.
        """
        return fromdict(cls, o)

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the dataclass instance to a Python dictionary object that is
        JSON serializable.
        """
        return asdict(self)

    def to_json(self, indent=None) -> str:
        """
        Converts the dataclass instance to a JSON `string` representation.
        """
        return json.dumps(self.to_dict(), indent=indent)

    def __init_subclass__(cls, str=True):
        """
        Checks for optional settings and flags that may be passed in by the
        sub-class, and calls the Meta initializer when :class:`Meta` is sub-classed.

        :param str: True to add a default `__str__` method to the subclass.
        """
        super().__init_subclass__()
        # Calls the Meta initializer when inner :class:`Meta` is sub-classed.
        call_meta_initializer_if_needed(cls)
        # Add a `__str__` method to the subclass, if needed
        if str:
            _set_new_attribute(cls, '__str__', _str_fn())


def _str_fn():
    """
    Converts the dataclass instance to a *prettified* JSON string
    representation, when the `str()` method is invoked.
    """
    return _create_fn('__str__',
                      ('self',),
                      ['return self.to_json(indent=2)'])
