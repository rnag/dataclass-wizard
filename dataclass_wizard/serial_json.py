import json
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
    class Meta(BaseJSONWizardMeta):
        """
        Inner meta class that can be extended by sub-classes for additional
        customization with the JSON load / dump process.
        """
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

    def __str__(self):
        """
        Converts the dataclass instance to a *prettified* JSON string
        representation, when the `str()` method is invoked.
        """
        return self.to_json(indent=2)

    def __init_subclass__(cls):
        """
        Checks for optional settings and flags that may be passed in by the
        sub-class.
        """
        super().__init_subclass__()
        # Calls the Meta initializer when inner :class:`Meta` is sub-classed.
        call_meta_initializer_if_needed(cls)
