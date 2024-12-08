import logging
from dataclasses import dataclass, asdict
from timeit import timeit
from typing import Optional, TypeVar

import dataclass_factory
import pytest
from dataclasses_json import DataClassJsonMixin
from jsons import JsonSerializable
from dacite import from_dict as dacite_from_dict
from pydantic import BaseModel
import marshmallow
import attr
import mashumaro

from dataclass_wizard import JSONWizard, LoadMeta
from dataclass_wizard.class_helper import create_new_class
from dataclass_wizard.utils.string_conv import to_snake_case

log = logging.getLogger(__name__)

# Dataclass for the test
@dataclass
class MyClass:
    my_str: str
    my_int: int
    my_bool: Optional[bool]

# Add Pydantic Model
class MyClassPydantic(BaseModel):
    my_str: str
    my_int: int
    my_bool: Optional[bool]

# Marshmallow Schema
class MyClassSchema(marshmallow.Schema):
    my_str = marshmallow.fields.Str()
    my_int = marshmallow.fields.Int()
    my_bool = marshmallow.fields.Bool()

# attrs Class
@attr.s
class MyClassAttrs:
    my_str = attr.ib(type=str)
    my_int = attr.ib(type=int)
    my_bool = attr.ib(type=Optional[bool])

# Mashumaro Model
@dataclass
class MyClassMashumaro(mashumaro.DataClassDictMixin):
    my_str: str
    my_int: int
    my_bool: Optional[bool]

# Model for `dataclass-wizard`
WizType = TypeVar("WizType", MyClass, JSONWizard)
# Model for `jsons`
JsonsType = TypeVar("JsonsType", MyClass, JsonSerializable)
# Model for `dataclasses-json`
DJType = TypeVar("DJType", MyClass, DataClassJsonMixin)
# Factory for `dataclass-factory`
factory = dataclass_factory.Factory()

MyClassWizard: WizType = create_new_class(MyClass, (MyClass, JSONWizard), "Wizard")
MyClassDJ: DJType = create_new_class(MyClass, (MyClass, DataClassJsonMixin), "DJ")
MyClassJsons: JsonsType = create_new_class(MyClass, (MyClass, JsonSerializable), "Jsons")

# Enable experimental `v1` mode for optimized de/serialization
LoadMeta(v1=True).bind_to(MyClassWizard)


@pytest.fixture(scope="session")
def data():
    return {
        "my_str": "hello world!",
        "my_int": 21,
        "my_bool": True,
    }

def test_load(data, n):
    """
    [ RESULTS ON MAC OS X ]

    benchmarks.simple.simple - [INFO] dataclass-wizard     0.033917
    benchmarks.simple.simple - [INFO] dataclass-factory    0.103837
    benchmarks.simple.simple - [INFO] dataclasses-json     3.941902
    benchmarks.simple.simple - [INFO] jsons                5.636863
    benchmarks.simple.simple - [INFO] dacite               0.572661
    benchmarks.simple.simple - [INFO] pydantic             0.081108
    benchmarks.simple.simple - [INFO] marshmallow          2.550217
    benchmarks.simple.simple - [INFO] attrs                0.022822
    benchmarks.simple.simple - [INFO] mashumaro            0.046641
    """
    g = globals().copy()
    g.update(locals())

    # Add dacite and pydantic benchmarks
    log.info("dataclass-wizard     %f",
             timeit("MyClassWizard.from_dict(data)", globals=g, number=n))
    log.info("dataclass-factory    %f",
             timeit("factory.load(data, MyClass)", globals=g, number=n))
    log.info("dataclasses-json     %f",
             timeit("MyClassDJ.from_dict(data)", globals=g, number=n))
    log.info("jsons                %f",
             timeit("MyClassJsons.load(data)", globals=g, number=n))
    log.info("dacite               %f",
             timeit("dacite_from_dict(MyClass, data)", globals=g, number=n))
    log.info("pydantic             %f",
             timeit("MyClassPydantic(**data)", globals=g, number=n))
    log.info("marshmallow          %f",
             timeit("MyClassSchema().load(data)", globals=g, number=n))
    log.info("attrs                %f",
             timeit("MyClassAttrs(**data)", globals=g, number=n))
    log.info("mashumaro            %f",
             timeit("MyClassMashumaro.from_dict(data)", globals=g, number=n))

    # Assert the dataclass instances have the same values for all fields.
    c1 = MyClassWizard.from_dict(data)
    c2 = factory.load(data, MyClass)
    c3 = MyClassDJ.from_dict(data)
    c4 = MyClassJsons.load(data)
    c5 = dacite_from_dict(MyClass, data)
    c6 = MyClassPydantic(**data)
    c7 = MyClassSchema().load(data)
    c8 = MyClassAttrs(**data)
    c9 = MyClassMashumaro.from_dict(data)

    assert c1.__dict__ == c2.__dict__ == c3.__dict__ == c4.__dict__ == c5.__dict__ == c6.model_dump() == c7 == c8.__dict__ == c9.to_dict()

def test_dump(data, n):
    """
    [ RESULTS ON MAC OS X ]

    benchmarks.simple.simple - [INFO] dataclass-wizard     0.072549
    benchmarks.simple.simple - [INFO] asdict (dataclasses) 0.101621
    benchmarks.simple.simple - [INFO] dataclass-factory    0.087357
    benchmarks.simple.simple - [INFO] dataclasses-json     1.488334
    benchmarks.simple.simple - [INFO] jsons                8.550752
    benchmarks.simple.simple - [INFO] dacite (not applicable) -- skipped
    benchmarks.simple.simple - [INFO] pydantic             0.080157
    benchmarks.simple.simple - [INFO] marshmallow          0.000578
    benchmarks.simple.simple - [INFO] attrs                0.146561
    benchmarks.simple.simple - [INFO] mashumaro            0.010199
    """

    # [ RESULTS ]
    # benchmarks.simple.simple - [INFO] dataclass-wizard     0.065604
    # benchmarks.simple.simple - [INFO] asdict (dataclasses) 0.087785
    # benchmarks.simple.simple - [INFO] dataclass-factory    0.084215
    # benchmarks.simple.simple - [INFO] dataclasses-json     1.278573
    # benchmarks.simple.simple - [INFO] jsons                6.192119
    # benchmarks.simple.simple - [INFO] dacite (not applicable) -- skipped
    # benchmarks.simple.simple - [INFO] pydantic             0.066679
    # benchmarks.simple.simple - [INFO] marshmallow          0.000481
    # benchmarks.simple.simple - [INFO] attrs                0.122282
    # benchmarks.simple.simple - [INFO] mashumaro            0.009025

    c1 = MyClassWizard.from_dict(data)
    c2 = factory.load(data, MyClass)
    c3 = MyClassDJ.from_dict(data)
    c4 = MyClassJsons.load(data)
    c5 = dacite_from_dict(MyClass, data)
    c6 = MyClassPydantic(**data)
    c7 = MyClassSchema().load(data)
    c8 = MyClassAttrs(**data)
    c9 = MyClassMashumaro.from_dict(data)

    g = globals().copy()
    g.update(locals())

    log.info("dataclass-wizard     %f",
             timeit("c1.to_dict()", globals=g, number=n))
    log.info("asdict (dataclasses) %f",
             timeit("asdict(c1)", globals=g, number=n))
    log.info("dataclass-factory    %f",
             timeit("factory.dump(c2, MyClass)", globals=g, number=n))
    log.info("dataclasses-json     %f",
             timeit("c3.to_dict()", globals=g, number=n))
    log.info("jsons                %f",
             timeit("c4.dump()", globals=g, number=n))
    log.info("dacite (not applicable) -- skipped")
    log.info("pydantic             %f",
             timeit("c6.model_dump()", globals=g, number=n))
    log.info("marshmallow          %f",
             timeit("c7", globals=g, number=n))
    log.info("attrs                %f",
             timeit("attr.asdict(c8)", globals=g, number=n))
    log.info("mashumaro            %f",
             timeit("c9.to_dict()", globals=g, number=n))

    # Assert the dict objects which are the result of `to_dict` are all equal.
    c1_dict = {to_snake_case(f): fval for f, fval in c1.to_dict().items()}

    assert c1_dict == factory.dump(c2, MyClass) == c3.to_dict() == c4.dump() == c6.model_dump() == attr.asdict(c8) == c9.to_dict()
