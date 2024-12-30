from abc import ABC, abstractmethod
from dataclasses import Field, MISSING
from typing import (Any, Type, Dict, Tuple, ClassVar,
                    Optional, Union, Iterable, Callable, Collection, Sequence)

from .constants import PACKAGE_NAME
from .utils.string_conv import normalize


# added as we can't import from `type_def`, as we run into a circular import.
JSONObject = Dict[str, Any]


def type_name(obj: type) -> str:
    """Return the type or class name of an object"""
    from .utils.typing_compat import is_generic

    # for type generics like `dict[str, float]`, we want to return
    # the subscripted value as is, rather than simply accessing the
    # `__name__` property, which in this case would be `dict` instead.
    if is_generic(obj):
        return str(obj)

    return getattr(obj, '__qualname__', getattr(obj, '__name__', repr(obj)))


def show_deprecation_warning(
    fn: 'Callable | str',
    reason: str,
    fmt: str = "Deprecated function {name} ({reason})."
) -> None:
    """
    Display a deprecation warning for a given function.

    @param fn: Function which is deprecated.
    @param reason: Reason for the deprecation.
    @param fmt: Format string for the name/reason.
    """
    import warnings
    warnings.simplefilter('always', DeprecationWarning)
    warnings.warn(
        fmt.format(name=getattr(fn, '__name__', fn), reason=reason),
        category=DeprecationWarning,
        stacklevel=2,
    )


class JSONWizardError(ABC, Exception):
    """
    Base error class, for errors raised by this library.
    """

    _TEMPLATE: ClassVar[str]

    @property
    def class_name(self) -> Optional[str]:
        return self._class_name or self._default_class_name

    @class_name.setter
    def class_name(self, cls: Optional[Type]):
        # Set parent class for errors
        self.parent_cls = cls
        # Set class name
        if getattr(self, '_class_name', None) is None:
            # noinspection PyAttributeOutsideInit
            self._class_name = self.name(cls)

    @property
    def parent_cls(self) -> Optional[type]:
        return self._parent_cls

    @parent_cls.setter
    def parent_cls(self, cls: Optional[type]):
        # noinspection PyAttributeOutsideInit
        self._parent_cls = cls

    @staticmethod
    def name(obj) -> str:
        """Return the type or class name of an object"""
        # Uses short-circuiting with `or` to efficiently
        # return the first valid name.
        return (getattr(obj, '__qualname__', None)
                or getattr(obj, '__name__', None)
                or str(obj))

    @property
    @abstractmethod
    def message(self) -> str:
        """
        Format and return an error message.
        """

    def __str__(self):
        return self.message


class ParseError(JSONWizardError):
    """
    Base error when an error occurs during the JSON load process.
    """

    _TEMPLATE = ('Failure parsing field `{field}` in class `{cls}`. Expected '
                 'a type {ann_type}, got {obj_type}.\n'
                 '  value: {o!r}\n'
                 '  error: {e!s}')

    def __init__(self, base_err: Exception,
                 obj: Any,
                 ann_type: Optional[Union[Type, Iterable]],
                 _default_class: Optional[type] = None,
                 _field_name: Optional[str] = None,
                 _json_object: Any = None,
                 **kwargs):

        super().__init__()

        self.obj = obj
        self.obj_type = type(obj)
        self.ann_type = ann_type
        self.base_error = base_err
        self.kwargs = kwargs
        self._class_name = None
        self._default_class_name = self.name(_default_class) \
            if _default_class else None
        self._field_name = _field_name
        self._json_object = _json_object
        self.fields = None

    @property
    def field_name(self) -> Optional[str]:
        return self._field_name

    @field_name.setter
    def field_name(self, name: Optional[str]):
        if self._field_name is None:
            self._field_name = name

    @property
    def json_object(self):
        return self._json_object

    @json_object.setter
    def json_object(self, json_obj):
        if self._json_object is None:
            self._json_object = json_obj

    @property
    def message(self) -> str:

        ann_type = self.name(
            self.ann_type if self.ann_type is not None
            else next((f.type for f in self.fields
                       if f.name == self._field_name), None))

        msg = self._TEMPLATE.format(
            cls=self.class_name, field=self.field_name,
            e=self.base_error, o=self.obj,
            ann_type=ann_type,
            obj_type=self.name(self.obj_type))

        if self.json_object:
            from .utils.json_util import safe_dumps
            self.kwargs['json_object'] = safe_dumps(self.json_object)

        if self.kwargs:
            sep = '\n  '
            parts = sep.join(f'{k}: {v!r}' for k, v in self.kwargs.items())
            msg = f'{msg}{sep}{parts}'

        return msg


class ExtraData(JSONWizardError):
    """
    Error raised when extra keyword arguments are passed in to the constructor
    or `__init__()` method of an `EnvWizard` subclass.

    Note that this error class is raised by default, unless a value for the
    `extra` field is specified in the :class:`Meta` class.
    """

    _TEMPLATE = ('{cls}.__init__() received extra keyword arguments:\n'
                 '  extras: {extra_kwargs!r}\n'
                 '  fields: {field_names!r}\n'
                 '  resolution: specify a value for `extra` in the Meta '
                 'config for the class, to control how extra keyword '
                 'arguments are handled.')

    def __init__(self,
                 cls: Type,
                 extra_kwargs: Collection[str],
                 field_names: Collection[str]):

        super().__init__()

        self.class_name: str = type_name(cls)
        self.extra_kwargs = extra_kwargs
        self.field_names = field_names

    @property
    def message(self) -> str:
        msg = self._TEMPLATE.format(
            cls=self.class_name,
            extra_kwargs=self.extra_kwargs,
            field_names=self.field_names,
        )

        return msg


class MissingFields(JSONWizardError):
    """
    Error raised when unable to create a class instance (most likely due to
    missing arguments)
    """

    _TEMPLATE = ('`{cls}.__init__()` missing required fields.\n'
                 '  Provided: {fields!r}\n'
                 '  Missing: {missing_fields!r}\n'
                 '{expected_keys}'
                 '  Input JSON: {json_string}'
                 '{e}')

    def __init__(self, base_err: 'Exception | None',
                 obj: JSONObject,
                 cls: Type,
                 cls_fields: Tuple[Field, ...],
                 cls_kwargs: 'JSONObject | None' = None,
                 missing_fields: 'Collection[str] | None' = None,
                 missing_keys: 'Collection[str] | None' = None,
                 **kwargs):

        super().__init__()

        self.obj = obj

        if missing_fields:
            self.fields = [f.name for f in cls_fields
                           if f.name not in missing_fields
                           and f.default is MISSING
                           and f.default_factory is MISSING]
            self.missing_fields = missing_fields
        else:
            self.fields = list(cls_kwargs.keys())
            self.missing_fields = [f.name for f in cls_fields
                                   if f.name not in self.fields
                                   and f.default is MISSING
                                   and f.default_factory is MISSING]

        self.base_error = base_err
        self.missing_keys = missing_keys
        self.kwargs = kwargs
        self.class_name: str = self.name(cls)
        self.parent_cls = cls
        self.all_fields = cls_fields

    @property
    def message(self) -> str:
        from .class_helper import get_meta
        from .utils.json_util import safe_dumps

        # need to determine this, as we can't
        # directly import `class_helper.py`
        meta = get_meta(self.parent_cls)
        v1 = meta.v1

        if isinstance(self.obj, list):
            keys = [f.name for f in self.all_fields]
            obj = dict(zip(keys, self.obj))
        else:
            obj = self.obj

        # check if any field names match, and where the key transform could be the cause
        # see https://github.com/rnag/dataclass-wizard/issues/54 for more info

        normalized_json_keys = [normalize(key) for key in obj]
        if next((f for f in self.missing_fields if normalize(f) in normalized_json_keys), None):
            from .enums import LetterCase
            from .v1.enums import KeyCase
            from .loader_selection import get_loader

            key_transform = get_loader(self.parent_cls).transform_json_field
            if isinstance(key_transform, (LetterCase, KeyCase)):
                if key_transform.value is None:
                    key_transform = f'{key_transform.name}'
                else:
                    key_transform = f'{key_transform.value.f.__name__}()'
            elif key_transform is not None:
                key_transform = f'{getattr(key_transform, "__name__", key_transform)}()'

            self.kwargs['Key Transform'] = key_transform
            self.kwargs['Resolution'] = 'For more details, please see https://github.com/rnag/dataclass-wizard/issues/54'

        if v1:
            self.kwargs['Resolution'] = ('Ensure that all required fields are provided in the input. '
                                         'For more details, see:\n'
                                         '    https://github.com/rnag/dataclass-wizard/discussions/167')

        if self.base_error is not None:
            e = f'\n  error: {self.base_error!s}'
        else:
            e = ''

        if self.missing_keys is not None:
            expected_keys = f'  Expected Keys: {self.missing_keys!r}\n'
        else:
            expected_keys = ''

        msg = self._TEMPLATE.format(
            cls=self.class_name,
            json_string=safe_dumps(self.obj),
            e=e,
            fields=self.fields,
            expected_keys=expected_keys,
            missing_fields=self.missing_fields)

        if self.kwargs:
            sep = '\n  '
            parts = sep.join(f'{k}: {v}' for k, v in self.kwargs.items())
            msg = f'{msg}{sep}{parts}'

        return msg


class UnknownKeysError(JSONWizardError):
    """
    Error raised when unknown JSON key(s) are
    encountered in the JSON load process.

    Note that this error class is only raised when the
    `raise_on_unknown_json_key` flag is enabled in
    the :class:`Meta` class.
    """

    _TEMPLATE = ('One or more JSON keys are not mapped to the dataclass schema for class `{cls}`.\n'
                 '  Unknown key{s}: {unknown_keys!r}\n'
                 '  Dataclass fields: {fields!r}\n'
                 '  Input JSON object: {json_string}')

    def __init__(self,
                 unknown_keys: 'list[str] | str',
                 obj: JSONObject,
                 cls: Type,
                 cls_fields: Tuple[Field, ...], **kwargs):
        super().__init__()

        self.unknown_keys = unknown_keys
        self.obj = obj
        self.fields = [f.name for f in cls_fields]
        self.kwargs = kwargs
        self.class_name: str = self.name(cls)

    @property
    def json_key(self):
        show_deprecation_warning(
            UnknownKeysError.json_key.fget,
            'use `unknown_keys` instead',
        )
        return self.unknown_keys

    @property
    def message(self) -> str:
        from .utils.json_util import safe_dumps
        if not isinstance(self.unknown_keys, str) and len(self.unknown_keys) > 1:
            s = 's'
        else:
            s = ''

        msg = self._TEMPLATE.format(
            cls=self.class_name,
            s=s,
            json_string=safe_dumps(self.obj),
            fields=self.fields,
            unknown_keys=self.unknown_keys)

        if self.kwargs:
            sep = '\n  '
            parts = sep.join(f'{k}: {v!r}' for k, v in self.kwargs.items())
            msg = f'{msg}{sep}{parts}'

        return msg


# Alias for backwards-compatibility.
UnknownJSONKey = UnknownKeysError


class MissingData(ParseError):
    """
    Error raised when unable to create a class instance, as the JSON object
    is None.
    """

    _TEMPLATE = ('Failure loading class `{cls}`. '
                 'Missing value for field (expected a dict, got None)\n'
                 '  dataclass field: {field!r}\n'
                 '  resolution: annotate the field as '
                 '`Optional[{nested_cls}]` or `{nested_cls} | None`')

    def __init__(self, nested_cls: Type, **kwargs):
        super().__init__(self, None, nested_cls, **kwargs)
        self.nested_class_name: str = self.name(nested_cls)

        # self.nested_class_name: str = type_name(nested_cls)

    @property
    def message(self) -> str:
        from .utils.json_util import safe_dumps

        msg = self._TEMPLATE.format(
            cls=self.class_name,
            nested_cls=self.nested_class_name,
            json_string=safe_dumps(self.obj),
            field=self.field_name,
            o=self.obj,
        )

        if self.kwargs:
            sep = '\n  '
            parts = sep.join(f'{k}: {v!r}' for k, v in self.kwargs.items())
            msg = f'{msg}{sep}{parts}'

        return msg


class RecursiveClassError(JSONWizardError):
    """
    Error raised when we encounter a `RecursionError` due to cyclic
    or self-referential dataclasses.
    """

    _TEMPLATE = ('Failure parsing class `{cls}`. '
                 'Consider updating the Meta config to enable '
                 'the `recursive_classes` flag.\n\n'
                f'Example with `{PACKAGE_NAME}.LoadMeta`:\n'
                 ' >>> LoadMeta(recursive_classes=True).bind_to({cls})\n\n'
                 'For more info, please see:\n'
                 '  https://github.com/rnag/dataclass-wizard/issues/62')

    def __init__(self, cls: Type):
        super().__init__()

        self.class_name: str = self.name(cls)

    @property
    def message(self) -> str:
        return self._TEMPLATE.format(cls=self.class_name)


class InvalidConditionError(JSONWizardError):
    """
    Error raised when a condition is not wrapped in ``SkipIf``.
    """

    _TEMPLATE = ('Failure parsing annotations for class `{cls}`. '
                 'Field has an invalid condition.\n'
                 '  dataclass field: {field!r}\n'
                 '  resolution: Wrap conditions inside SkipIf().`')

    def __init__(self, cls: Type, field_name: str):
        super().__init__()

        self.class_name: str = self.name(cls)
        self.field_name: str = field_name

    @property
    def message(self) -> str:
        return self._TEMPLATE.format(cls=self.class_name,
                                     field=self.field_name)


class MissingVars(JSONWizardError):
    """
    Error raised when unable to create an instance of a EnvWizard subclass
    (most likely due to missing environment variables in the Environment)

    """
    _TEMPLATE = ('\n`{cls}` has {prefix} missing in the environment:\n'
                 '{fields}\n\n'
                 '**Resolution options**\n\n'
                 '1. Set a default value for the field:\n\n'
                 '{def_resolution}'
                 '\n\n'
                 '2. Provide the value during initialization:\n\n'
                 '    {init_resolution}')

    def __init__(self,
                 cls: Type,
                 missing_vars: Sequence[Tuple[str, 'str | None', str, Any]]):

        super().__init__()

        indent = ' ' * 4

        #   - `name` (mapped to `CUSTOM_A_NAME`)
        self.class_name: str = type_name(cls)
        self.fields = '\n'.join([f'{indent}- {f[0]} -> {f[1]}' for f in missing_vars])
        self.def_resolution = '\n'.join([f'{indent}class {self.class_name}:'] +
                                        [f'{indent * 2}{f}: {typ} = {default!r}'
                                         for (f, _, typ, default) in missing_vars])

        init_vars = ', '.join([f'{f}={default!r}' for (f, _, typ, default) in missing_vars])
        self.init_resolution = f'instance = {self.class_name}({init_vars})'

        num_fields = len(missing_vars)
        self.prefix = f'{len(missing_vars)} required field{"s" if num_fields > 1 else ""}'

    @property
    def message(self) -> str:
        msg = self._TEMPLATE.format(
            cls=self.class_name,
            prefix=self.prefix,
            fields=self.fields,
            def_resolution=self.def_resolution,
            init_resolution=self.init_resolution,
        )

        return msg
