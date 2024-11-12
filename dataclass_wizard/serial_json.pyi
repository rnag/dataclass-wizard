import json
from typing import Type, List, Union, AnyStr

from .abstractions import AbstractJSONWizard, W
from .bases_meta import BaseJSONWizardMeta
from .type_def import Decoder, Encoder, JSONObject, ListOfJSONObject


# A handy alias in case it comes in useful to anyone :)
JSONWizard = JSONSerializable


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

        # Class attribute to enable detection of the class type.
        __is_inner_meta__ = True

        def __init_subclass__(cls):
            # Set the `__init_subclass__` method here, so we can ensure it
            # doesn't run for the `JSONSerializable.Meta` class.
            ...

    @classmethod
    def from_json(cls: Type[W], string: AnyStr, *,
                  decoder: Decoder = json.loads,
                  **decoder_kwargs) -> Union[W, List[W]]:
        """
        Converts a JSON `string` to an instance of the dataclass, or a list of
        the dataclass instances.
        """
        ...

    @classmethod
    def from_list(cls: Type[W], o: ListOfJSONObject) -> List[W]:
        """
        Converts a Python `list` object to a list of the dataclass instances.
        """
        # alias: fromlist(cls, o)
        ...

    @classmethod
    def from_dict(cls: Type[W], o: JSONObject) -> W:
        """
        Converts a Python `dict` object to an instance of the dataclass.
        """
        # alias: fromdict(cls, o)
        ...

    def to_dict(self: W) -> JSONObject:
        """
        Converts the dataclass instance to a Python dictionary object that is
        JSON serializable.
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
    def list_to_json(cls: Type[W],
                     instances: List[W],
                     encoder: Encoder = json.dumps,
                     **encoder_kwargs) -> AnyStr:
        """
        Converts a ``list`` of dataclass instances to a JSON `string`
        representation.
        """
        ...

    # noinspection PyShadowingBuiltins
    def __init_subclass__(cls, str=True):
        """
        Checks for optional settings and flags that may be passed in by the
        sub-class, and calls the Meta initializer when :class:`Meta` is sub-classed.

        :param str: True to add a default `__str__` method to the subclass.
        """
        ...
