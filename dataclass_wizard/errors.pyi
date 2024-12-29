import warnings
from abc import ABC, abstractmethod
from dataclasses import Field
from typing import (Any, ClassVar, Iterable, Callable, Collection, Sequence)


# added as we can't import from `type_def`, as we run into a circular import.
JSONObject = dict[str, Any]


def type_name(obj: type) -> str:
    """Return the type or class name of an object"""


def show_deprecation_warning(
    fn: Callable | str,
    reason: str,
    fmt: str = "Deprecated function {name} ({reason})."
) -> None:
    """
    Display a deprecation warning for a given function.

    @param fn: Function which is deprecated.
    @param reason: Reason for the deprecation.
    @param fmt: Format string for the name/reason.
    """


class JSONWizardError(ABC, Exception):
    """
    Base error class, for errors raised by this library.
    """

    _TEMPLATE: ClassVar[str]

    _parent_cls: type
    _class_name: str | None
    _default_class_name: str | None

    def class_name(self) -> str | None: ...
    # noinspection PyRedeclaration
    def class_name(self) -> None: ...

    def parent_cls(self) -> type | None: ...
    # noinspection PyRedeclaration
    def parent_cls(self, value: type | None) -> None: ...

    @staticmethod
    def name(obj) -> str: ...

    @property
    @abstractmethod
    def message(self) -> str:
        """
        Format and return an error message.
        """

    def __str__(self) -> str: ...


class ParseError(JSONWizardError):
    """
    Base error when an error occurs during the JSON load process.
    """

    _TEMPLATE: str

    obj: Any
    obj_type: type
    ann_type: type | Iterable | None
    base_error: Exception
    kwargs: dict[str, Any]
    _class_name: str | None
    _default_class_name: str | None
    _field_name: str | None
    _json_object: Any | None
    fields: Collection[Field] | None

    def __init__(self, base_err: Exception,
                 obj: Any,
                 ann_type: type | Iterable | None,
                 _default_class: type | None = None,
                 _field_name: str | None = None,
                 _json_object: Any = None,
                 **kwargs):
        ...

    @property
    def field_name(self) -> str | None:
        ...

    @property
    def json_object(self):
        ...

    @property
    def message(self) -> str: ...


class ExtraData(JSONWizardError):
    """
    Error raised when extra keyword arguments are passed in to the constructor
    or `__init__()` method of an `EnvWizard` subclass.

    Note that this error class is raised by default, unless a value for the
    `extra` field is specified in the :class:`Meta` class.
    """

    _TEMPLATE: str

    class_name: str
    extra_kwargs: Collection[str]
    field_names: Collection[str]

    def __init__(self,
                 cls: type,
                 extra_kwargs: Collection[str],
                 field_names: Collection[str]):
        ...

    @property
    def message(self) -> str: ...


class MissingFields(JSONWizardError):
    """
    Error raised when unable to create a class instance (most likely due to
    missing arguments)
    """

    _TEMPLATE: str

    obj: JSONObject
    fields: list[str]
    all_fields: tuple[Field, ...]
    missing_fields: Collection[str]
    base_error: Exception | None
    missing_keys: Collection[str] | None
    kwargs: dict[str, Any]
    class_name: str
    parent_cls: type

    def __init__(self, base_err: Exception | None,
                 obj: JSONObject,
                 cls: type,
                 cls_fields: tuple[Field, ...],
                 cls_kwargs: JSONObject | None = None,
                 missing_fields: Collection[str] | None = None,
                 missing_keys: Collection[str] | None = None,
                 **kwargs):
        ...

    @property
    def message(self) -> str: ...


class UnknownKeysError(JSONWizardError):
    """
    Error raised when unknown JSON key(s) are
    encountered in the JSON load process.

    Note that this error class is only raised when the
    `raise_on_unknown_json_key` flag is enabled in
    the :class:`Meta` class.
    """

    _TEMPLATE: str

    unknown_keys: list[str] | str
    obj: JSONObject
    fields: list[str]
    kwargs: dict[str, Any]
    class_name: str

    def __init__(self,
                 unknown_keys: list[str] | str,
                 obj: JSONObject,
                 cls: type,
                 cls_fields: tuple[Field, ...],
                 **kwargs):
        ...

    @property
    @warnings.deprecated('use `unknown_keys` instead')
    def json_key(self) -> list[str] | str: ...

    @property
    def message(self) -> str: ...


# Alias for backwards-compatibility.
UnknownJSONKey = UnknownKeysError


class MissingData(ParseError):
    """
    Error raised when unable to create a class instance, as the JSON object
    is None.
    """

    _TEMPLATE: str

    nested_class_name: str

    def __init__(self, nested_cls: type, **kwargs):
        ...

    @property
    def message(self) -> str: ...


class RecursiveClassError(JSONWizardError):
    """
    Error raised when we encounter a `RecursionError` due to cyclic
    or self-referential dataclasses.
    """

    _TEMPLATE: str

    class_name: str

    def __init__(self, cls: type): ...

    @property
    def message(self) -> str: ...


class InvalidConditionError(JSONWizardError):
    """
    Error raised when a condition is not wrapped in ``SkipIf``.
    """

    _TEMPLATE: str

    class_name: str
    field_name: str

    def __init__(self, cls: type, field_name: str):
        ...

    @property
    def message(self) -> str: ...


class MissingVars(JSONWizardError):
    """
    Error raised when unable to create an instance of a EnvWizard subclass
    (most likely due to missing environment variables in the Environment)

    """
    _TEMPLATE: str

    class_name: str
    fields: str
    def_resolution: str
    init_resolution: str
    prefix: str

    def __init__(self,
                 cls: type,
                 missing_vars: Sequence[tuple[str, str | None, str, Any]]):
        ...

    @property
    def message(self) -> str: ...
