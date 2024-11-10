"""
Common test fixtures and utilities.
"""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class SampleClass:
    """Sample dataclass model for various test scenarios."""
    f1: str
    f2: int


class MyUUIDSubclass(UUID):
    """
    Simple UUID subclass that calls :meth:`hex` when ``str()`` is invoked.
    """

    def __str__(self):
        return self.hex
