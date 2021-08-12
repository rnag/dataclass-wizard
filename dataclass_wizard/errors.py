from typing import Any, Type


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
