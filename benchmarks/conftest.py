import pytest


@pytest.fixture(scope="session")
def n():
    return 100_000
