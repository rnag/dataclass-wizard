from typing import ClassVar, Generic, Union, List, Tuple, Dict, Callable

import pytest

from dataclass_wizard.type_def import T
from dataclass_wizard.utils.typing_compat import get_origin, get_args
from ...conftest import *


@pytest.mark.parametrize(
    'tp,expected',
    [
        (Literal[42], Literal),
        (int, int),
        (ClassVar[int], ClassVar),
        (Generic, Generic),
        (Generic[T], Generic),
        (Union[T, int], Union),
        (List[Tuple[T, T]][int], list),
    ]
)
def test_get_origin(tp, expected):
    actual = get_origin(tp)
    assert actual is expected


@pytest.mark.parametrize(
    'tp,expected',
    [
        (Dict[str, int], (str, int)),
        (int, ()),
        (Callable[[], T][int], ([], int)),
        # The following cases are an `xfail` on Python 3.6
        pytest.param(
            Union[int, Union[T, int], str][int], (int, str),
                     marks=pytest.mark.skipif(
                         PY36, reason='requires python 3.7 or higher')),
        pytest.param(
            Union[int, Tuple[T, int]][str], (int, Tuple[str, int]),
            marks=pytest.mark.skipif(
                PY36, reason='requires python 3.7 or higher')),
    ]
)
def test_get_args(tp, expected):
    actual = get_args(tp)
    assert actual == expected
