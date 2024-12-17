import logging
from dataclasses import dataclass
from typing import Any

import pytest

from dataclasses_json import (dataclass_json, Undefined, CatchAll as CatchAllDJ)
from dataclass_wizard import (JSONWizard, CatchAll as CatchAllWizard)


log = logging.getLogger(__name__)


@dataclass()
class DontCareAPIDump:
    endpoint: str
    data: dict[str, Any]


@dataclass_json(undefined=Undefined.INCLUDE)
@dataclass()
class DontCareAPIDumpDJ(DontCareAPIDump):
    unknown_things: CatchAllDJ


@dataclass()
class DontCareAPIDumpWizard(DontCareAPIDump, JSONWizard):

    class _(JSONWizard.Meta):
        v1 = True

    unknown_things: CatchAllWizard


# Fixtures for test data
@pytest.fixture(scope='session')
def data():
    return {"endpoint": "some_api_endpoint",
            "data": {"foo": 1, "bar": "2"},
            "undefined_field_name": [1, 2, 3]}


@pytest.fixture(scope='session')
def data_no_extras():
    return {"endpoint": "some_api_endpoint",
            "data": {"foo": 1, "bar": "2"}}


# Benchmark for deserialization (from_dict)
@pytest.mark.benchmark(group="deserialization")
def test_deserialize_wizard(benchmark, data):
    benchmark(lambda: DontCareAPIDumpWizard.from_dict(data))


@pytest.mark.benchmark(group="deserialization")
def test_deserialize_json(benchmark, data):
    benchmark(lambda: DontCareAPIDumpDJ.from_dict(data))


# Benchmark for deserialization with no extra data
@pytest.mark.benchmark(group="deserialization_no_extra_data")
def test_deserialize_wizard_no_extras(benchmark, data_no_extras):
    benchmark(lambda: DontCareAPIDumpWizard.from_dict(data_no_extras))


@pytest.mark.benchmark(group="deserialization_no_extra_data")
def test_deserialize_json_no_extras(benchmark, data_no_extras):
    benchmark(lambda: DontCareAPIDumpDJ.from_dict(data_no_extras))


# Benchmark for serialization (to_dict)
@pytest.mark.benchmark(group="serialization")
def test_serialize_wizard(benchmark, data):
    dump1 = DontCareAPIDumpWizard.from_dict(data)
    benchmark(lambda: dump1.to_dict())


@pytest.mark.benchmark(group="serialization")
def test_serialize_json(benchmark, data):
    dump2 = DontCareAPIDumpDJ.from_dict(data)
    benchmark(lambda: dump2.to_dict())


def test_validate(data, data_no_extras):
    dump1 = DontCareAPIDumpDJ.from_dict(data_no_extras)  # DontCareAPIDump(endpoint='some_api_endpoint', data={'foo': 1, 'bar': '2'})
    dump2 = DontCareAPIDumpWizard.from_dict(data_no_extras)  # DontCareAPIDump(endpoint='some_api_endpoint', data={'foo': 1, 'bar': '2'})

    assert dump1.endpoint == dump2.endpoint
    assert dump1.data == dump2.data
    assert dump1.unknown_things == dump2.unknown_things == {}

    expected = {'endpoint': 'some_api_endpoint', 'data': {'foo': 1, 'bar': '2'}}

    assert dump1.to_dict() == dump2.to_dict() == expected

    dump1 = DontCareAPIDumpDJ.from_dict(data)  # DontCareAPIDump(endpoint='some_api_endpoint', data={'foo': 1, 'bar': '2'})
    dump2 = DontCareAPIDumpWizard.from_dict(data)  # DontCareAPIDump(endpoint='some_api_endpoint', data={'foo': 1, 'bar': '2'})

    assert dump1.endpoint == dump2.endpoint
    assert dump1.data == dump2.data
    assert dump1.unknown_things == dump2.unknown_things

    expected = {'endpoint': 'some_api_endpoint', 'data': {'foo': 1, 'bar': '2'}, 'undefined_field_name': [1, 2, 3]}

    assert dump1.to_dict() == dump2.to_dict() == expected
