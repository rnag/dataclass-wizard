"""
Common test fixtures and utilities.
"""

from pathlib import Path
from uuid import UUID


class MyUUIDSubclass(UUID):
    """
    Simple UUID subclass that calls :meth:`hex` when ``str()`` is invoked.
    """

    def __str__(self):
        return self.hex
