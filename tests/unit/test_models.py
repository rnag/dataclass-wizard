import pytest

from dataclass_wizard.models import Alias


def test_alias_does_not_allow_both_default_and_default_factory():
    """
    Confirm we can't specify both `default` and `default_factory` when
    calling the :func:`Alias` helper function.
    """
    with pytest.raises(ValueError):
        _ = Alias('test', default=None, default_factory=None)
