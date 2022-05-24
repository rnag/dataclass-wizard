import json
from datetime import datetime, date
from typing import (
    Type, Dict, List, Tuple, Iterable, Sequence, Union,
    AnyStr
)

from ..abstractions import AbstractParser, FieldToParser
from ..class_helper import (
    create_new_class,
    dataclass_to_loader, set_class_loader,
)
from ..constants import _LOAD_HOOKS
from ..decorators import _single_arg_alias
from ..loaders import LoadMixin
from ..type_def import (
    FrozenKeys, DefFactory, M, N, U, DD, LSQ, NT
)
from ..utils.type_conv import (
    as_datetime, as_date
)


class EnvLoader(LoadMixin):
    """
    This Mixin class derives its name from the eponymous `json.loads`
    function. Essentially it contains helper methods to convert JSON strings
    (or a Python dictionary object) to a `dataclass` which can often contain
    complex types such as lists, dicts, or even other dataclasses nested
    within it.

    Refer to the :class:`AbstractLoader` class for documentation on any of the
    implemented methods.

    """
    __slots__ = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()

        cls.register_load_hook(bytes, cls.load_to_bytes)
        cls.register_load_hook(bytearray, cls.load_to_byte_array)

    @staticmethod
    def load_to_bytes(
            o: AnyStr, base_type: Type[bytes], encoding='utf-8') -> bytes:

        return base_type(o, encoding)

    @staticmethod
    def load_to_byte_array(
            o: AnyStr, base_type: Type[bytearray],
            encoding='utf-8') -> bytearray:

        encoded_string = o.encode(encoding)
        return base_type(encoded_string)

    @staticmethod
    @_single_arg_alias('base_type')
    def load_to_uuid(o: Union[AnyStr, U], base_type: Type[U]) -> U:
        # alias: base_type(o)
        ...

    @staticmethod
    def load_to_iterable(
            o: Iterable, base_type: Type[LSQ],
            elem_parser: AbstractParser) -> LSQ:

        if isinstance(o, str):
            if o.lstrip().startswith('['):
                o = json.loads(o)
            else:
                o = map(str.strip, o.split(','))

        return super(EnvLoader, EnvLoader).load_to_iterable(
            o, base_type, elem_parser)

    @staticmethod
    def load_to_tuple(
            o: Union[List, Tuple], base_type: Type[Tuple],
            elem_parsers: Sequence[AbstractParser]) -> Tuple:

        return super(EnvLoader, EnvLoader).load_to_tuple(
            o, base_type, elem_parsers)

    @staticmethod
    def load_to_named_tuple(
            o: Union[Dict, List, Tuple], base_type: Type[NT],
            field_to_parser: FieldToParser,
            field_parsers: List[AbstractParser]) -> NT:

        # TODO check for both list and dict

        return super(EnvLoader, EnvLoader).load_to_named_tuple(
            o, base_type, field_to_parser, field_parsers)

    @staticmethod
    def load_to_named_tuple_untyped(
            o: Union[Dict, List, Tuple], base_type: Type[NT],
            dict_parser: AbstractParser, list_parser: AbstractParser) -> NT:

        return super(EnvLoader, EnvLoader).load_to_named_tuple_untyped(
            o, base_type, dict_parser, list_parser)

    @staticmethod
    def load_to_dict(
            o: Dict, base_type: Type[M],
            key_parser: AbstractParser,
            val_parser: AbstractParser) -> M:

        return super(EnvLoader, EnvLoader).load_to_dict(
            o, base_type, key_parser, val_parser)

    @staticmethod
    def load_to_defaultdict(
            o: Dict, base_type: Type[DD],
            default_factory: DefFactory,
            key_parser: AbstractParser,
            val_parser: AbstractParser) -> DD:

        return super(EnvLoader, EnvLoader).load_to_defaultdict(
            o, base_type, default_factory, key_parser, val_parser)

    @staticmethod
    def load_to_typed_dict(
            o: Dict, base_type: Type[M],
            key_to_parser: FieldToParser,
            required_keys: FrozenKeys,
            optional_keys: FrozenKeys) -> M:

        return super(EnvLoader, EnvLoader).load_to_typed_dict(
            o, base_type, key_to_parser, required_keys, optional_keys)

    @staticmethod
    def load_to_datetime(
            o: Union[str, N], base_type: Type[datetime]) -> datetime:
        # Check if it's a string in numeric format, like '1.23'
        if isinstance(o, str) and o.replace('.', '', 1).isdigit():
            return base_type.fromtimestamp(float(o))
        # default: as_datetime
        return as_datetime(o, base_type)

    @staticmethod
    def load_to_date(o: Union[str, N], base_type: Type[date]) -> date:
        # Check if it's a string in numeric format, like '1.23'
        if isinstance(o, str) and o.replace('.', '', 1).isdigit():
            return base_type.fromtimestamp(float(o))
        # default: as_date
        return as_date(o, base_type)


def get_loader(class_or_instance=None, create=True) -> Type[EnvLoader]:
    """
    Get the loader for the class, using the following logic:

        * Return the class if it's already a sub-class of :class:`LoadMixin`
        * If `create` is enabled (which is the default), a new sub-class of
          :class:`LoadMixin` for the class will be generated and cached on the
          initial run.
        * Otherwise, we will return the base loader, :class:`LoadMixin`, which
          can potentially be shared by more than one dataclass.

    """
    try:
        return dataclass_to_loader(class_or_instance)

    except KeyError:

        if hasattr(class_or_instance, _LOAD_HOOKS):
            return set_class_loader(class_or_instance, class_or_instance)

        elif create:
            cls_loader = create_new_class(class_or_instance, (EnvLoader, ))
            return set_class_loader(class_or_instance, cls_loader)

        return set_class_loader(class_or_instance, EnvLoader)
