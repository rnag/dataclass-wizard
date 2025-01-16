import json
import logging

from .abstractions import AbstractJSONWizard
from .bases_meta import BaseJSONWizardMeta, LoadMeta, DumpMeta
from .class_helper import call_meta_initializer_if_needed
from .dumpers import asdict
from .loader_selection import fromdict, fromlist
from .type_def import dataclass_transform
# noinspection PyProtectedMember
from .utils.dataclass_compat import _create_fn, _set_new_attribute


@dataclass_transform()
class JSONSerializable(AbstractJSONWizard):

    __slots__ = ()

    class Meta(BaseJSONWizardMeta):

        __slots__ = ()

        __is_inner_meta__ = True

        def __init_subclass__(cls):
            return cls._init_subclass()

    @classmethod
    def from_json(cls, string, *,
                  decoder=json.loads,
                  **decoder_kwargs):

        o = decoder(string, **decoder_kwargs)

        return fromdict(cls, o) if isinstance(o, dict) else fromlist(cls, o)

    from_list = classmethod(fromlist)

    from_dict = classmethod(fromdict)

    to_dict = asdict

    def to_json(self, *,
                encoder=json.dumps,
                **encoder_kwargs):

        return encoder(asdict(self), **encoder_kwargs)

    @classmethod
    def list_to_json(cls,
                     instances,
                     encoder=json.dumps,
                     **encoder_kwargs):

        list_of_dict = [asdict(o, cls=cls) for o in instances]

        return encoder(list_of_dict, **encoder_kwargs)

    # noinspection PyShadowingBuiltins
    def __init_subclass__(cls,
                          str=True,
                          debug=False,
                          key_case=None,
                          _key_transform=None):

        super().__init_subclass__()

        load_meta_kwargs = {}

        # if not is_dataclass(cls) and not cls.__module__.startswith('dataclass_wizard.'):
        #     # Apply the `@dataclass` decorator to the class
        #     # noinspection PyMethodFirstArgAssignment
        #     cls = dataclass(cls)

        if key_case is not None:
            load_meta_kwargs['v1'] = True
            load_meta_kwargs['v1_key_case'] = key_case

        if _key_transform is not None:
            DumpMeta(key_transform=_key_transform).bind_to(cls)

        if debug:
            default_lvl = logging.DEBUG
            logging.basicConfig(level=default_lvl)
            # minimum logging level for logs by this library
            min_level = default_lvl if isinstance(debug, bool) else debug
            # set `v1_debug` flag for the class's Meta
            load_meta_kwargs['v1_debug'] = min_level

        # Calls the Meta initializer when inner :class:`Meta` is sub-classed.
        call_meta_initializer_if_needed(cls)

        if load_meta_kwargs:
            LoadMeta(**load_meta_kwargs).bind_to(cls)

        # Add a `__str__` method to the subclass, if needed
        if str:
            _set_new_attribute(cls, '__str__', _str_fn())

        return cls


def _str_fn():
    return _create_fn('__str__',
                      ('self',),
                      ['return self.to_json(indent=2)'])


def _str_pprint_fn():
    from pprint import pformat

    def __str__(self):
        return pformat(self, width=70)

    return __str__


# A handy alias in case it comes in useful to anyone :)
JSONWizard = JSONSerializable


class JSONPyWizard(JSONWizard):
    """Helper for JSONWizard that ensures dumping to JSON keeps keys as-is."""

    # noinspection PyShadowingBuiltins
    def __init_subclass__(cls,
                          str=True,
                          debug=False,
                          key_case=None,
                          _key_transform=None):
        """Bind child class to DumpMeta with no key transformation."""

        # Call JSONSerializable.__init_subclass__()
        # set `key_transform_with_dump` for the class's Meta
        new_cls = super().__init_subclass__(False, debug, key_case, 'NONE')

        # Add a `__str__` method to the subclass, if needed
        if str:
            _set_new_attribute(new_cls, '__str__', _str_pprint_fn())

        return new_cls
