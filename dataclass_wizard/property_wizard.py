from dataclasses import MISSING, Field
from functools import wraps
from typing import Dict, Any, Type, Union, Tuple, Optional

from .type_def import T, NoneType
from .utils.type_check import (
    get_type_hints_with_extras, get_origin, get_args,
    is_generic, is_literal, is_annotated
)


AnnotationType = Dict[str, Type[T]]


def property_wizard(*args, **kwargs):
    """
    Adds support for field properties with default values in dataclasses.

    For examples of usage, please see the `Using Field Properties`_ section in
    the docs. I also added `an answer`_ on a SO article that deals with using
    such properties in dataclasses.

    .. _Using Field Properties: https://dataclass-wizard.readthedocs.io/en/latest/using_field_properties.html
    .. _an answer: https://stackoverflow.com/a/68488125/10237506
    """

    cls: Type = type(*args, **kwargs)
    cls_dict: Dict[str, Any] = args[2]
    annotations: AnnotationType = get_type_hints_with_extras(cls)

    # For each property, we want to replace the annotation for the underscore-
    # leading field associated with that property with the 'public' field
    # name, and this mapping helps us keep a track of that.
    annotation_repls: Dict[str, str] = {}

    for f, val in cls_dict.items():

        if isinstance(val, property):

            if val.fset is None:
                # The property is read-only, not settable
                continue

            if not f.startswith('_'):
                # The property is marked as 'public' (i.e. no leading
                # underscore)
                _process_public_property(
                    cls, f, val, annotations, annotation_repls)
            else:
                # The property is marked as 'private'
                _process_underscored_property(
                    cls, f, val, annotations, annotation_repls)

    if annotation_repls:
        # Use a comprehension approach because we want to replace a
        # key while preserving the insertion order, because the order
        # of fields does matter when the constructor is called.
        cls.__annotations__ = {annotation_repls.get(f, f): ftype
                               for f, ftype in cls.__annotations__.items()}

    return cls


def _process_public_property(cls: Type, public_f: str, val: property,
                             annotations: AnnotationType,
                             annotation_repls: Dict[str, str]):
    """
    Handles the case when the property is marked as 'public' (i.e. no leading
    underscore)
    """

    # The field with a leading underscore
    under_f = '_' + public_f
    default = None

    if public_f in annotations or under_f in annotations:

        if under_f in annotations:
            # Also add it to the list of class annotations to replace later
            #   (this is what `dataclasses` uses to add the field to the
            #   constructor)
            annotation_repls[under_f] = public_f

            try:
                # Get the value of the underscored field
                default = getattr(cls, under_f)
            except AttributeError:
                # The public field is probably type-annotated but not defined
                #   i.e. my_var: str
                default = _default_from_annotation(annotations, under_f)
            else:
                # Check if the value of underscored field is a dataclass Field.
                # If so, we can use the `default` if one is set.
                if isinstance(default, Field):
                    default = _default_from_field(annotations, under_f, default)
                # Delete the field that starts with an underscore. This is needed
                # since we'll be replacing the annotation for `under_f` later, and
                # `dataclasses` will complain if it sees a variable which is a
                # `Field` that appears to be missing a type annotation.
                delattr(cls, under_f)

        if public_f in annotations and not default:
            default = _default_from_annotation(annotations, public_f)

    else:
        # adding this to check if it's a regular property (not
        # associated with a dataclass field)
        return

    # Wraps the `setter` for the property
    val = val.setter(_wrapper(val.fset, default))

    # Set the field that does not start with an underscore
    setattr(cls, public_f, val)


def _process_underscored_property(cls: Type, under_f: str, val: property,
                                  annotations: AnnotationType,
                                  annotation_repls: Dict[str, str]):
    """
    Handles the case when the property is marked as 'private' (i.e. leads with
    an underscore)
    """

    # The field *without* a leading underscore
    public_f = under_f.lstrip('_')
    default = None

    if public_f in annotations or under_f in annotations:

        if under_f in annotations:
            # Also add it to the list of class annotations to replace later
            #   (this is what `dataclasses` uses to add the field to the
            #   constructor)
            annotation_repls[under_f] = public_f
            default = _default_from_annotation(annotations, under_f)

        if public_f in annotations:
            # First, get the type annotation for the public field
            default = _default_from_annotation(annotations, public_f)

            if not default and hasattr(cls, public_f):
                # Get the value of the field without a leading underscore
                default = getattr(cls, public_f)
                # Check if the value of the public field is a dataclass Field.
                # If so, we can use the `default` if one is set.
                if isinstance(default, Field):
                    default = _default_from_field(
                        annotations, public_f, default)

    else:
        # adding this to check if it's a regular property (not
        # associated with a dataclass field)
        return

    # Wraps the `setter` for the property
    val = val.setter(_wrapper(val.fset, default))

    # Replace the value of the field without a leading underscore
    setattr(cls, public_f, val)

    # Delete the property associated with the underscored field name.
    # This is technically not needed, but it supports cases where we
    # define an attribute with the same name as the property, i.e.
    #    @property
    #    def _wheels(self)
    #        return self._wheels
    delattr(cls, under_f)


def _default_from_field(cls_annotations: AnnotationType,
                        field: str, field_val: Field):
    """
    Get the default value for `field`, which is defined as a
    :class:`dataclasses.Field`. If no `default` or `default_factory` is
    defined, then return the default value from the annotated type instead.
    """

    if field_val.default is not MISSING:
        return field_val.default
    elif field_val.default_factory is not MISSING:
        return field_val.default_factory()
    else:
        return _default_from_annotation(cls_annotations, field)


def _default_from_annotation(cls_annotations: AnnotationType, field: str):
    """
    Get the default value for the type annotated on a field. Note that we
    include a check to see if the annotated type is a `Generic` type from the
    ``typing`` module.
    """

    default_type = cls_annotations.get(field)

    if is_generic(default_type):
        # Annotated type is a Generic from the `typing` module
        return _default_from_generic_type(default_type, field)

    try:
        return default_type()
    except TypeError:
        return None


def _default_from_generic_type(default_type: Type[T], field: Optional[str] = None):
    """
    Process a Generic type from the `typing` module, and return the default
    value for the annotated type.
    """

    args = get_args(default_type)

    if is_annotated(default_type):
        # The Generic type appears as `Annotated[T, extras...]`
        default_type, *extras = args
        # Loop over and search for any `dataclasses.Field` types
        for extra in extras:
            if isinstance(extra, Field):
                return _default_from_field(
                    {field: default_type}, field, extra)
        # Else, if none of the extras are particularly useful, just process
        # type `T`, which can be either a concrete or Generic sub-type.
        return _default_from_annotation({field: default_type}, field)

    if is_literal(default_type):
        # The Generic type appears as `Literal["r", "r+", ...]`
        return _default_from_typing_args(args)

    if get_origin(default_type) is Union:
        # The Generic type appears as `Optional[T]` or `Union[T1, T2, ...]`
        default_type = _default_from_typing_args(args)
        if default_type is not None:
            return default_type()
        return None


def _default_from_typing_args(args: Optional[Tuple[Type[T], ...]]):
    """
    `args` is the type arguments for a generic annotated type from the
    ``typing`` module. For example, given a generic type `Union[str, int]`,
    the args will be a tuple of (str, int).

    If `None` is included in the typed args for `cls`, then it's perfectly
    valid to return `None` as the default. Otherwise, we'll just use the first
    type in the list of args.

    """

    if args and NoneType not in args:
        try:
            return args[0]
        except TypeError:   # pragma: no cover
            return None
    return None


def _wrapper(fset, initial_val):
    """
    Wraps the property `setter` method to check if we are passed in a property
    object itself, which will be true when no initial value is specified.
    """

    @wraps(fset)
    def new_fset(self, value):
        if isinstance(value, property):
            value = initial_val
        fset(self, value)

    return new_fset
