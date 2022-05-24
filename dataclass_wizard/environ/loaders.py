import json
from datetime import datetime, date
from typing import (
    Type, Dict, List, Tuple, Iterable, Sequence, Union,
    AnyStr, Callable
)

from ..abstractions import AbstractParser, FieldToParser
from ..class_helper import (
    get_class_name, create_new_class,
    dataclass_to_loader, set_class_loader,
    dataclass_field_to_load_parser, json_field_to_dataclass_field,
    _CLASS_TO_LOAD_FUNC, dataclass_fields, get_meta, )
from ..constants import _LOAD_HOOKS
from ..decorators import _single_arg_alias
from ..errors import ParseError, MissingFields, UnknownJSONKey, MissingData
from ..loaders import LoadMixin
from ..log import LOG
from ..type_def import (
    ExplicitNull, FrozenKeys, DefFactory, JSONObject,
    M, N, T, U, DD, LSQ, NT
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


def fromdict(cls: Type[T], d: JSONObject) -> T:
    """
    Converts a Python dictionary object to a dataclass instance.

    Iterates over each dataclass field recursively; lists, dicts, and nested
    dataclasses will likewise be initialized as expected.

    When directly invoking this function, an optional Meta configuration for
    the dataclass can be specified via ``LoadMeta``; by default, this will
    apply recursively to any nested dataclasses. Here's a sample usage of this
    below::

        >>> LoadMeta(key_transform='CAMEL').bind_to(MyClass)
        >>> fromdict(MyClass, {"myStr": "value"})

    """
    try:
        load = _CLASS_TO_LOAD_FUNC[cls]
    except KeyError:
        load = load_func_for_dataclass(cls)

    return load(d)


def load_func_for_dataclass(cls: Type[T]) -> Callable[[JSONObject], T]:

    # Get the loader for the class, or create a new one as needed.
    cls_loader = get_loader(cls)

    # Get the meta config for the class, or the default config otherwise.
    meta = get_meta(cls)

    # This contains a mapping of the original field name to the parser for its
    # annotated type; the item lookup *can* be case-insensitive.
    # TODO CHANGE
    field_to_parser = dataclass_field_to_load_parser(cls_loader, cls, meta)

    # A cached mapping of each key in a JSON or dictionary object to the
    # resolved dataclass field name; useful so we don't need to do a case
    # transformation (via regex) each time.
    json_to_dataclass_field = json_field_to_dataclass_field(cls)

    def cls_fromdict(o: JSONObject, *_):
        """
        De-serialize a dictionary `o` to an instance of a dataclass `cls`.
        """

        # Need to create a separate dictionary to copy over the constructor
        # args, as we don't want to mutate the original dictionary object.
        cls_kwargs = {}

        # This try-block is here in case the object `o` is None.
        try:
            # Loop over the dictionary object
            for json_key in o:

                # Get the resolved dataclass field name
                try:
                    field_name = json_to_dataclass_field[json_key]
                    # Exclude JSON keys that don't map to any fields.
                    if field_name is ExplicitNull:
                        continue

                except KeyError:
                    try:
                        field_name = lookup_field_for_json_key(o, json_key)
                    except LookupError:
                        continue

                try:
                    # Note: pass the original cased field to the class
                    # constructor; don't use the lowercase result from
                    # `transform_json_field`
                    cls_kwargs[field_name] = field_to_parser[field_name](
                        o[json_key])

                except ParseError as e:
                    # We run into a parsing error while loading the field
                    # value; Add additional info on the Exception object
                    # before re-raising it.
                    #
                    # First confirm these values are not already set by an
                    # inner dataclass. If so, it likely makes it easier to
                    # debug the cause. Note that this should already be
                    # handled by the `setter` methods.
                    e.class_name = cls
                    e.field_name = field_name
                    raise

        except TypeError:
            # If the object `o` is None, then raise an error with the relevant
            # info included. Else, just re-raise the error.
            if o is None:
                raise MissingData(cls) from None
            raise

        # Now pass the arguments to the constructor method, and return the new
        # dataclass instance. If there are any missing fields, we raise them
        # here.

        try:
            return cls(**cls_kwargs)

        except TypeError as e:
            raise MissingFields(
                e, o, cls, cls_kwargs, dataclass_fields(cls)
            ) from None

    def lookup_field_for_json_key(o: JSONObject, json_field: str):
        """
        Determines the dataclass field which a JSON key should map to. Note
        this only runs the initial time, i.e. the first time we encounter the
        key in a JSON object.

        :raises LookupError: If there no resolved field name for the JSON key.
        :raises UnknownJSONKey: If there is no resolved field name for the
          JSON key, and`raise_on_unknown_json_key` is enabled in the Meta
          config for the class.
        """

        # Transform JSON field name (typically camel-cased) to the
        # snake-cased variant which is convention in Python.
        transformed_field = cls_loader.transform_json_field(json_field)

        try:
            # Do a case-insensitive lookup of the dataclass field, and
            # cache the mapping so we have it for next time
            field_name = field_to_parser.get_key(transformed_field)
            json_to_dataclass_field[json_field] = field_name

        except KeyError:
            # Else, we see an unknown field in the dictionary object
            json_to_dataclass_field[json_field] = ExplicitNull
            LOG.warning(
                'JSON field %r missing from dataclass schema, '
                'class=%r, parsed field=%r',
                json_field, get_class_name(cls), transformed_field)

            # Raise an error here (if needed)
            if meta.raise_on_unknown_json_key:
                cls_fields = dataclass_fields(cls)
                e = UnknownJSONKey(json_field, o, cls, cls_fields)
                raise e from None

            raise LookupError

        return field_name

    # Save the load function for the class, so we don't need to run
    # this logic each time.
    _CLASS_TO_LOAD_FUNC[cls] = cls_fromdict

    return cls_fromdict
