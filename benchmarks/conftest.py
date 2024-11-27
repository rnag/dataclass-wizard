import pytest


@pytest.fixture(scope='session')
def n():
    return 100_000


def pytest_addoption(parser):
    parser.addoption(
        "--all",  # long option
        "-A",
        action="store_true",
        default=False,
        help="Run benchmarks for *all* libraries, including *slower* ones like `jsons`",
    )
