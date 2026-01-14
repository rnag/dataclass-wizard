"""
Internal typing shims (runtime-light).
"""
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from ._abstractions import (
        AbstractEnvWizard,
        AbstractJSONWizard,
        AbstractLoaderGenerator,
        AbstractDumperGenerator,
    )

else:
    # noinspection PyTypeChecker
    AbstractEnvWizard = object
    # noinspection PyTypeChecker
    AbstractJSONWizard = object
    # noinspection PyTypeChecker
    AbstractLoaderGenerator = object
    # noinspection PyTypeChecker
    AbstractDumperGenerator = object
