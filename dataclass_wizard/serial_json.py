import json
import logging
from dataclasses import is_dataclass, dataclass

from .abstractions import AbstractJSONWizard
from .bases_meta import BaseJSONWizardMeta, LoadMeta, DumpMeta
from .constants import PACKAGE_NAME
from .class_helper import call_meta_initializer_if_needed
from .type_def import dataclass_transform
from .loader_selection import asdict, fromdict, fromlist
# noinspection PyProtectedMember
from .utils.dataclass_compat import _create_fn, _set_new_attribute
from .type_def import dataclass_transform


def _str_fn():
    return _create_fn('__str__',
                      ('self',),
                      ['return self.to_json(indent=2)'])


def _configure_wizard_class(cls,
                            str=True,
                            debug=False,
                            case=None,
                            dump_case=None,
                            load_case=None,
                            _key_transform=None,
                            _v1_default=False):
    load_meta_kwargs = {}

    if case is not None:
        _v1_default = True
        load_meta_kwargs['v1_case'] = case

    if dump_case is not None:
        _v1_default = True
        load_meta_kwargs['v1_dump_case'] = dump_case

    if load_case is not None:
        _v1_default = True
        load_meta_kwargs['v1_load_case'] = load_case

    if _v1_default:
        load_meta_kwargs['v1'] = True

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


@dataclass_transform()
class DataclassWizard(AbstractJSONWizard):

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
                          str=False,
                          debug=False,
                          case=None,
                          dump_case=None,
                          load_case=None,
                          _key_transform=None,
                          _v1_default=True,
                          _apply_dataclass=True,
                          **dc_kwargs):

        super().__init_subclass__()

        # Apply the @dataclass decorator.
        if (_apply_dataclass
                and not is_dataclass(cls)
                # skip classes provided by this library
                and not cls.__module__.startswith(f'{PACKAGE_NAME}.')):
            # noinspection PyArgumentList
            dataclass(cls, **dc_kwargs)

        _configure_wizard_class(cls, str, debug, case, dump_case, load_case,
                                _key_transform, _v1_default)


# noinspection PyAbstractClass
@dataclass_transform()
class JSONSerializable(DataclassWizard):

    __slots__ = ()

    # noinspection PyShadowingBuiltins
    def __init_subclass__(cls,
                          str=True,
                          debug=False,
                          case=None,
                          dump_case=None,
                          load_case=None,
                          _key_transform=None,
                          _v1_default=False,
                          _apply_dataclass=False,
                          **_):

        super().__init_subclass__(str, debug, case, dump_case, load_case,
                                  _key_transform, _v1_default, _apply_dataclass)


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
                          case=None,
                          dump_case=None,
                          load_case=None,
                          _key_transform=None,
                          _v1_default=False,
                          _apply_dataclass=False,
                          **_):
        """Bind child class to DumpMeta with no key transformation."""

        # Call JSONSerializable.__init_subclass__()
        # set `key_transform_with_dump` for the class's Meta
        super().__init_subclass__(False, debug, case, dump_case, load_case, 'NONE',
                                  _v1_default, _apply_dataclass)

        # Add a `__str__` method to the subclass, if needed
        if str:
            _set_new_attribute(cls, '__str__', _str_pprint_fn())
