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
from dacite import from_dict as dacite_from_dict
from pydantic import BaseModel
import mashumaro

from dataclass_wizard import JSONWizard, LoadMeta
from dataclass_wizard.class_helper import create_new_class
from dataclass_wizard.constants import PY314_OR_ABOVE
from dataclass_wizard.utils.string_conv import to_snake_case
from dataclass_wizard.utils.type_conv import as_datetime, as_date


log = logging.getLogger(__name__)

# Dataclass Definitions (Same as before, no changes needed)
@dataclass
class Data1:
    instance: 'Instance'
    result: 'Result'


@dataclass
class Instance:
    name: str
    data: 'Data2'


@dataclass
class Data2:
    date: date
    owner: str


@dataclass
class Result:
    status: str
    iteration_results: 'IterationResults'


@dataclass
class IterationResults:
    iterations: List['Iteration']


@dataclass
class Iteration:
    name: str
    data: 'Data3'


@dataclass
class Data3:
    question1: str
    question2: str


# New Model Class Definitions for Libraries

class MyClassPydantic(BaseModel):
    instance: 'InstancePydantic'
    result: 'ResultPydantic'


class InstancePydantic(BaseModel):
    name: str
    data: 'Data2Pydantic'


class Data2Pydantic(BaseModel):
    date: date
    owner: str


class ResultPydantic(BaseModel):
    status: str
    iteration_results: 'IterationResultsPydantic'


@dataclass
class IterationResultsPydantic:
    iterations: List['IterationPydantic']


class IterationPydantic(BaseModel):
    name: str
    data: 'Data3Pydantic'


class Data3Pydantic(BaseModel):
    question1: str
    question2: str


@dataclass
class MyClassMashumaro(mashumaro.DataClassDictMixin):
    instance: 'InstanceMashumaro'
    result: 'Result'


@dataclass
class InstanceMashumaro:
    name: str
    data: 'Data2Mashumaro'


@dataclass
class Data2Mashumaro:
    date: date
    owner: str


# Corrected Definition for `MyClassDJ`
@dataclass
class MyClassDJ(DataClassJsonMixin):
    instance: 'InstanceDJ'
    result: 'Result'


class InstanceDJ:
    name: str
    data: 'Data2DJ'


class Data2DJ:
    date: date
    owner: str


# Model for `dataclass-wizard`
WizType = TypeVar('WizType', Data1, JSONWizard)
# Model for `jsons`
JsonsType = TypeVar('JsonsType', Data1, JsonSerializable)
# Model for `dataclasses-json`
DJType = TypeVar('DJType', Data1, DataClassJsonMixin)
# Model for `mashumaro`
MashumaroType = TypeVar('MashumaroType', Data1, mashumaro.DataClassDictMixin)
# Factory for `dataclass-factory`
factory = dataclass_factory.Factory()

MyClassWizard: WizType = create_new_class(
    Data1, (Data1, JSONWizard), 'Wizard',
    attr_dict=vars(Data1).copy())
MyClassJsons: JsonsType = create_new_class(
    Data1, (Data1, JsonSerializable), 'Jsons',
    attr_dict=vars(Data1).copy())
MyClassMashumaroModel: MashumaroType = create_new_class(
    Data1, (Data1, mashumaro.DataClassDictMixin), 'Mashumaro',
    attr_dict=vars(Data1).copy())

# Pydantic Model for Benchmarking
MyClassPydanticModel = MyClassPydantic

# Mashumaro Model for Benchmarking
# MyClassMashumaroModel = MyClassMashumaro


# Enable experimental `v1` mode for optimized de/serialization
LoadMeta(v1=True).bind_to(MyClassWizard)


@pytest.fixture(scope='session')
def data():
    return {
        "instance": {
            "name": "example1",
            "data": {
                "date": "2021-01-01",
                "owner": "Maciek"
            }
        },
        "result": {
            "status": "complete",
            "iteration_results": {
                "iterations": [
                    {
                        "name": "first",
                        "data": {
                            "question1": "yes",
                            "question2": "no"
                        }
                    }
                ]
            }
        }
    }


dt_iso_format_schema = dataclass_factory.Schema(
    parser=as_datetime,
    serializer=datetime.isoformat
)

date_iso_format_schema = dataclass_factory.Schema(
    parser=as_date,
    serializer=date.isoformat
)

factory.schemas = {
    datetime: dt_iso_format_schema,
    date: date_iso_format_schema
}


def test_load(request, data, n):
    """
    [ RESULTS]
    platform darwin -- Python 3.13.11, pytest-8.3.4, pluggy-1.6.0

    benchmarks.nested.nested - [INFO] dataclass-wizard     0.128877
    benchmarks.nested.nested - [INFO] dataclass-factory    0.405885
    benchmarks.nested.nested - [INFO] dataclasses-json     11.878780
    benchmarks.nested.nested - [INFO] mashumaro            0.154879
    benchmarks.nested.nested - [INFO] pydantic             0.286836
    benchmarks.nested.nested - [INFO] jsons                24.753070
    benchmarks.nested.nested - [INFO] jsons (strict)       26.192690

    """
    g = globals().copy()
    g.update(locals())

    MyClassWizard.from_dict(data)

    log.info('dataclass-wizard     %f',
             timeit('MyClassWizard.from_dict(data)', globals=g, number=n))

    if not PY314_OR_ABOVE:  # breaks on Python 3.14+
        log.info('dataclass-factory    %f',
                 timeit('factory.load(data, Data1)', globals=g, number=n))

    log.info('dataclasses-json     %f',
             timeit('MyClassDJ.from_dict(data)', globals=g, number=n))

    # JUST SKKIPING IN INTERESTS OF TIME
    # log.info('dacite               %f',
    #          timeit('dacite_from_dict(MyClass, data)', globals=g, number=n))

    log.info('mashumaro            %f',
             timeit('MyClassMashumaro.from_dict(data)', globals=g, number=n))

    log.info('pydantic             %f',
             timeit('MyClassPydantic(**data)', globals=g, number=n))

    if not request.config.getoption("--all"):
        pytest.skip("Skipping benchmarks for the rest by default, unless --all is specified.")

    log.info('jsons                %f',
             timeit('MyClassJsons.load(data)', globals=g, number=n))

    log.info('jsons (strict)       %f',
             timeit('MyClassJsons.load(data, strict=True)', globals=g, number=n))

    c1 = MyClassWizard.from_dict(data)
    if not PY314_OR_ABOVE:  # breaks on Python 3.14+
        c2 = factory.load(data, Data1)
    c3 = MyClassDJ.from_dict(data)
    c4 = MyClassJsons.load(data)
    c5 = MyClassMashumaro.from_dict(data)
    # c6 = dacite_from_dict(MyClass, data)
    c7 = MyClassPydantic(**data)

    assert c1.__dict__ == c3.__dict__ == c4.__dict__ == c5.__dict__ == c7.__dict__ # == c6.__dict__

    if not PY314_OR_ABOVE:  # breaks on Python 3.14+
        assert c1.__dict__ == c2.__dict__


def test_dump(request, data, n):
    """
    [ RESULTS]
    platform darwin -- Python 3.13.11, pytest-8.3.4, pluggy-1.6.0

    benchmarks.nested.nested - [INFO] dataclass-wizard     0.097571
    benchmarks.nested.nested - [INFO] asdict (dataclasses) 0.617322
    benchmarks.nested.nested - [INFO] dataclass-factory    0.214060
    benchmarks.nested.nested - [INFO] dataclasses-json     5.193261
    benchmarks.nested.nested - [INFO] mashumaro            0.077272
    benchmarks.nested.nested - [INFO] pydantic             0.177479
    benchmarks.nested.nested - [INFO] jsons                40.467886
    benchmarks.nested.nested - [INFO] jsons (strict)       36.541698
    """
    c1 = MyClassWizard.from_dict(data)
    if not PY314_OR_ABOVE:  # breaks on Python 3.14+
        c2 = factory.load(data, Data1)
    c3 = MyClassDJ.from_dict(data)
    c4 = MyClassJsons.load(data)
    c5 = MyClassMashumaro.from_dict(data)
    c6 = MyClassPydantic(**data)

    g = globals().copy()
    g.update(locals())

    log.info('dataclass-wizard     %f',
             timeit('c1.to_dict()', globals=g, number=n))

    log.info('asdict (dataclasses) %f',
             timeit('asdict(c1)', globals=g, number=n))

    if not PY314_OR_ABOVE:  # breaks on Python 3.14+
        log.info('dataclass-factory    %f',
                 timeit('factory.dump(c2, Data1)', globals=g, number=n))

    log.info('dataclasses-json     %f',
             timeit('c3.to_dict()', globals=g, number=n))

    log.info('mashumaro            %f',
             timeit('c5.to_dict()', globals=g, number=n))

    log.info('pydantic             %f',
             timeit('c6.model_dump()', globals=g, number=n))

    if not request.config.getoption("--all"):
        pytest.skip("Skipping benchmarks for the rest by default, unless --all is specified.")

    log.info('jsons                %f',
             timeit('c4.dump()', globals=g, number=n))

    log.info('jsons (strict)       %f',
             timeit('c4.dump(strict=True)', globals=g, number=n))

    # Assert the dict objects which are the result of `to_dict` are all equal.
    c1_dict = {to_snake_case(f): fval for f, fval in c1.to_dict().items()}

    # assert c1_dict == factory.dump(c2, Data1) == c3.to_dict() == c4.dump() == c5.to_dict()
