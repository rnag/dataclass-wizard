from collections import namedtuple
from typing import NamedTuple

from dataclass_wizard import DataclassWizard
from dataclass_wizard.v1 import EnvWizard

from ..._typing import Required, NotRequired, ReadOnly, TypedDict


class TN(NamedTuple):
    a: int
    b: int = 2


CN = namedtuple("CN", "a b", defaults=(2,))


class ContDict(DataclassWizard):
    class _(DataclassWizard.Meta):
        v1_namedtuple_as_dict = True

    tn: TN
    cn: CN

class ContList(DataclassWizard):
    class _(DataclassWizard.Meta):
        v1_namedtuple_as_dict = False

    tn: TN
    cn: CN


class EnvContDict(EnvWizard):
    class _(EnvWizard.Meta):
        v1_namedtuple_as_dict = True

    tn: TN
    cn: CN


class EnvContList(EnvWizard):
    class _(EnvWizard.Meta):
        v1_namedtuple_as_dict = False

    tn: TN
    cn: CN


# 1) total=False + Required/NotRequired/ReadOnly, E2E
class TD_TF(TypedDict, total=False):
    a: Required[int]          # required even though total=False
    b: NotRequired[int]       # optional
    ro: ReadOnly[int]         # optional because total=False


class ContTF(DataclassWizard):
    td: TD_TF


class EnvContTF(EnvWizard):
    td: TD_TF


# 2) total=True + NotRequired + ReadOnly requiredness, E2E
class TD_TT(TypedDict):
    a: int                    # required
    b: NotRequired[int]       # optional
    ro: ReadOnly[int]         # required (unless NotRequired wraps it)


class ContTT(DataclassWizard):
    td: TD_TT


class EnvContTT(EnvWizard):
    td: TD_TT


# 3) all-required TypedDict (no optional keys) => codegen inline path, E2E
class TD_AllReq(TypedDict):
    x: int
    y: str


class ContAllReq(DataclassWizard):
    td: TD_AllReq


class EnvContAllReq(EnvWizard):
    td: TD_AllReq
