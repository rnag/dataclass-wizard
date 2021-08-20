import logging
from dataclasses import dataclass
from timeit import timeit
from typing import Optional, TypeVar

import dataclass_factory
import pytest
from dataclasses_json import DataClassJsonMixin
from jsons import JsonSerializable

from dataclass_wizard import JSONWizard
from dataclass_wizard.class_helper import create_new_class
from dataclass_wizard.utils.string_conv import to_snake_case

log = logging.getLogger(__name__)


@dataclass
class MyClass:
    my_str: str
    my_int: int
    my_bool: Optional[bool]


# Model for `dataclass-wizard`
WizType = TypeVar('WizType', MyClass, JSONWizard)
# Model for `jsons`
JsonsType = TypeVar('JsonsType', MyClass, JsonSerializable)
# Model for `dataclasses-json`
DJType = TypeVar('DJType', MyClass, DataClassJsonMixin)
# Factory for `dataclass-factory`
factory = dataclass_factory.Factory()

MyClassWizard: WizType = create_new_class(
    MyClass, (MyClass, JSONWizard), 'Wizard')
MyClassDJ: DJType = create_new_class(
    MyClass, (MyClass, DataClassJsonMixin), 'DJ')
MyClassJsons: JsonsType = create_new_class(
    MyClass, (MyClass, JsonSerializable), 'Jsons')


@pytest.fixture(scope='session')
def data():
    return {
        'my_str': 'hello world!',
        'my_int': 21,
        'my_bool': True
    }


def test_load(data, n):
    g = globals().copy()
    g.update(locals())

    # Result: 0.491
    log.info('dataclass-wizard     %f',
             timeit('MyClassWizard.from_dict(data)', globals=g, number=n))

    # Result: 0.454
    log.info('dataclass-factory    %f',
             timeit('factory.load(data, MyClass)', globals=g, number=n))

    # Result: 6.965
    log.info('dataclasses-json     %f',
             timeit('MyClassDJ.from_dict(data)', globals=g, number=n))

    # Result: 13.525
    log.info('jsons                %f',
             timeit('MyClassJsons.load(data)', globals=g, number=n))

    # Result: 17.678
    log.info('jsons (strict)       %f',
             timeit('MyClassJsons.load(data, strict=True)', globals=g, number=n))

    # Assert the dataclass instances have the same values for all fields.

    c1 = MyClassWizard.from_dict(data)
    c2 = factory.load(data, MyClass)
    c3 = MyClassDJ.from_dict(data)
    c4 = MyClassJsons.load(data)

    assert c1.__dict__ == c2.__dict__ == c3.__dict__ == c4.__dict__


def test_dump(data, n):
    c1 = MyClassWizard.from_dict(data)
    c2 = factory.load(data, MyClass)
    c3 = MyClassDJ.from_dict(data)
    c4 = MyClassJsons.load(data)

    g = globals().copy()
    g.update(locals())

    # Result: 0.696
    log.info('dataclass-wizard     %f',
             timeit('c1.to_dict()', globals=g, number=n))

    # Result: 0.751
    log.info('dataclass-factory    %f',
             timeit('factory.dump(c2, MyClass)', globals=g, number=n))

    # Result: 2.154
    log.info('dataclasses-json     %f',
             timeit('c3.to_dict()', globals=g, number=n))

    # Result: 15.130
    log.info('jsons                %f',
             timeit('c4.dump()', globals=g, number=n))

    # Result: 14.657
    log.info('jsons (strict)       %f',
             timeit('c4.dump(strict=True)', globals=g, number=n))

    # Assert the dict objects which are the result of `to_dict` are all equal.

    # Need this step because our lib converts field names to camel-case
    # by default.
    c1_dict = {to_snake_case(f): fval for f, fval in c1.to_dict().items()}

    assert c1_dict == factory.dump(c2, MyClass) == c3.to_dict() == c4.dump()
