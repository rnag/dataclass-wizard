from logging import DEBUG, StreamHandler

from dataclass_wizard import DataclassWizard
from dataclass_wizard.class_helper import get_meta


def test_dataclass_wizard_with_debug(restore_logger, mock_debug_log):
    """Subclass `DataclassWizard` with `debug=True`."""
    logger = restore_logger

    class _(DataclassWizard, debug=True):
        ...

    assert get_meta(_).v1_debug == DEBUG

    assert logger.level == DEBUG
    assert logger.propagate is False
    assert any(isinstance(h, StreamHandler) for h in logger.handlers)
    # optional: ensure it didn't add duplicates
    assert sum(isinstance(h, StreamHandler) for h in logger.handlers) == 1
