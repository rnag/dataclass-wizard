import json
from dataclasses import Field, MISSING
from typing import Any, Type, Dict, Tuple


class ParseError(Exception):
    """
    Base error class raised by this library.
    """
    _TEMPLATE = ('Failure parsing field `{field}` in class `{cls}`. Expected '
                 'a type {ann_type}, got {obj_type}.\n'
                 '  value: {o!r}\n'
                 '  error: {e!s}')

    def __init__(self, base_err: Exception, obj: Any, ann_type: Type, **kwargs):
        super().__init__()

        self.obj = obj
        self.obj_type = type(obj)
        self.ann_type = ann_type
        self.base_error = base_err
        self.kwargs = kwargs
        self.class_name: str = None
        self.field_name: str = None
        self._field_name = None

    @staticmethod
    def name(obj) -> str:
        """Return the type or class name of an object"""
        return getattr(obj, '__qualname__', getattr(obj, '__name__', obj))

    @property
    def message(self):
        msg = self._TEMPLATE.format(
            cls=self.class_name, field=self.field_name,
            e=self.base_error, o=self.obj,
            ann_type=self.name(self.ann_type),
            obj_type=self.name(self.obj_type))

        if self.kwargs:
            sep = '\n  '
            parts = sep.join(f'{k}: {v!r}' for k, v in self.kwargs.items())
            msg = f'{msg}{sep}{parts}'

        return msg

    def __str__(self):
        return self.message


class MissingFields(Exception):
    """
    Error raised when unable to create a class instance (most likely due to
    missing arguments)
    """
    _TEMPLATE = ('Failure calling constructor method of class `{cls}`. '
                 'Missing values for required dataclass fields.\n'
                 '  have fields: {fields!r}\n'
                 '  missing fields: {missing_fields!r}\n'
                 '  input JSON object: {json_string}\n'
                 '  error: {e!s}')

    def __init__(self, base_err: Exception,
                 obj: Dict[str, Any],
                 cls: Type,
                 cls_kwargs: Dict[str, Any],
                 cls_fields: Tuple[Field], **kwargs):

        super().__init__()

        self.obj = obj
        self.fields = list(cls_kwargs.keys())

        self.missing_fields = [f.name for f in cls_fields
                               if f.name not in self.fields
                               and f.default is MISSING
                               and f.default_factory is MISSING]
        self.base_error = base_err
        self.kwargs = kwargs
        self.class_name: str = self.name(cls)

    @staticmethod
    def name(obj) -> str:
        """Return the type or class name of an object"""
        return getattr(obj, '__qualname__', getattr(obj, '__name__', obj))

    @property
    def message(self):
        msg = self._TEMPLATE.format(
            cls=self.class_name,
            json_string=json.dumps(self.obj),
            e=self.base_error,
            fields=self.fields,
            missing_fields=self.missing_fields)

        if self.kwargs:
            sep = '\n  '
            parts = sep.join(f'{k}: {v!r}' for k, v in self.kwargs.items())
            msg = f'{msg}{sep}{parts}'

        return msg

    def __str__(self):
        return self.message
