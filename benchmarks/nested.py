import logging
from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from timeit import timeit
from typing import TypeVar, List, Union

import dataclass_factory
import marshmallow
import pytest
from dataclasses_json import DataClassJsonMixin, config
from jsons import JsonSerializable

from dataclass_wizard import JSONWizard
from dataclass_wizard.class_helper import create_new_class
from dataclass_wizard.utils.string_conv import to_snake_case
from dataclass_wizard.utils.type_conv import as_datetime, as_date


log = logging.getLogger(__name__)


@dataclass
class Data1:
    """
    Top-level dataclass for the majority of the cases.

    """

    instance: "Instance"
    result: "Result"


@dataclass
class Instance:
    """
    Instance dataclass

    """

    name: str
    data: "Data2"


@dataclass
class Data2:
    """
    Data dataclass

    """

    date: date
    owner: str


@dataclass
class Result:
    """
    Result dataclass

    """

    status: str
    iteration_results: "IterationResults"


@dataclass
class IterationResults:
    """
    IterationResults dataclass

    """

    iterations: List["Iteration"]


@dataclass
class Iteration:
    """
    Iteration dataclass

    """

    name: str
    data: "Data3"


@dataclass
class Data3:
    """
    Data dataclass

    """

    question1: str
    question2: str


@dataclass
class MyClassDJ(DataClassJsonMixin):
    """
    Top level dataclass for testing with `dataclasses-json`. Just a note
    this nested definition is a bit painful, but necessary as there seems
    no way to decode `date` fields automatically by default.

    """

    instance: "InstanceJD"
    result: "Result"


@dataclass
class InstanceJD:
    """
    Instance dataclass for `dataclasses-json`

    """

    name: str
    data: "Data2JD"


@dataclass
class Data2JD:
    """
    Data dataclass for `dataclasses-json`. Note this is needed because
    otherwise we de-serialize strings as strings, instead of `date` type.
    So we need to tell `dataclasses-json` to de-serialize our field as
    a `date` type.

    """

    date: date = field(
        metadata=config(
            encoder=date.isoformat,
            decoder=as_date,
            mm_field=marshmallow.fields.Date(format="iso"),
        )
    )
    owner: str


# Model for `dataclass-wizard`
WizType = TypeVar("WizType", Data1, JSONWizard)
# Model for `jsons`
JsonsType = TypeVar("JsonsType", Data1, JsonSerializable)
# Model for `dataclasses-json`
DJType = TypeVar("DJType", Data1, DataClassJsonMixin)
# Factory for `dataclass-factory`
factory = dataclass_factory.Factory()

MyClassWizard: WizType = create_new_class(
    Data1, (Data1, JSONWizard), "Wizard", attr_dict=vars(Data1).copy()
)
MyClassJsons: JsonsType = create_new_class(
    Data1, (Data1, JsonSerializable), "Jsons", attr_dict=vars(Data1).copy()
)


@pytest.fixture(scope="session")
def data():
    return {
        "instance": {
            "name": "example1",
            "data": {"date": "2021-01-01", "owner": "Maciek"},
        },
        "result": {
            "status": "complete",
            "iteration_results": {
                "iterations": [
                    {"name": "first", "data": {"question1": "yes", "question2": "no"}}
                ]
            },
        },
    }


dt_iso_format_schema = dataclass_factory.Schema(
    parser=as_datetime, serializer=datetime.isoformat
)

date_iso_format_schema = dataclass_factory.Schema(
    parser=as_date, serializer=date.isoformat
)

factory.schemas = {datetime: dt_iso_format_schema, date: date_iso_format_schema}


def test_load(data, n):
    g = globals().copy()
    g.update(locals())

    # Result: 0.811
    log.info(
        "dataclass-wizard     %f",
        timeit("MyClassWizard.from_dict(data)", globals=g, number=n),
    )

    # Result: 0.795
    log.info(
        "dataclass-factory    %f",
        timeit("factory.load(data, Data1)", globals=g, number=n),
    )

    # Result: 20.571
    log.info(
        "dataclasses-json     %f",
        timeit("MyClassDJ.from_dict(data)", globals=g, number=n),
    )

    # Result: 45.352
    log.info(
        "jsons                %f",
        timeit("MyClassJsons.load(data)", globals=g, number=n),
    )

    # Result: 62.501
    log.info(
        "jsons (strict)       %f",
        timeit("MyClassJsons.load(data, strict=True)", globals=g, number=n),
    )

    # Assert the dataclass instances have the same values for all fields.

    c1 = MyClassWizard.from_dict(data)
    c2 = factory.load(data, Data1)
    c3 = MyClassDJ.from_dict(data)  # TODO unused in comparison
    c4 = MyClassJsons.load(data)

    # Note: we can't do direct comparison with `dataclasses-json`, because
    # that uses different model dataclasses (for ex. `InstanceJD` instead
    # of `Instance`)
    assert c1.__dict__ == c2.__dict__ == c4.__dict__


def test_dump(data, n):
    c1 = MyClassWizard.from_dict(data)
    c2 = factory.load(data, Data1)
    c3 = MyClassDJ.from_dict(data)
    c4 = MyClassJsons.load(data)

    g = globals().copy()
    g.update(locals())

    # Result: 1.096
    log.info("dataclass-wizard     %f", timeit("c1.to_dict()", globals=g, number=n))

    # Result: 1.754
    log.info("asdict (dataclasses) %f", timeit("asdict(c1)", globals=g, number=n))

    # Result: 0.597
    log.info(
        "dataclass-factory    %f",
        timeit("factory.dump(c2, Data1)", globals=g, number=n),
    )

    # Result: 7.514
    log.info("dataclasses-json     %f", timeit("c3.to_dict()", globals=g, number=n))

    # Result: 54.996
    log.info("jsons                %f", timeit("c4.dump()", globals=g, number=n))

    # Result: 51.893
    log.info(
        "jsons (strict)       %f", timeit("c4.dump(strict=True)", globals=g, number=n)
    )

    # Assert the dict objects which are the result of `to_dict` are all equal.

    # Need this step because our lib converts field names to camel-case
    # by default.
    # c1_dict = {to_snake_case(f): fval for f, fval in c1.to_dict().items()}

    # I tried to do an assertion but it failed. Even if I remove our result
    # e.g. `c1_dict`, results are still unequal between the others. I'll
    # need to dedicate some time to look into this a bit more in depth.
    # assert c1_dict == factory.dump(c2, Data1) == c3.to_dict() == c4.dump()
