import json
import logging
from dataclasses import dataclass, MISSING

from .abstractions import AbstractJSONWizard
from .bases_meta import BaseJSONWizardMeta, LoadMeta, DumpMeta, register_type
from .class_helper import call_meta_initializer_if_needed
from .constants import PACKAGE_NAME
from .loader_selection import asdict, fromdict, fromlist
from .log import enable_library_debug_logging
from .type_def import dataclass_transform
# noinspection PyProtectedMember
from .utils.dataclass_compat import (_create_fn,
                                     _dataclass_needs_refresh,
                                     _set_new_attribute)


def _str_fn():
    return _create_fn('__str__',
                      ('self',),
                      ['return self.to_json(indent=2)'])


def _first_declared_attr_in_mro(cls, name: str):
    """First `name` found in MRO (excluding cls); else None."""
    for base in cls.__mro__[1:]:
        attr = base.__dict__.get(name, MISSING)
        if attr is not MISSING:
            return attr
    return None


def _set_from_dict_and_to_dict_if_needed(cls):
    """
    Pin default dispatchers on subclasses.

    Codegen is lazy; if a base later gets a specialised
    `from_dict` / `to_dict`, subclasses would inherit it.
    Defining defaults in `cls.__dict__` blocks that.
    """
    if 'from_dict' not in cls.__dict__:
        inherited = _first_declared_attr_in_mro(cls, 'from_dict')
        if getattr(inherited, '__func__', None) is fromdict:
            cls.from_dict = classmethod(fromdict)

    if 'to_dict' not in cls.__dict__:
        inherited = _first_declared_attr_in_mro(cls, 'to_dict')
        if inherited is asdict:
            cls.to_dict = asdict


# noinspection PyShadowingBuiltins
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
        # minimum logging level for logs by this library
        lvl = logging.DEBUG if isinstance(debug, bool) else debug
        # enable library logging
        enable_library_debug_logging(lvl)
        # set `v1_debug` flag for the class's Meta
        load_meta_kwargs['v1_debug'] = lvl

    if load_meta_kwargs:
        LoadMeta(**load_meta_kwargs).bind_to(cls)

    # Calls the Meta initializer when inner :class:`Meta` is sub-classed.
    call_meta_initializer_if_needed(cls)

    # Add a `__str__` method to the subclass, if needed
    if str:
        _set_new_attribute(cls, '__str__', _str_fn())

    # Add `from_dict` and `to_dict` methods to the subclass, if needed
    _set_from_dict_and_to_dict_if_needed(cls)


@dataclass_transform()
class DataclassWizard(AbstractJSONWizard):

    __slots__ = ()

    class Meta(BaseJSONWizardMeta):

        __slots__ = ()

        __is_inner_meta__ = True

        def __init_subclass__(cls):
            return cls._init_subclass()

    register_type = classmethod(register_type)

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

        # skip classes provided by this library.
        if cls.__module__.startswith(f'{PACKAGE_NAME}.'):
            return

        # Apply the @dataclass decorator.
        if _apply_dataclass and _dataclass_needs_refresh(cls):
            # noinspection PyArgumentList
            dataclass(cls, **dc_kwargs)

        _configure_wizard_class(cls, str, debug, case, dump_case, load_case,
                                _key_transform, _v1_default)


# noinspection PyAbstractClass
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
