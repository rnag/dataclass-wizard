import pytest
from pytest_mock import MockerFixture

from dataclass_wizard.utils.lazy_loader import LazyLoader


@pytest.fixture
def mock_logging(mocker: MockerFixture):
    return mocker.patch('dataclass_wizard.utils.lazy_loader.logging')


def test_lazy_loader_when_module_not_found():
    extra_name = 'my-extra'

    mod = LazyLoader(globals(), 'my_module', extra_name)

    with pytest.raises(ImportError) as e:
        _ = mod.my_var

    assert 'pip install' in e.value.msg
    assert extra_name in e.value.msg


def test_lazy_loader_with_warning(mock_logging):
    warning_msg = 'My test warning'

    mod = LazyLoader(globals(), 'pytimeparse', warning=warning_msg)

    _ = mod.parse

    # Assert a warning is logged
    mock_logging.warning.assert_called_once_with(warning_msg)

    # Add for code coverage
    _ = dir(mod)
