import json
import logging
from dataclasses import dataclass, MISSING

from .abstractions import AbstractJSONWizard
from .bases_meta import BaseJSONWizardMeta, LoadMeta, register_type
from .class_helper import call_meta_initializer_if_needed, str_pprint_fn
from .constants import PACKAGE_NAME
from .dumpers import asdict
from .loaders import fromdict, fromlist
from ._log import enable_library_debug_logging
from .type_def import dataclass_transform
# noinspection PyProtectedMember
from .utils._dataclass_compat import (dataclass_needs_refresh,
                                      set_new_attribute)


def first_declared_attr_in_mro(cls, name):
    """First `name` found in MRO (excluding cls); else None."""
    for base in cls.__mro__[1:]:
        attr = base.__dict__.get(name, MISSING)
        if attr is not MISSING:
            return attr
    return None


def set_from_dict_and_to_dict_if_needed(cls):
    """
    Pin default dispatchers on subclasses.

    Codegen is lazy; if a base later gets a specialised
    `from_dict` / `to_dict`, subclasses would inherit it.
    Defining defaults in `cls.__dict__` blocks that.
    """
    if 'from_dict' not in cls.__dict__:
        inherited = first_declared_attr_in_mro(cls, 'from_dict')
        if getattr(inherited, '__func__', None) is fromdict:
            cls.from_dict = classmethod(fromdict)

    if 'to_dict' not in cls.__dict__:
        inherited = first_declared_attr_in_mro(cls, 'to_dict')
        if inherited is asdict:
            cls.to_dict = asdict


# noinspection PyShadowingBuiltins
def configure_wizard_class(cls,
                           str=False,
                           debug=False,
                           case=None,
                           dump_case=None,
                           load_case=None):
    load_meta_kwargs = {}

    if case is not None:
        load_meta_kwargs['case'] = case

    if dump_case is not None:
        load_meta_kwargs['dump_case'] = dump_case

    if load_case is not None:
        load_meta_kwargs['load_case'] = load_case

    if debug:
        # minimum logging level for logs by this library
        lvl = logging.DEBUG if isinstance(debug, bool) else debug
        # enable library logging
        enable_library_debug_logging(lvl)
        # set `debug` flag for the class's Meta
        load_meta_kwargs['debug'] = lvl

    if load_meta_kwargs:
        LoadMeta(**load_meta_kwargs).bind_to(cls)

    # Calls the Meta initializer when inner :class:`Meta` is sub-classed.
    call_meta_initializer_if_needed(cls)

    # Add a `__str__` method to the subclass, if needed
    if str:
        set_new_attribute(cls, '__str__', str_pprint_fn())

    # Add `from_dict` and `to_dict` methods to the subclass, if needed
    set_from_dict_and_to_dict_if_needed(cls)


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
                          _apply_dataclass=True,
                          **dc_kwargs):

        super().__init_subclass__()

        # skip classes provided by this library.
        if cls.__module__.startswith(f'{PACKAGE_NAME}.'):
            return

        # Apply the @dataclass decorator.
        if _apply_dataclass and dataclass_needs_refresh(cls):
            # noinspection PyArgumentList
            dataclass(cls, **dc_kwargs)

        configure_wizard_class(cls, str, debug, case, dump_case, load_case)


# noinspection PyAbstractClass
class JSONWizard(DataclassWizard):

    __slots__ = ()

    # noinspection PyShadowingBuiltins
    def __init_subclass__(cls,
                          str=False,
                          debug=False,
                          case=None,
                          dump_case=None,
                          load_case=None,
                          _apply_dataclass=False,
                          **_):

        super().__init_subclass__(str, debug, case, dump_case, load_case,
                                  _apply_dataclass)
