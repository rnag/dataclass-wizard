from datetime import datetime, date, timezone
from typing import (
    Type, Dict, List, Tuple, Iterable, Sequence,
    Union, AnyStr, Optional, Callable,
)

from ..abstractions import AbstractParser
from ..bases import META
from ..decorators import _single_arg_alias
from ..loaders import LoadMixin, load_func_for_dataclass
from ..type_def import (
    FrozenKeys, DefFactory, M, N, U, DD, LSQ, NT, T, JSONObject
)
from ..utils.type_conv import (
    as_datetime, as_date, as_list, as_dict
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

        return base_type(o, encoding) if isinstance(o, str) else base_type(o)

    @staticmethod
    @_single_arg_alias('base_type')
    def load_to_uuid(o: Union[AnyStr, U], base_type: Type[U]) -> U:
        # alias: base_type(o)
        ...

    @staticmethod
    def load_to_iterable(
            o: Iterable, base_type: Type[LSQ],
            elem_parser: AbstractParser) -> LSQ:

        return super(EnvLoader, EnvLoader).load_to_iterable(
            as_list(o), base_type, elem_parser)

    @staticmethod
    def load_to_tuple(
            o: Union[List, Tuple], base_type: Type[Tuple],
            elem_parsers: Sequence[AbstractParser]) -> Tuple:

        return super(EnvLoader, EnvLoader).load_to_tuple(
            as_list(o), base_type, elem_parsers)

    @staticmethod
    def load_to_named_tuple(
            o: Union[Dict, List, Tuple], base_type: Type[NT],
            field_to_parser: 'FieldToParser',
            field_parsers: List[AbstractParser]) -> NT:

        # TODO check for both list and dict

        return super(EnvLoader, EnvLoader).load_to_named_tuple(
            as_list(o), base_type, field_to_parser, field_parsers)

    @staticmethod
    def load_to_named_tuple_untyped(
            o: Union[Dict, List, Tuple], base_type: Type[NT],
            dict_parser: AbstractParser, list_parser: AbstractParser) -> NT:

        return super(EnvLoader, EnvLoader).load_to_named_tuple_untyped(
            as_list(o), base_type, dict_parser, list_parser)

    @staticmethod
    def load_to_dict(
            o: Dict, base_type: Type[M],
            key_parser: AbstractParser,
            val_parser: AbstractParser) -> M:

        return super(EnvLoader, EnvLoader).load_to_dict(
            as_dict(o), base_type, key_parser, val_parser)

    @staticmethod
    def load_to_defaultdict(
            o: Dict, base_type: Type[DD],
            default_factory: DefFactory,
            key_parser: AbstractParser,
            val_parser: AbstractParser) -> DD:

        return super(EnvLoader, EnvLoader).load_to_defaultdict(
            as_dict(o), base_type, default_factory, key_parser, val_parser)

    @staticmethod
    def load_to_typed_dict(
            o: Dict, base_type: Type[M],
            key_to_parser: 'FieldToParser',
            required_keys: FrozenKeys,
            optional_keys: FrozenKeys) -> M:

        return super(EnvLoader, EnvLoader).load_to_typed_dict(
            as_dict(o), base_type, key_to_parser, required_keys, optional_keys)

    @staticmethod
    def load_to_datetime(
            o: Union[str, N], base_type: Type[datetime]) -> datetime:
        if isinstance(o, str):
            # Check if it's a string in numeric format, like '1.23'
            if o.replace('.', '', 1).isdigit():
                return base_type.fromtimestamp(float(o), tz=timezone.utc)

            return base_type.fromisoformat(o.replace('Z', '+00:00', 1))

        # default: as_datetime
        return as_datetime(o, base_type)

    @staticmethod
    def load_to_date(o: Union[str, N], base_type: Type[date]) -> date:
        if isinstance(o, str):
            # Check if it's a string in numeric format, like '1.23'
            if o.replace('.', '', 1).isdigit():
                return base_type.fromtimestamp(float(o))

            return base_type.fromisoformat(o)

        # default: as_date
        return as_date(o, base_type)

    @staticmethod
    def load_func_for_dataclass(
        cls: Type[T],
        config: Optional[META],
        is_main_class: bool = False,
    ) -> Callable[['str | JSONObject | T', Type[T]], T]:

        load = load_func_for_dataclass(
            cls,
            is_main_class=False,
            config=config,
            # override the loader class
            loader_cls=EnvLoader,
        )

        def load_to_dataclass(o: 'str | JSONObject | T', *_) -> T:
            """
            Receives either a string or a `dict` as an input, and return a
            dataclass instance of type `cls`.
            """
            if type(o) is cls:
                return o

            return load(as_dict(o))

        return load_to_dataclass
