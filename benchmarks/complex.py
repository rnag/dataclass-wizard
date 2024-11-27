import logging
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from timeit import timeit
from typing import Optional, TypeVar, Dict, Any, List, Union, NamedTuple, Tuple

import dataclass_factory
import marshmallow
import pytest
from dataclasses_json import DataClassJsonMixin, config
from jsons import JsonSerializable
from dacite import from_dict as dacite_from_dict
from pydantic import BaseModel
import attr
import mashumaro

from dataclass_wizard import JSONWizard
from dataclass_wizard.class_helper import create_new_class
from dataclass_wizard.utils.string_conv import to_snake_case
from dataclass_wizard.utils.type_conv import as_datetime


log = logging.getLogger(__name__)

@dataclass
class MyClass:
    my_ledger: Dict[str, Any]
    the_answer_to_life: Optional[int]
    people: List['Person']
    is_enabled: bool = True


@dataclass
class MyClassDJ(DataClassJsonMixin):
    my_ledger: Dict[str, Any]
    the_answer_to_life: Optional[int]
    people: List['PersonDJ']
    is_enabled: bool = True


# New Mashumaro Model
@dataclass
class MyClassMashumaro(mashumaro.DataClassDictMixin):
    my_ledger: Dict[str, Any]
    the_answer_to_life: Optional[int]
    people: List['Person']
    is_enabled: bool = True


@dataclass
class Person:
    name: 'Name'
    age: int
    birthdate: datetime
    gender: str
    occupation: Union[str, List[str]]
    hobbies: Dict[str, List[str]] = field(
        default_factory=lambda: defaultdict(list))


class Name(NamedTuple):
    first: str
    last: str
    salutation: Optional[str] = 'Mr.'

@dataclass
class NameDataclass:
    first: str
    last: str
    salutation: Optional[str] = 'Mr.'


@dataclass
class PersonDJ:
    name: NameDataclass
    age: int
    birthdate: datetime = field(metadata=config(
        encoder=datetime.isoformat,
        decoder=as_datetime,
        mm_field=marshmallow.fields.DateTime(format='iso')
    ))
    gender: str
    occupation: Union[str, List[str]]
    hobbies: Dict[str, List[str]] = field(
        default_factory=lambda: defaultdict(list))


# Model for `dataclass-wizard`
WizType = TypeVar('WizType', MyClass, JSONWizard)
# Model for `jsons`
JsonsType = TypeVar('JsonsType', MyClass, JsonSerializable)
# Model for `dataclasses-json`
DJType = TypeVar('DJType', MyClass, DataClassJsonMixin)
# Model for `mashumaro`
MashumaroType = TypeVar('MashumaroType', MyClass, mashumaro.DataClassDictMixin)
# Factory for `dataclass-factory`
factory = dataclass_factory.Factory()

MyClassWizard: WizType = create_new_class(
    MyClass, (MyClass, JSONWizard), 'Wizard',
    attr_dict=vars(MyClass).copy())
# MyClassDJ: DJType = create_new_class(
#     MyClass, (MyClass, DataClassJsonMixin), 'DJ',
#     attr_dict=vars(MyClass).copy())
MyClassJsons: JsonsType = create_new_class(
    MyClass, (MyClass, JsonSerializable), 'Jsons',
    attr_dict=vars(MyClass).copy())
MyClassMashumaro: MashumaroType = create_new_class(
    MyClass, (MyClass, mashumaro.DataClassDictMixin), 'Mashumaro',
    attr_dict=vars(MyClass).copy())



def custom_name_decoder(value):
    return Name(**value)


@pytest.fixture(scope='session')
def data():
    return {
        'my_ledger': {
            'Day 1': 'some details',
            'Day 17': ['a', 'sample', 'list']
        },
        'the_answer_to_life': '42',
        'people': [
            {
                'name': ('Roberto', 'Fuirron'),
                'age': 21,
                'birthdate': '1950-02-28T17:35:20Z',
                'gender': 'M',
                'occupation': ['sailor', 'fisher'],
                'hobbies': {'M-F': ('chess', '123', 'reading'), 'Sat-Sun': ['parasailing']}
            },
            {
                'name': ('Janice', 'Darr', 'Dr.'),
                'age': 45,
                'birthdate': '1971-11-05T05:10:59Z',
                'gender': 'F',
                'occupation': 'Dentist'
            }
        ]
    }


@pytest.fixture(scope='session')
def data_2(data):
    """data for `dataclasses-factory`, which has issue with tuple -> NamedTuple"""

    d = data.copy()
    d['people'] = [p.copy() for p in data['people']]

    # I want to make this into a Tuple - ('Roberto', 'Fuirron') -
    # but `dataclass-factory` doesn't seem to like that.

    d['people'][0]['name'] = {'first': 'Roberto', 'last': 'Fuirron'}
    d['people'][1]['name'] = {'first': 'Janice', 'last': 'Darr', 'salutation': 'Dr.'}

    return d


def parse_iso_format(data):
    return as_datetime(data)

iso_format_schema = dataclass_factory.Schema(
    parser=parse_iso_format,
    serializer=datetime.isoformat
)

factory.schemas = {
    datetime: iso_format_schema
}

def test_load(request, data, data_2, n):
    g = globals().copy()
    g.update(locals())

    log.info('dataclass-wizard     %f',
             timeit('MyClassWizard.from_dict(data)', globals=g, number=n))

    log.info('dataclass-factory    %f',
             timeit('factory.load(data_2, MyClass)', globals=g, number=n))

    log.info('dataclasses-json     %f',
             timeit('MyClassDJ.from_dict(data_2)', globals=g, number=n))

    log.info('mashumaro            %f',
             timeit('MyClassMashumaro.from_dict(data)', globals=g, number=n))

    if not request.config.getoption("--all"):
        pytest.skip("Skipping benchmarks for the rest by default, unless --all is specified.")

    log.info('jsons                %f',
             timeit('MyClassJsons.load(data)', globals=g, number=n))

    log.info('jsons (strict)       %f',
             timeit('MyClassJsons.load(data, strict=True)', globals=g, number=n))

    # Assert the dataclass instances have the same values for all fields.
    c1 = MyClassWizard.from_dict(data)
    c2 = factory.load(data_2, MyClass)
    c3 = MyClassDJ.from_dict(data)
    c4 = MyClassJsons.load(data)
    c5 = MyClassMashumaro.from_dict(data)

    # Since these models might differ slightly, we can skip exact equality checks
    # assert c1.__dict__ == c2.__dict__ == c3.__dict__ == c4.__dict__ == c5.__dict__

def test_dump(request, data, data_2, n):
    c1 = MyClassWizard.from_dict(data)
    c2 = factory.load(data_2, MyClass)
    c3 = MyClassDJ.from_dict(data_2)
    c4 = MyClassJsons.load(data)
    c5 = MyClassMashumaro.from_dict(data)

    g = globals().copy()
    g.update(locals())

    log.info('dataclass-wizard     %f',
             timeit('c1.to_dict()', globals=g, number=n))

    log.info('asdict (dataclasses) %f',
             timeit('asdict(c1)', globals=g, number=n))

    log.info('dataclass-factory    %f',
             timeit('factory.dump(c2, MyClass)', globals=g, number=n))

    log.info('dataclasses-json     %f',
             timeit('c3.to_dict()', globals=g, number=n))

    log.info('mashumaro            %f',
             timeit('c5.to_dict()', globals=g, number=n))

    if not request.config.getoption("--all"):
        pytest.skip("Skipping benchmarks for the rest by default, unless --all is specified.")

    log.info('jsons                %f',
             timeit('c4.dump()', globals=g, number=n))

    log.info('jsons (strict)       %f',
             timeit('c4.dump(strict=True)', globals=g, number=n))

    # Assert the dict objects which are the result of `to_dict` are all equal.
    c1_dict = {to_snake_case(f): fval for f, fval in c1.to_dict().items()}

   #  assert c1_dict == factory.dump(c2, MyClass) == c3.to_dict() == c4.dump() == c5.to_dict()
