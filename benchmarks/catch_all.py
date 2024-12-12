import logging
from dataclasses import dataclass
from timeit import timeit
from typing import Any

import pytest

from dataclasses_json import (dataclass_json,
                              Undefined,
                              CatchAll as CatchAllDJ)

from dataclass_wizard import (JSONWizard,
                              CatchAll as CatchAllWizard)


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


@pytest.fixture(scope='session')
def data():
    return {"endpoint": "some_api_endpoint",
            "data": {"foo": 1, "bar": "2"},
            "undefined_field_name": [1, 2, 3]}


@pytest.fixture(scope='session')
def data_no_extras():
    return {"endpoint": "some_api_endpoint",
            "data": {"foo": 1, "bar": "2"}}


def test_load(data, n):
    """
    [ RESULTS ON MAC OS X ]

    benchmarks.catch_all.catch_all - [INFO] dataclass-wizard     0.060889
    benchmarks.catch_all.catch_all - [INFO] dataclasses-json     11.469157

    """
    g = globals().copy()
    g.update(locals())

    log.info('dataclass-wizard     %f',
             timeit('DontCareAPIDumpWizard.from_dict(data)', globals=g, number=n))
    log.info('dataclasses-json     %f',
             timeit('DontCareAPIDumpDJ.from_dict(data)', globals=g, number=n))

    dump1 = DontCareAPIDumpDJ.from_dict(data)  # DontCareAPIDump(endpoint='some_api_endpoint', data={'foo': 1, 'bar': '2'})
    dump2 = DontCareAPIDumpWizard.from_dict(data)  # DontCareAPIDump(endpoint='some_api_endpoint', data={'foo': 1, 'bar': '2'})

    assert dump1.endpoint == dump2.endpoint
    assert dump1.data == dump2.data
    assert dump1.unknown_things == dump2.unknown_things


def test_load_with_no_extra_data(data_no_extras, n):
    """
    [ RESULTS ON MAC OS X ]

    benchmarks.catch_all.catch_all - [INFO] dataclass-wizard     0.045790
    benchmarks.catch_all.catch_all - [INFO] dataclasses-json     11.031206

    """
    g = globals().copy()
    g.update(locals())

    log.info('dataclass-wizard     %f',
             timeit('DontCareAPIDumpWizard.from_dict(data_no_extras)', globals=g, number=n))
    log.info('dataclasses-json     %f',
             timeit('DontCareAPIDumpDJ.from_dict(data_no_extras)', globals=g, number=n))

    dump1 = DontCareAPIDumpDJ.from_dict(data_no_extras)  # DontCareAPIDump(endpoint='some_api_endpoint', data={'foo': 1, 'bar': '2'})
    dump2 = DontCareAPIDumpWizard.from_dict(data_no_extras)  # DontCareAPIDump(endpoint='some_api_endpoint', data={'foo': 1, 'bar': '2'})

    assert dump1.endpoint == dump2.endpoint
    assert dump1.data == dump2.data
    assert dump1.unknown_things == dump2.unknown_things == {}


def test_dump(data):
    """
    [ RESULTS ON MAC OS X ]

    benchmarks.catch_all.catch_all - [INFO] dataclass-wizard     0.317555
    benchmarks.catch_all.catch_all - [INFO] dataclasses-json     3.970232

    """
    dump1 = DontCareAPIDumpWizard.from_dict(data)
    dump2 = DontCareAPIDumpDJ.from_dict(data)

    g = globals().copy()
    g.update(locals())

    log.info('dataclass-wizard     %f',
             timeit('dump1.to_dict()', globals=g, number=n))
    log.info('dataclasses-json     %f',
             timeit('dump2.to_dict()', globals=g, number=n))

    expected = {'endpoint': 'some_api_endpoint', 'data': {'foo': 1, 'bar': '2'}, 'undefined_field_name': [1, 2, 3]}

    assert dump1.to_dict() == dump2.to_dict() == expected
