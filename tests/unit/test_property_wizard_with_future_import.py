from __future__ import annotations

import logging
from dataclasses import dataclass, field

from dataclass_wizard import property_wizard


log = logging.getLogger(__name__)


def test_property_wizard_with_public_property_and_field_with_or():
    """
    Using `property_wizard` when the dataclass has both a property and field
    name *without* a leading underscore, and using the OR ("|") operator,
    instead of the `typing.Union` usage.
    """
    @dataclass
    class Vehicle(metaclass=property_wizard):

        # The value of `wheels` here will be ignored, since `wheels` is simply
        # re-assigned on the following property definition.
        wheels: int | str = 4

        @property
        def wheels(self) -> int:
            return self._wheels

        @wheels.setter
        def wheels(self, wheels: int | str):
            self._wheels = int(wheels)

    v = Vehicle()
    log.debug(v)
    assert v.wheels == 0

    v = Vehicle(wheels=3)
    log.debug(v)
    assert v.wheels == 3

    v = Vehicle('6')
    log.debug(v)
    assert v.wheels == 6, 'The constructor should use our setter method'

    v.wheels = '123'
    assert v.wheels == 123, 'Expected assignment to use the setter method'


def test_property_wizard_with_unresolvable_forward_ref():
    """
    Using `property_wizard` when the annotated field for a property references
    a class or type that is not yet declared.
    """
    @dataclass
    class Vehicle(metaclass=property_wizard):

        # The value of `cars` here will be ignored, since `cars` is simply
        # re-assigned on the following property definition.
        cars: list[Car] = field(default_factory=list)
        trucks: list[Truck] = field(default_factory=list)

        @property
        def cars(self) -> int:
            return self._cars

        @cars.setter
        def cars(self, cars: list[Car]):
            self._cars = cars * 2 if cars else cars

    @dataclass
    class Car:
        spare_tires: int

    class Truck:
        ...

    v = Vehicle()
    log.debug(v)
    assert v.cars is None

    v = Vehicle([Car(1)])
    log.debug(v)
    assert v.cars == [Car(1), Car(1)], 'The constructor should use our ' \
                                       'setter method'

    v.cars = [Car(3)]
    assert v.cars == [Car(3), Car(3)], 'Expected assignment to use the ' \
                                       'setter method'
