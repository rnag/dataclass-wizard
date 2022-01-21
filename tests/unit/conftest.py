"""
Common test fixtures and utilities.
"""
from dataclasses import dataclass
from uuid import UUID

from ..conftest import PY36


@dataclass
class SampleClass:
    """Sample dataclass model for various test scenarios."""
    f1: str
    f2: int


if PY36:
    # Ignore these files, because Python 3.6 doesn't define the `__future__`
    # import used, so we'll run into an error if we import these modules.
    #
    # Ref: https://docs.pytest.org/en/6.2.x/example/pythoncollection.html#customizing-test-collection
    collect_ignore = ['test_load_with_future_import.py',
                      'test_property_wizard_with_future_import.py']


class MyUUIDSubclass(UUID):
    """
    Simple UUID subclass that calls :meth:`hex` when ``str()`` is invoked.
    """

    def __str__(self):
        return self.hex
