from dataclasses import MISSING, Field
from functools import wraps
from typing import Dict, Any, get_type_hints


def property_wizard(*args, **kwargs):
    """Adds support for using properties with default values in dataclasses."""
    cls = type(*args, **kwargs)
    cls_dict: Dict[str, Any] = args[2]
    annotations = get_type_hints(cls)

    def get_default_from_annotation(field_: str):
        """Get the default value for the type annotated on a field"""
        default_type = annotations.get(field_)
        try:
            return default_type()
        except TypeError:
            return None

    # For each property, we want to replace the annotation for the underscore-
    # leading field associated with that property with the 'public' field
    # name, and this mapping helps us keep a track of that.
    annotation_repls = {}

    for f, val in cls_dict.items():

        if isinstance(val, property):

            if val.fset is None:
                # The property is read-only, not settable
                continue

            if f.startswith('_'):
                # The property is marked as 'private' (i.e. starts with an underscore)

                # The field *without* a leading underscore
                public_f = f.lstrip('_')

                if val.fset is None:
                    # property is read-only, not settable
                    continue

                if f not in annotations and public_f not in annotations:
                    # adding this to check if it's a regular property (not
                    # associated with a dataclass field)
                    continue

                try:
                    # Get the value of the field named without a leading underscore
                    default = getattr(cls, public_f)
                except AttributeError:
                    # The public field is probably type-annotated but not defined
                    #   i.e. my_var: str
                    default = get_default_from_annotation(public_f)
                else:
                    if isinstance(default, property):
                        # The public field is a property
                        # Check if the value of underscored field is a dataclass
                        # Field. If so, we can use the `default` if one is set.
                        f_val = getattr(cls, '_' + f, None)
                        if isinstance(f_val, Field):
                            if f_val.default is not MISSING:
                                default = f_val.default
                            elif f_val.default_factory is not MISSING:
                                default = f_val.default_factory()
                            else:
                                default = get_default_from_annotation(public_f)
                        else:
                            default = get_default_from_annotation(public_f)

                # Wraps the `setter` for the property
                val = val.setter(_wrapper(val.fset, default))

                # Replace the value of the field without a leading underscore
                setattr(cls, public_f, val)

                # Delete the property if the field name starts with an underscore
                # This is technically not needed, but it supports cases where we
                # define an attribute with the same name as the property, i.e.
                #    @property
                #    def _wheels(self)
                #        return self._wheels
                if f.startswith('_'):
                    delattr(cls, f)

            else:
                # The property is marked as 'public' (i.e. no leading underscore)

                # The field with a leading underscore
                under_f = '_' + f

                try:
                    # Get the value of the underscored field
                    default = getattr(cls, under_f)
                except AttributeError:
                    # The public field is probably type-annotated but not defined
                    #   i.e. my_var: str
                    default = get_default_from_annotation(under_f)
                else:
                    # Check if the value of underscored field is a dataclass
                    # Field. If so, we can use the `default` if one is set.
                    if isinstance(default, Field):
                        if default.default is not MISSING:
                            default = default.default
                        elif default.default_factory is not MISSING:
                            default = default.default_factory()
                        else:
                            default = get_default_from_annotation(under_f)

                # Wraps the `setter` for the property
                val = val.setter(_wrapper(val.fset, default))

                # Set the field that does not start with an underscore
                setattr(cls, f, val)

                # Also add it to the list of class annotations to replace later
                #   (this is what `dataclasses` uses to add the field to the
                #   constructor)
                annotation_repls[under_f] = f

                # Delete the field name that starts with an underscore
                try:
                    delattr(cls, under_f)
                except AttributeError:
                    pass

    if annotation_repls:
        cls_annotations = getattr(cls, '__annotations__', None)

        if cls_annotations:
            # Use a comprehension approach because we want to replace a
            # key while preserving the insertion order, because the order
            # of fields does matter when the constructor is called.
            cls.__annotations__ = {annotation_repls.get(f, f): type_
                                   for f, type_ in cls_annotations.items()}

    return cls


def _wrapper(fset, initial_val):
    """
    Wraps the property `setter` method to check if we are passed
    in a property object itself, which will be true when no
    initial value is specified (thanks to @Martin CR).
    """

    @wraps(fset)
    def new_fset(self, value):
        if isinstance(value, property):
            value = initial_val
        fset(self, value)

    return new_fset
