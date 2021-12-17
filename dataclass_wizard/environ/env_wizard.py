import os
from typing import ClassVar, _GenericAlias, TypeVar, Type

from ..bases_meta import BaseEnvWizardMeta
from ..class_helper import call_meta_initializer_if_needed
from ..environ.loaders import EnvLoader
from ..errors import ParseError
from ..loaders import get_loader


def is_classvar(a_type):
    # This test uses a typing internal class, but it's the best way to
    # test if this is a ClassVar.
    # noinspection PyProtectedMember
    return (a_type is ClassVar
            or (type(a_type) is _GenericAlias
                and a_type.__origin__ is ClassVar))


E = TypeVar('E', bound='EnvWizard')
E = Type[E]


class EnvWizard:

    __slots__ = ()

    class Meta(BaseEnvWizardMeta):
        """
        Inner meta class that can be extended by sub-classes for additional
        customization with the environment load process.
        """
        __slots__ = ()

        # Class attribute to enable detection of the class type.
        __is_inner_meta__ = True

        def __init_subclass__(cls):
            # Set the `__init_subclass__` method here, so we can ensure it
            # doesn't run for the `EnvWizard.Meta` class.
            return cls._init_subclass()

    def __init_subclass__(cls: E, my_kwarg='test', **kwargs):
        super().__init_subclass__(**kwargs)
        # Calls the Meta initializer when inner :class:`Meta` is sub-classed.
        call_meta_initializer_if_needed(cls)

        cls_loader = get_loader(cls, base_cls=EnvLoader)

        # Get type annotations for attributes in the class.
        cls_annotations = getattr(cls, '__annotations__', None)
        cls_dict = getattr(cls, '__dict__')
        if cls_annotations is None:
            return

        missing_vars = []

        for field, ann in cls_annotations.items():
            if is_classvar(ann):
                continue

            if field in os.environ:
                env_val = os.environ[field]

                # TODO extras?
                extras = {}
                parser = cls_loader.get_parser_for_annotation(ann, cls, extras)

                try:
                    parsed_val = parser(env_val)
                except ParseError as e:
                    # We run into a parsing error while loading the field
                    # value; Add additional info on the Exception object
                    # before re-raising it.
                    e.class_name = cls
                    e.field_name = field
                    # TODO
                    e.kwargs['env_variable'] = field
                    raise
                else:
                    setattr(cls, field, parsed_val)

            elif field not in cls_dict:
                # TODO
                missing_vars.append(field)

            # print(field, ann)

        if missing_vars:
            fields = '\n'.join([f'  - {f}' for f in missing_vars])
            raise ValueError(f'Following required fields in class `{cls.__qualname__}` are missing in the Environment:\n{fields}')
