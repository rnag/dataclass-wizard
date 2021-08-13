import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Union, List, ClassVar, DefaultDict, Set

import pytest

from dataclass_wizard import property_wizard
from ..conftest import Literal, Annotated, PY39_OR_ABOVE

log = logging.getLogger(__name__)


def test_property_wizard_does_not_affect_normal_properties():
    """
    The `property_wizard` should not otherwise affect normal properties (i.e. ones
    that don't have their property names (or underscored names) annotated as a
    dataclass field.

    """
    @dataclass
    class Vehicle(metaclass=property_wizard):

        def __post_init__(self):
            self.wheels = 4
            self._my_prop = 0

        @property
        def wheels(self) -> int:
            return self._wheels

        @wheels.setter
        def wheels(self, wheels: Union[int, str]):
            self._wheels = int(wheels)

        @property
        def _my_prop(self) -> int:
            return self.my_prop

        @_my_prop.setter
        def _my_prop(self, my_prop: Union[int, str]):
            self.my_prop = int(my_prop) + 5

    v = Vehicle()
    log.debug(v)
    assert v.wheels == 4
    assert v._my_prop == 5

    # These should all result in a `TypeError`, as neither `wheels` nor
    # `_my_prop` are valid arguments to the constructor, as they are just
    # normal properties.

    with pytest.raises(TypeError):
        _ = Vehicle(wheels=3)

    with pytest.raises(TypeError):
        _ = Vehicle('6')

    with pytest.raises(TypeError):
        _ = Vehicle(_my_prop=2)

    v.wheels = '123'
    assert v.wheels == 123, 'Expected assignment to use the setter method'

    v._my_prop = '5'
    assert v._my_prop == 10, 'Expected assignment to use the setter method'


def test_property_wizard_does_not_affect_read_only_properties():
    """
    The `property_wizard` should not otherwise affect properties which are
    read-only (i.e. ones which don't define a `setter` method)

    """
    @dataclass
    class Vehicle(metaclass=property_wizard):
        list_of_wheels: list = field(default_factory=list)

        @property
        def wheels(self) -> int:
            return len(self.list_of_wheels)

    v = Vehicle()
    log.debug(v)
    assert v.wheels == 0

    # AttributeError: can't set attribute
    with pytest.raises(AttributeError):
        v.wheels = 3

    v = Vehicle(list_of_wheels=[1, 2, 1])
    assert v.wheels == 3

    v.list_of_wheels = [0]
    assert v.wheels == 1


def test_property_wizard_with_public_property_and_underscored_field():
    """
    Using `property_wizard` when the dataclass has an public property and an
    underscored field name.
    """
    @dataclass
    class Vehicle(metaclass=property_wizard):

        _wheels: Union[int, str] = 4

        @property
        def wheels(self) -> int:
            return self._wheels

        @wheels.setter
        def wheels(self, wheels: Union[int, str]):
            self._wheels = int(wheels)

    v = Vehicle()
    log.debug(v)
    assert v.wheels == 4

    # Note that my IDE complains here, and suggests `_wheels` as a possible
    # keyword argument to the constructor method; however, that's wrong and
    # will error if you try it way.
    v = Vehicle(wheels=3)
    log.debug(v)
    assert v.wheels == 3

    v = Vehicle('6')
    log.debug(v)
    assert v.wheels == 6, 'The constructor should use our setter method'

    v.wheels = '123'
    assert v.wheels == 123, 'Expected assignment to use the setter method'


def test_property_wizard_with_public_property_and_field():
    """
    Using `property_wizard` when the dataclass has both a property and field
    name *without* a leading underscore.
    """
    @dataclass
    class Vehicle(metaclass=property_wizard):

        # The value of `wheels` here will be ignored, since `wheels` is simply
        # re-assigned on the following property definition.
        wheels: Union[int, str] = 4

        @property
        def wheels(self) -> int:
            return self._wheels

        @wheels.setter
        def wheels(self, wheels: Union[int, str]):
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


def test_property_wizard_with_underscored_property_and_public_field():
    """
    Using `property_wizard` when the dataclass has an underscored property and
    a public field name.
    """
    @dataclass
    class Vehicle(metaclass=property_wizard):

        wheels: Union[int, str] = 4

        @property
        def _wheels(self) -> int:
            return self._wheels

        @_wheels.setter
        def _wheels(self, wheels: Union[int, str]):
            self._wheels = int(wheels)

    v = Vehicle()
    log.debug(v)
    assert v.wheels == 4

    v = Vehicle(wheels=3)
    log.debug(v)
    assert v.wheels == 3

    v = Vehicle('6')
    log.debug(v)
    assert v.wheels == 6, 'The constructor should use our setter method'

    v.wheels = '123'
    assert v.wheels == 123, 'Expected assignment to use the setter method'


def test_property_wizard_with_underscored_property_and_field():
    """
    Using `property_wizard` when the dataclass has both a property and field
    name with a leading underscore.

    Note: this approach is generally *not* recommended, because the IDE won't
    know that the property or field name will be transformed to a public field
    name without the leading underscore, so it won't offer the desired type
    hints and auto-completion here.

    """
    @dataclass
    class Vehicle(metaclass=property_wizard):

        # The value of `_wheels` here will be ignored, since `_wheels` is
        # simply re-assigned on the following property definition.
        _wheels: Union[int, str] = 4

        @property
        def _wheels(self) -> int:
            return self._wheels

        @_wheels.setter
        def _wheels(self, wheels: Union[int, str]):
            self._wheels = int(wheels)

    v = Vehicle()
    log.debug(v)
    assert v.wheels == 0

    # Note that my IDE complains here, and suggests `_wheels` as a possible
    # keyword argument to the constructor method; however, that's wrong and
    # will error if you try it way.
    v = Vehicle(wheels=3)
    log.debug(v)
    assert v.wheels == 3

    v = Vehicle('6')
    log.debug(v)
    assert v.wheels == 6, 'The constructor should use our setter method'

    v.wheels = '123'
    assert v.wheels == 123, 'Expected assignment to use the setter method'


def test_property_wizard_with_public_property_and_annotated_field():
    """
    Using `property_wizard` when the dataclass has both a property and field
    name *without* a leading underscore, and the field is a
    :class:`typing.Annotated` type.
    """
    @dataclass
    class Vehicle(metaclass=property_wizard):

        # The value of `wheels` here will be ignored, since `wheels` is simply
        # re-assigned on the following property definition.
        wheels: Annotated[Union[int, str], field(default=4)] = None

        @property
        def wheels(self) -> int:
            return self._wheels

        @wheels.setter
        def wheels(self, wheels: Union[int, str]):
            self._wheels = int(wheels)

    v = Vehicle()
    log.debug(v)
    assert v.wheels == 4

    v = Vehicle(wheels=3)
    log.debug(v)
    assert v.wheels == 3

    v = Vehicle('6')
    log.debug(v)
    assert v.wheels == 6, 'The constructor should use our setter method'

    v.wheels = '123'
    assert v.wheels == 123, 'Expected assignment to use the setter method'


def test_property_wizard_with_private_property_and_annotated_field_with_no_useful_extras():
    """
    Using `property_wizard` when the dataclass has both a property and field
    name with a leading underscore, and the field is a
    :class:`typing.Annotated` type without any extras that are a
    :class:`dataclasses.Field` type.
    """
    @dataclass
    class Vehicle(metaclass=property_wizard):

        # The value of `wheels` here will be ignored, since `wheels` is simply
        # re-assigned on the following property definition.
        _wheels: Annotated[Union[int, str], 'Hello world!', 123] = None

        @property
        def _wheels(self) -> int:
            return self._wheels

        @_wheels.setter
        def _wheels(self, wheels: Union[int, str]):
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


def test_property_wizard_with_multiple_inheritance():
    """
    When using multiple inheritance or when extending from more than one
    class, and if any of the super classes define properties that should also
    be `dataclass` fields, then the recommended approach is to define the
    `property_wizard` metaclass on each class that has such properties. Note
    that the last class in the below example (Car) doesn't need to use this
    metaclass, as it doesn't have any properties that meet this condition.

    """
    @dataclass
    class VehicleWithWheels(metaclass=property_wizard):
        _wheels: Union[int, str] = field(default=4)

        @property
        def wheels(self) -> int:
            return self._wheels

        @wheels.setter
        def wheels(self, wheels: Union[int, str]):
            self._wheels = int(wheels)

    @dataclass
    class Vehicle(VehicleWithWheels, metaclass=property_wizard):
        _windows: Union[int, str] = field(default=6)

        @property
        def windows(self) -> int:
            return self._windows

        @windows.setter
        def windows(self, windows: Union[int, str]):
            self._windows = int(windows)

    @dataclass
    class Car(Vehicle):
        my_list: List[str] = field(default_factory=list)

    v = Car()
    log.debug(v)
    assert v.wheels == 4
    assert v.windows == 6
    assert v.my_list == []

    # Note that my IDE complains here, and suggests `_wheels` as a possible
    # keyword argument to the constructor method; however, that's wrong and
    # will error if you try it way.
    v = Car(wheels=3, windows=5, my_list=['hello', 'world'])
    log.debug(v)
    assert v.wheels == 3
    assert v.windows == 5
    assert v.my_list == ['hello', 'world']

    v = Car('6', '7', ['testing'])
    log.debug(v)
    assert v.wheels == 6, 'The constructor should use our setter method'
    assert v.windows == 7, 'The constructor should use our setter method'
    assert v.my_list == ['testing']

    v.wheels = '123'
    assert v.wheels == 123, 'Expected assignment to use the setter method'
    v.windows = '321'
    assert v.windows == 321, 'Expected assignment to use the setter method'

# NOTE: the below test cases are added for coverage purposes


def test_property_wizard_with_public_property_and_underscored_field_without_default_value():
    """
    Using `property_wizard` when the dataclass has a public property, and an
    underscored field *without* a default value explicitly set.
    """
    @dataclass
    class Vehicle(metaclass=property_wizard):

        _wheels: Union[int, str]

        @property
        def wheels(self) -> int:
            return self._wheels

        @wheels.setter
        def wheels(self, wheels: Union[int, str]):
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


def test_property_wizard_with_public_property_and_underscored_field_with_default_factory():
    """
    Using `property_wizard` when the dataclass has a public property, and an
    underscored field has only `default_factory` set.
    """
    @dataclass
    class Vehicle(metaclass=property_wizard):

        _wheels: Union[int, str] = field(default_factory=str)

        @property
        def wheels(self) -> int:
            return self._wheels

        @wheels.setter
        def wheels(self, wheels: Union[int, str]):
            self._wheels = int(wheels)

    with pytest.raises(ValueError):
        # Setter raises ValueError, as `wheels` will be a string by default
        _ = Vehicle()

    v = Vehicle(wheels=3)
    log.debug(v)
    assert v.wheels == 3

    v = Vehicle('6')
    log.debug(v)
    assert v.wheels == 6, 'The constructor should use our setter method'

    v.wheels = '123'
    assert v.wheels == 123, 'Expected assignment to use the setter method'


def test_property_wizard_with_public_property_and_underscored_field_without_default_or_default_factory():
    """
    Using `property_wizard` when the dataclass has a public property, and an
    underscored field has neither `default` or `default_factory` set.
    """
    @dataclass
    class Vehicle(metaclass=property_wizard):

        _wheels: Union[int, str] = field()

        @property
        def wheels(self) -> int:
            return self._wheels

        @wheels.setter
        def wheels(self, wheels: Union[int, str]):
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


def test_property_wizard_with_underscored_property_and_public_field_without_default_value():
    """
    Using `property_wizard` when the dataclass has an underscored property,
    and a public field *without* a default value explicitly set.
    """
    @dataclass
    class Vehicle(metaclass=property_wizard):

        wheels: Union[int, str]

        @property
        def _wheels(self) -> int:
            return self._wheels

        @_wheels.setter
        def _wheels(self, wheels: Union[int, str]):
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


def test_property_wizard_with_public_property_and_public_field_is_property():
    """
    Using `property_wizard` when the dataclass has an underscored property,
    and a public field is also defined as a property.
    """
    @dataclass
    class Vehicle(metaclass=property_wizard):

        # The value of `wheels` here will be ignored, since `wheels` is simply
        # re-assigned on the following property definition.
        wheels = property
        # Defines the default value for `wheels`, since it won't work if we
        # define it above. The `init=False` is needed since otherwise IDEs
        # seem to suggest `_wheels` as a parameter to the constructor method,
        # which shouldn't be the case.
        #
        # Note: if are *ok* with the default value for the type (0 in this
        # case), then you can remove the below line and annotate the above
        # line instead as `wheels: Union[int, str] = property`
        _wheels: Union[int, str] = field(default=4, init=False)

        @wheels
        def wheels(self) -> int:
            return self._wheels

        @wheels.setter
        def wheels(self, wheels: Union[int, str]):
            self._wheels = int(wheels)

    v = Vehicle()
    log.debug(v)
    assert v.wheels == 4

    v = Vehicle(wheels=3)
    log.debug(v)
    assert v.wheels == 3

    v = Vehicle('6')
    log.debug(v)
    assert v.wheels == 6, 'The constructor should use our setter method'

    v.wheels = '123'
    assert v.wheels == 123, 'Expected assignment to use the setter method'


def test_property_wizard_with_underscored_property_and_public_field_with_default():
    """
    Using `property_wizard` when the dataclass has an underscored property,
    and the public field has `default` set.
    """
    @dataclass
    class Vehicle(metaclass=property_wizard):

        wheels: Union[int, str] = field(default=2)

        @property
        def _wheels(self) -> int:
            return self._wheels

        @_wheels.setter
        def _wheels(self, wheels: Union[int, str]):
            self._wheels = int(wheels)

    v = Vehicle()
    log.debug(v)
    assert v.wheels == 2

    v = Vehicle(wheels=3)
    log.debug(v)
    assert v.wheels == 3

    v = Vehicle('6')
    log.debug(v)
    assert v.wheels == 6, 'The constructor should use our setter method'

    v.wheels = '123'
    assert v.wheels == 123, 'Expected assignment to use the setter method'


def test_property_wizard_with_underscored_property_and_public_field_with_default_factory():
    """
    Using `property_wizard` when the dataclass has an underscored property,
    and the public field has only `default_factory` set.
    """
    @dataclass
    class Vehicle(metaclass=property_wizard):

        wheels: Union[int, str] = field(default_factory=str)

        @property
        def _wheels(self) -> int:
            return self._wheels

        @_wheels.setter
        def _wheels(self, wheels: Union[int, str]):
            self._wheels = int(wheels)

    with pytest.raises(ValueError):
        # Setter raises ValueError, as `wheels` will be a string by default
        _ = Vehicle()

    v = Vehicle(wheels=3)
    log.debug(v)
    assert v.wheels == 3

    v = Vehicle('6')
    log.debug(v)
    assert v.wheels == 6, 'The constructor should use our setter method'

    v.wheels = '123'
    assert v.wheels == 123, 'Expected assignment to use the setter method'


def test_property_wizard_with_underscored_property_and_public_field_without_default_or_default_factory():
    """
    Using `property_wizard` when the dataclass has an underscored property,
    and the public field has neither `default` or `default_factory` set.
    """
    @dataclass
    class Vehicle(metaclass=property_wizard):

        wheels: Union[int, str] = field()

        @property
        def _wheels(self) -> int:
            return self._wheels

        @_wheels.setter
        def _wheels(self, wheels: Union[int, str]):
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


def test_property_wizard_where_annotated_type_contains_none():
    """
    Using `property_wizard` when the annotated type for the dataclass field
    associated with a property is here a :class:`Union` type that contains
    `None`. As such, the field is technically an `Optional` so the default
    value will be `None` if no value is specified via the constructor.

    """
    @dataclass
    class Vehicle(metaclass=property_wizard):

        wheels: Union[int, str, None]

        @property
        def _wheels(self) -> int:
            return self._wheels

        @_wheels.setter
        def _wheels(self, wheels: Union[int, str]):
            self._wheels = int(wheels)

    # TypeError: int() argument is `None`
    with pytest.raises(TypeError):
        _ = Vehicle()

    v = Vehicle(wheels=3)
    log.debug(v)
    assert v.wheels == 3

    v = Vehicle('6')
    log.debug(v)
    assert v.wheels == 6, 'The constructor should use our setter method'

    v.wheels = '123'
    assert v.wheels == 123, 'Expected assignment to use the setter method'


def test_property_wizard_with_literal_type():
    """
    Using `property_wizard` when the dataclass field associated with a
    property is annotated with a :class:`Literal` type.
    """
    @dataclass
    class Vehicle(metaclass=property_wizard):

        # Annotate `wheels` as a literal that should only be set to 1 or 0
        # (similar to how the binary numeral system works, for example)
        #
        # Note: we can assign a default value for `wheels` explicitly, so that
        # the IDE doesn't complain when we omit the argument to the
        # constructor method, but it's technically not required.
        wheels: Literal[1, '1', 0, '0']

        @property
        def _wheels(self) -> int:
            return self._wheels

        @_wheels.setter
        def _wheels(self, wheels: Union[int, str]):
            self._wheels = int(wheels)

    v = Vehicle()
    log.debug(v)
    assert v.wheels == 1

    # The IDE should display a warning (`wheels` only accepts [0, 1]), however
    # it won't prevent the assignment here.
    v = Vehicle(wheels=3)
    log.debug(v)
    assert v.wheels == 3

    # The IDE should display no warning here, as this is an acceptable value
    v = Vehicle('1')
    log.debug(v)
    assert v.wheels == 1, 'The constructor should use our setter method'

    v.wheels = '123'
    assert v.wheels == 123, 'Expected assignment to use the setter method'


def test_property_wizard_with_concrete_type():
    """
    Using `property_wizard` when the dataclass field associated with a
    property is annotated with a non-generic type, such as a `str` or `int`.
    """
    @dataclass
    class Vehicle(metaclass=property_wizard):

        wheels: int

        @property
        def _wheels(self) -> int:
            return self._wheels

        @_wheels.setter
        def _wheels(self, wheels: Union[int, str]):
            self._wheels = int(wheels)

    v = Vehicle()
    log.debug(v)
    assert v.wheels == 0

    v = Vehicle(wheels=3)
    log.debug(v)
    assert v.wheels == 3

    v = Vehicle('1')
    log.debug(v)
    assert v.wheels == 1, 'The constructor should use our setter method'

    v.wheels = '123'
    assert v.wheels == 123, 'Expected assignment to use the setter method'


def test_property_wizard_with_concrete_type_and_default_factory_raises_type_error():
    """
    Using `property_wizard` when the dataclass field associated with a
    property is annotated with a non-generic type, such as a `datetime`, which
    doesn't have a no-args constructor. Since `property_wizard` is not able to
    instantiate a new `datetime`, the default value should be ``None``.

    """
    @dataclass
    class Vehicle(metaclass=property_wizard):

        # Date when the vehicle was sold
        sold_dt: datetime

        @property
        def _sold_dt(self) -> int:
            return self._sold_dt

        @_sold_dt.setter
        def _sold_dt(self, sold_dt: datetime):
            """Save the datetime with the year set to `2010`"""
            self._sold_dt = sold_dt.replace(year=2010)

    # AttributeError: 'NoneType' object has no attribute 'replace'
    with pytest.raises(AttributeError):
        _ = Vehicle()

    dt = datetime(2020, 1, 1, 12, 0, 0)             # Jan. 1 2020 12:00 PM
    expected_dt = datetime(2010, 1, 1, 12, 0, 0)    # Jan. 1 2010 12:00 PM

    v = Vehicle(sold_dt=dt)
    log.debug(v)
    assert v.sold_dt != dt
    assert v.sold_dt == expected_dt, 'The constructor should use our setter ' \
                                     'method'

    dt = datetime.min
    expected_dt = datetime.min.replace(year=2010)

    v.sold_dt = dt
    assert v.sold_dt == expected_dt, 'Expected assignment to use the setter ' \
                                     'method'


def test_property_wizard_with_generic_type_which_is_not_supported():
    """
    Using `property_wizard` when the dataclass field associated with a
    property is annotated with a generic type other than one of the supported
    types (e.g. Literal and Union).

    """

    @dataclass
    class Vehicle(metaclass=property_wizard):
        # Date when the vehicle was sold
        sold_dt: ClassVar[datetime]

        @property
        def _sold_dt(self) -> int:
            return self._sold_dt

        @_sold_dt.setter
        def _sold_dt(self, sold_dt: datetime):
            """Save the datetime with the year set to `2010`"""
            self._sold_dt = sold_dt.replace(year=2010)

    v = Vehicle()
    log.debug(v)

    dt = datetime(2020, 1, 1, 12, 0, 0)  # Jan. 1 2020 12:00 PM
    expected_dt = datetime(2010, 1, 1, 12, 0, 0)  # Jan. 1 2010 12:00 PM

    # TypeError: __init__() got an unexpected keyword argument 'sold_dt'
    #   Note: This is expected because the field for the property is a
    #   `ClassVar`, and even `dataclasses` excludes this annotated type
    #   from the constructor.
    with pytest.raises(TypeError):
        _ = Vehicle(sold_dt=dt)

    # Our property should still work as expected, however
    v.sold_dt = dt
    assert v.sold_dt == expected_dt, 'Expected assignment to use the setter ' \
                                     'method'


def test_property_wizard_with_mutable_types_v1():
    """
    The `property_wizard` handles mutable collections (e.g. subclasses of list,
    dict, and set) as expected. The defaults for these mutable types should
    use a `default_factory` so we can observe the expected behavior.
    """

    @dataclass
    class Vehicle(metaclass=property_wizard):

        wheels: List[Union[int, str]]
        # _wheels: List[Union[int, str]] = field(init=False)

        inverse_bool_set: Set[bool]
        # Not needed, but we can also define this as below if we want to
        # inverse_bool_set: Annotated[Set[bool], field(default_factory=set)]

        # We'll need the `field(default_factory=...)` syntax here, because
        # otherwise the default_factory will be `defaultdict()`, which is not what
        # we want.
        wheels_dict: Annotated[
            DefaultDict[str, List[str]],
            field(default_factory=lambda: defaultdict(list))
        ]

        @property
        def wheels(self) -> List[int]:
            return self._wheels

        @wheels.setter
        def wheels(self, wheels: List[Union[int, str]]):
            self._wheels = [int(w) for w in wheels]

        @property
        def inverse_bool_set(self) -> Set[bool]:
            return self._inverse_bool_set

        @inverse_bool_set.setter
        def inverse_bool_set(self, bool_set: Set[bool]):
            # Confirm that we're passed in the right type when no value is set via
            # the constructor (i.e. from the `property_wizard` metaclass)
            assert isinstance(bool_set, set)
            self._inverse_bool_set = {not b for b in bool_set}

        @property
        def wheels_dict(self) -> int:
            return self._wheels_dict

        @wheels_dict.setter
        def wheels_dict(self, wheels: Union[int, str]):
            self._wheels_dict = wheels

    v1 = Vehicle(wheels=['1', '2', '3'],
                 inverse_bool_set={True, False},
                 wheels_dict=defaultdict(list, key=['value']))
    v1.wheels_dict['key2'].append('another value')
    log.debug(v1)

    v2 = Vehicle()
    v2.wheels.append(4)
    v2.wheels_dict['a'].append('5')
    v2.inverse_bool_set.add(True)
    log.debug(v2)

    v3 = Vehicle()
    v3.wheels.append(1)
    v3.wheels_dict['b'].append('2')
    v3.inverse_bool_set.add(False)
    log.debug(v3)

    assert v1.wheels == [1, 2, 3]
    assert v1.inverse_bool_set == {False, True}
    assert v1.wheels_dict == {'key': ['value'], 'key2': ['another value']}

    assert v2.wheels == [4]
    assert v2.inverse_bool_set == {True}
    assert v2.wheels_dict == {'a': ['5']}

    assert v3.wheels == [1]
    assert v3.inverse_bool_set == {False}
    assert v3.wheels_dict == {'b': ['2']}


def test_property_wizard_with_mutable_types_v2():
    """
    The `property_wizard` handles mutable collections (e.g. subclasses of list,
    dict, and set) as expected. The defaults for these mutable types should
    use a `default_factory` so we can observe the expected behavior.

    In this version, we explicitly pass in the `field(default_factory=...)`
    syntax for all field properties, though it's technically not needed.
    """

    @dataclass
    class Vehicle(metaclass=property_wizard):
        wheels: Annotated[List[int], field(default_factory=list)]
        _wheels_list: list = field(default_factory=list)

        @property
        def wheels_list(self) -> list:
            return self._wheels_list

        @wheels_list.setter
        def wheels_list(self, wheels):
            self._wheels_list = wheels

        @property
        def wheels(self) -> list:
            return self._wheels

        @wheels.setter
        def wheels(self, wheels):
            self._wheels = wheels

    v1 = Vehicle(wheels=[1, 2], wheels_list=[2, 1])
    v1.wheels.append(3)
    v1.wheels_list.insert(0, 3)
    log.debug(v1)

    v2 = Vehicle()
    log.debug(v2)

    v2.wheels.append(2)
    v2.wheels.append(1)
    v2.wheels_list.append(1)
    v2.wheels_list.append(2)

    v3 = Vehicle()
    log.debug(v3)

    v3.wheels.append(1)
    v3.wheels.append(1)
    v3.wheels_list.append(5)
    v3.wheels_list.append(5)

    assert v1.wheels == [1, 2, 3]
    assert v1.wheels_list == [3, 2, 1]
    assert v2.wheels == [2, 1]
    assert v2.wheels_list == [1, 2]
    assert v3.wheels == [1, 1]
    assert v3.wheels_list == [5, 5]


@pytest.mark.skipif(not PY39_OR_ABOVE, reason='requires Python 3.9 or higher')
def test_property_wizard_with_mutable_types_with_parameterized_standard_collections():
    """
    Test case for mutable types with a Python 3.9 specific feature:
    parameterized standard collections. As such, this test case is only
    expected to pass for Python 3.9+.
    """

    @dataclass
    class Vehicle(metaclass=property_wizard):

        wheels: list[Union[int, str]]
        # _wheels: List[Union[int, str]] = field(init=False)

        inverse_bool_set: set[bool]
        # Not needed, but we can also define this as below if we want to
        # inverse_bool_set: Annotated[Set[bool], field(default_factory=set)]

        # We'll need the `field(default_factory=...)` syntax here, because
        # otherwise the default_factory will be `defaultdict()`, which is not what
        # we want.
        wheels_dict: Annotated[
            defaultdict[str, List[str]],
            field(default_factory=lambda: defaultdict(list))
        ]

        @property
        def wheels(self) -> List[int]:
            return self._wheels

        @wheels.setter
        def wheels(self, wheels: List[Union[int, str]]):
            self._wheels = [int(w) for w in wheels]

        @property
        def inverse_bool_set(self) -> Set[bool]:
            return self._inverse_bool_set

        @inverse_bool_set.setter
        def inverse_bool_set(self, bool_set: Set[bool]):
            # Confirm that we're passed in the right type when no value is set via
            # the constructor (i.e. from the `property_wizard` metaclass)
            assert isinstance(bool_set, set)
            self._inverse_bool_set = {not b for b in bool_set}

        @property
        def wheels_dict(self) -> int:
            return self._wheels_dict

        @wheels_dict.setter
        def wheels_dict(self, wheels: Union[int, str]):
            self._wheels_dict = wheels

    v1 = Vehicle(wheels=['1', '2', '3'],
                 inverse_bool_set={True, False},
                 wheels_dict=defaultdict(list, key=['value']))
    v1.wheels_dict['key2'].append('another value')
    log.debug(v1)

    v2 = Vehicle()
    v2.wheels.append(4)
    v2.wheels_dict['a'].append('5')
    v2.inverse_bool_set.add(True)
    log.debug(v2)

    v3 = Vehicle()
    v3.wheels.append(1)
    v3.wheels_dict['b'].append('2')
    v3.inverse_bool_set.add(False)
    log.debug(v3)

    assert v1.wheels == [1, 2, 3]
    assert v1.inverse_bool_set == {False, True}
    assert v1.wheels_dict == {'key': ['value'], 'key2': ['another value']}

    assert v2.wheels == [4]
    assert v2.inverse_bool_set == {True}
    assert v2.wheels_dict == {'a': ['5']}

    assert v3.wheels == [1]
    assert v3.inverse_bool_set == {False}
    assert v3.wheels_dict == {'b': ['2']}
