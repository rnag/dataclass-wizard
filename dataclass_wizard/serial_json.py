import json
import logging

from .abstractions import AbstractJSONWizard
from .bases_meta import BaseJSONWizardMeta, LoadMeta
from .class_helper import call_meta_initializer_if_needed
from .dumpers import asdict
from .loaders import fromdict, fromlist
# noinspection PyProtectedMember
from .utils.dataclass_compat import _create_fn, _set_new_attribute


class JSONSerializable(AbstractJSONWizard):

    __slots__ = ()

    class Meta(BaseJSONWizardMeta):

        __slots__ = ()

        __is_inner_meta__ = True

        def __init_subclass__(cls):
            return cls._init_subclass()

    @classmethod
    def from_json(cls, string, *,
                  decoder = json.loads,
                  **decoder_kwargs):

        o = decoder(string, **decoder_kwargs)

        return fromdict(cls, o) if isinstance(o, dict) else fromlist(cls, o)

    from_list = classmethod(fromlist)

    from_dict = classmethod(fromdict)

    to_dict = asdict

    def to_json(self, *,
                encoder = json.dumps,
                **encoder_kwargs):

        return encoder(asdict(self), **encoder_kwargs)

    @classmethod
    def list_to_json(cls,
                     instances,
                     encoder = json.dumps,
                     **encoder_kwargs):

        list_of_dict = [asdict(o, cls=cls) for o in instances]

        return encoder(list_of_dict, **encoder_kwargs)

    # noinspection PyShadowingBuiltins
    def __init_subclass__(cls, str=True, debug=False):

        super().__init_subclass__()
        # Calls the Meta initializer when inner :class:`Meta` is sub-classed.
        call_meta_initializer_if_needed(cls)
        # Add a `__str__` method to the subclass, if needed
        if str:
            _set_new_attribute(cls, '__str__', _str_fn())
        if debug:
            default_lvl = logging.DEBUG
            logging.basicConfig(level=default_lvl)
            # minimum logging level for logs by this library
            min_level = default_lvl if isinstance(debug, bool) else debug
            # set `debug_enabled` flag for the class's Meta
            LoadMeta(debug_enabled=min_level).bind_to(cls)


def _str_fn():

    return _create_fn('__str__',
                      ('self', ),
                      ['return self.to_json(indent=2)'])
