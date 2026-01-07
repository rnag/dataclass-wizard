"""
Common test fixtures and utilities.
"""
from dataclasses import dataclass
from uuid import UUID

import pytest


# Ref: https://docs.pytest.org/en/6.2.x/example/parametrize.html#parametrizing-conditional-raising
from contextlib import nullcontext as does_not_raise


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


@pytest.fixture
def mock_log(caplog):
    caplog.set_level('INFO', logger='dataclass_wizard')
    return caplog

@pytest.fixture
def mock_debug_log(caplog):
    caplog.set_level('DEBUG', logger='dataclass_wizard')
    return caplog
