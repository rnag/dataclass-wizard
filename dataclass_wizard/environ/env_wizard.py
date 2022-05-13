from __future__ import annotations

from typing import TypeVar, Type

from ..bases import AbstractEnvMeta
from ..enums import LetterCasePriority
from ..utils.type_conv import as_enum
from ..utils.type_helper import type_name
from ..utils.typing_compat import is_classvar, eval_forward_ref_if_needed
from ..bases_meta import BaseEnvWizardMeta
from ..class_helper import call_meta_initializer_if_needed, get_meta
from ..environ.loaders import EnvLoader
from ..errors import ParseError
from ..loaders import get_loader


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

    def __init_subclass__(cls: E):
        super().__init_subclass__()
        # Calls the Meta initializer when inner :class:`Meta` is sub-classed.
        call_meta_initializer_if_needed(cls)

        meta = get_meta(cls, base_cls=AbstractEnvMeta)
        cls_loader = get_loader(cls, base_cls=EnvLoader)

        get_env = as_enum(meta.key_transform, LetterCasePriority)

        # Get type annotations for attributes in the class.
        cls_dict = cls.__dict__
        missing_vars = []

        for field, ann in cls.__annotations__.items():

            ann = eval_forward_ref_if_needed(ann, cls)

            if is_classvar(ann):
                continue

            value = get_env(field)

            # if value is not None:
            #     setattr(cls, name, value)
            #
            # else:
            #     if name in cls_dict:
            #         # the default value to return, if no matching Env Var is found.
            #         default = cls_dict[name]
            #         setattr(cls, name, default)
            #     else:
            #         type_name = getattr(typ, '__qualname__', typ.__name__)
            #         # noinspection PyBroadException
            #         try:
            #             suggested = typ()
            #         except Exception:
            #             suggested = None
            #
            #         raise LookupError(f'{cls.__qualname__}: No matching Env Var for field `{name}`\n'
            #                           f'suggestion: set a default value such as below.\n'
            #                           f'  {name}: {type_name} = {suggested!r}')
            #

            if value is not None:

                # TODO extras?
                extras = {}
                parser = cls_loader.get_parser_for_annotation(ann, cls, extras)

                try:
                    parsed_val = parser(value)
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

            else:

                if field in cls_dict:
                    # the default value to return, if no matching Env Var is found.
                    default = cls_dict[field]
                    setattr(cls, field, default)
                else:
                    print(ann)
                    tn = type_name(ann)
                    # noinspection PyBroadException
                    try:
                        suggested = ann()
                    except Exception:
                        suggested = None
                    # TODO
                    missing_vars.append((field, tn, suggested))

            # print(field, ann)

        if missing_vars:
            fields = '\n'.join([f'  - {f[0]}' for f in missing_vars])
            resolutions = '\n'.join([f'  {f}: {typ} = {default!r}' for (f, typ, default) in missing_vars])

            raise ValueError(f'Following required fields in class `{cls.__qualname__}` are missing in the Environment:\n{fields}\n{resolutions}')
