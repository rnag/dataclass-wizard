from typing import Callable, Type, Dict, Optional, ClassVar


class BaseLoadHook:
    """
    Container class for type hooks.
    """
    __slots__ = ()

    __LOAD_HOOKS__: ClassVar[Dict[Type, Callable]] = None

    def __init_subclass__(cls):
        super().__init_subclass__()
        # (Re)assign the dict object so we have a fresh copy per class
        cls.__LOAD_HOOKS__ = {}

    @classmethod
    def register_load_hook(cls, typ: Type, func: Callable):
        """Registers the hook for a type, on the default loader by default."""
        cls.__LOAD_HOOKS__[typ] = func

    @classmethod
    def get_load_hook(cls, typ: Type) -> Optional[Callable]:
        """Retrieves the hook for a type, if one exists."""
        return cls.__LOAD_HOOKS__.get(typ)


class BaseDumpHook:
    """
    Container class for type hooks.
    """
    __slots__ = ()

    __DUMP_HOOKS__: ClassVar[Dict[Type, Callable]] = None

    def __init_subclass__(cls):
        super().__init_subclass__()
        # (Re)assign the dict object so we have a fresh copy per class
        cls.__DUMP_HOOKS__ = {}

    @classmethod
    def register_dump_hook(cls, typ: Type, func: Callable):
        """Registers the hook for a type, on the default dumper by default."""
        cls.__DUMP_HOOKS__[typ] = func

    @classmethod
    def get_dump_hook(cls, typ: Type) -> Optional[Callable]:
        """Retrieves the hook for a type, if one exists."""
        return cls.__DUMP_HOOKS__.get(typ)
