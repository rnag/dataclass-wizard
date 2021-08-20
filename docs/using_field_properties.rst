======================
Using Field Properties
======================

I am personally a huge fan of the ``dataclasses`` module - to me it's a
truly modern, and Pythonic, way of defining your own container classes.
The best part is it frees you from a lot of the boilerplate code you'd otherwise
have to write, such as the ``__init__`` and ``__repr__`` magic methods.

However, using field properties  in ``dataclasses`` is just not obvious. You
can define normal properties easily enough, such as a ``count`` read-only
property which returns the length of a ``products`` list for example.
However, suppose you want the ability to pass in an initial value for a property
via the ``__init__`` constructor, or set a default value if not explicitly passed in
via the constructor method, then that's where it starts to get a little tricky. But
first, let's start out by defining what I mean by a field property.


Here is how I'd define the use of a *field property* in Python ``dataclasses``:

    A property that is also defined as ``dataclass`` field, such that an
    initial value can be set or passed in via the constructor method. This is mostly
    just syntactic sugar, to hint to the ``dataclass`` decorator that you want to add a
    parameter to the constructor and associate it with the property.
    The other implicit constraint is that setting the property via the constructor
    method and via the assignment operator should both call the validation logic
    in the property's ``setter`` method, so that ``Foo(x=bar)`` and ``foo.x = bar``
    should both achieve the same purpose.


If you are interested in learning more, I would recommend that you check out
this great article that delves a bit deeper into using properties in ``dataclasses`` :

* https://florimond.dev/en/posts/2018/10/reconciling-dataclasses-and-properties-in-python/


First, let's start out by exploring how field properties
(mostly) work with ``dataclasses``:

.. code:: python3

    from dataclasses import dataclass, field
    from typing import Union


    @dataclass
    class Vehicle:

        wheels: Union[int, str] = 0
        # Uncomment the field below if you want to make your IDE a bit happier.
        #   _wheels: int = field(repr=False, init=False)

        @property
        def wheels(self) -> int:
            return self._wheels

        @wheels.setter
        def wheels(self, wheels: Union[int, str]):
            self._wheels = int(wheels)


    if __name__ == '__main__':
        v = Vehicle(wheels='3')

        print(v)
        # prints:
        #   Vehicle(wheels=3)

        # This works as expected!
        assert v.wheels == 3, 'The constructor should use our setter method'

        # So does this...
        v.wheels = '6'
        assert v.wheels == 6

        # But it ends up failing here, because our `setter` method is passed
        # in a `property` object by the `dataclasses` decorator (as no initial
        # value is explicitly set)
        v = Vehicle()

        # We unfortunately won't get here :(
        print(v)

So in nearly all cases it seem to work as expected, except when there's no initial
value for the property specified via the constructor method; in that case, it
looks like ``dataclasses`` passes in a ``property`` object to our setter method.

This seems a bit odd, but if we wanted to then we can easily resolve this edge
case by modifying our setter method slightly as below:

.. code:: python3

    @wheels.setter
    def wheels(self, wheels: Union[int, str]):
        self._wheels = 0 if isinstance(wheels, property) else int(wheels)


And... looks like that fixed it! Now the initial code we put together seems to work as
expected. But from what I can tell there seems to be a few main issues with this:

* If we have multiple *field properties* in a ``dataclass``, that certainly means
  we need to remember to update each of their ``setter`` methods to handle this
  peculiar edge case.

* It'll be tricky if we want to update the default value for the property when no
  value is passed in via the ``__init__``. Likely we will have to replace this value
  in the setter method.

* Also, sometimes properties can have complex logic in their ``setter`` methods, so it
  probably won't be as easy as the one liner ``if-else`` statement above.


There's a couple good examples out there of handling properties with default values
in ``dataclasses``, and a solid attempt at supporting this can be found in the
`link here`_.

But as I've pointed out, there's only two main issues I had with the solution above:

1. The property getter and setter methods, ``get_wheels`` and ``set_wheels``, are exposed
   as public methods. If you wanted to, you can fix that by adding an underscore in front
   of their method names, but it doesn't look as nice or Pythonic as ``property`` methods.

2. At least in my case, it's easy to forget to add that last line ``Vehicle.wheels = property(Vehicle.get_wheels, Vehicle.set_wheels)``,
   especially if I'm adding another field property to the class.


The ``dataclass-wizard`` package provides a `metaclass`_ approach which
attempts to resolve this issue with minimal overhead and setup involved.

The metaclass ``property_wizard`` provides support for using field properties
with default values in dataclasses; as mentioned above, the purpose here is to
assign an initial value to the field property, if one is not explicitly passed
in via the constructor method. The metaclass also pairs well with the
``JSONSerializable`` (aliased to the ``JSONWizard``) Mixin class.

Here is our revised approach after updating the above class to use
the ``property_wizard`` metaclass:

.. code:: python3

    from dataclasses import dataclass, field
    from typing import Union

    from dataclass_wizard import property_wizard


    @dataclass
    class Vehicle(metaclass=property_wizard):

        wheels: Union[int, str] = None
        # Uncomment the field below if you want to make your IDE a bit happier.
        # Remember to set an initial value `x` as needed, via `default=x`.
        #   _wheels: int = field(init=False)

        @property
        def wheels(self) -> int:
            return self._wheels

        @wheels.setter
        def wheels(self, wheels: Union[int, str]):
            self._wheels = int(wheels)


    if __name__ == '__main__':
        v = Vehicle(wheels='3')

        print(v)
        # prints:
        #   Vehicle(wheels=3)

        # This works as expected!
        assert v.wheels == 3, 'The constructor should use our setter method'

        # So does this...
        v.wheels = '6'
        assert v.wheels == 6

        # Our `setter` method is still passed in a `property` object, but the
        # updated `setter` method (added by the metaclass) is now able to
        # automatically check for this value, and update `_wheels` with the
        # default value for the annotated type.
        v = Vehicle()

        # We've successfully managed to handle the edge case above!
        print(v)

But fortunately... there is yet an even simpler approach!

Using the `Annotated`_ type from the ``typing`` module (introduced in Python 3.9)
it is possible to set a default value for the field property in the annotation itself.
This is done by adding a ``field`` extra in the ``Annotated`` definition as
shown below; here we'll instead import the type from the ``typing-extensions``
module, just so that the code works for Python 3.6+ without issue.

.. code:: python3

    from dataclasses import dataclass, field
    from typing import Union
    from typing_extensions import Annotated

    from dataclass_wizard import property_wizard


    @dataclass
    class Vehicle(metaclass=property_wizard):

        wheels: Annotated[Union[int, str], field(default=4)]
        # Uncomment the field below if you want to make your IDE a bit happier.
        #   _wheels: int = field(init=False)

        @property
        def wheels(self) -> int:
            return self._wheels

        @wheels.setter
        def wheels(self, wheels: Union[int, str]):
            self._wheels = int(wheels)


    if __name__ == '__main__':
        v = Vehicle(wheels='3')

        print(v)
        # prints:
        #   Vehicle(wheels=3)

        # This works as expected!
        assert v.wheels == 3, 'The constructor should use our setter method'

        # So does this...
        v.wheels = '6'
        assert v.wheels == 6

        # Our `setter` method is still passed in a `property` object, but the
        # updated `setter` method (added by the metaclass) is now able to
        # automatically check for this value, and update `_wheels` with the
        # default value for the annotated type.
        v = Vehicle()

        print(v)
        # prints:
        #   Vehicle(wheels=4)

So what are the benefits of the ``Annotated`` approach
over the previous one? Well, here are a few I can think of:

* An IDE implicitly understands that a variable with a type annotation ``Annotated[T, extras...]``
  is the same as annotating it with a type ``T``, so it can offer the same
  type hints and suggestions as it normally would.

* The ``Annotated`` declaration also seems a bit more explicit to me, and other
  developers looking at the code can more clearly understand where ``wheels``
  gets its default value from.

* You won't need to play around with adding a leading underscore to the
  field property (i.e. marking it as *private*). Both the annotated type and
  an initial value is set in the annotation itself.

.. _link here: https://github.com/florimondmanca/www/issues/102#issuecomment-733947821
.. _metaclass: https://realpython.com/python-metaclasses/
.. _Annotated: https://docs.python.org/3.9/library/typing.html#typing.Annotated

More Examples
-------------
TODO.

For now, please check out the test cases `here <https://github.com/rnag/dataclass-wizard/blob/main/tests/unit/test_property_wizard.py>`_
for additional examples.


Working with Mutable Types
--------------------------

Field properties annotated with any of the known
mutable types (``list``, ``dict``, and ``set``) should have
their initial value generated via a *default factory*
rather than a constant *default* value.

`v0.5.1 <history.html#0.5.1 (2021-08-13)>`__ introduced
a bug fix for the aforementioned behavior, and also updated
the metaclass so that the ``field(default_factory=...)``
declaration on a field property is now properly used
as expected.

For field properties that are annotated as any mutable types,
the recommended approach is to pass in the ``default_factory``
argument so that an initial value can be set as expected, in the
case that no value is passed in via the constructor method.

The following example confirms that field properties with mutable
types are now set with initial values as expected:

.. code:: python3

    from collections import defaultdict
    from dataclasses import dataclass, field
    from typing import Union, List, Set, DefaultDict
    from typing_extensions import Annotated

    from dataclass_wizard import property_wizard


    @dataclass
    class Vehicle(metaclass=property_wizard):
        wheels: List[Union[int, str]]
        # Uncomment the field below if you want to make your IDE a bit happier.
        #   _wheels: List[int] = field(init=False)

        inverse_bools: Set[bool]
        # If we wanted to, we can also define this as below:
        #   inverse_bools: Annotated[Set[bool], field(default_factory=set)]

        # We need to use the `field(default_factory=...)` syntax here, because
        # otherwise the value is initialized from the no-args constructor,
        # i.e. `defaultdict()`, which is not what we want.
        inventory: Annotated[
            DefaultDict[str, List[Union[int, str]]],
            field(default_factory=lambda: defaultdict(list))
        ]

        @property
        def wheels(self) -> List[int]:
            return self._wheels

        @wheels.setter
        def wheels(self, wheels: List[Union[int, str]]):
            # Try to avoid a list comprehension, as that will defeat the point
            # of this example (as that generates a list with a new "id").
            for i, w in enumerate(wheels):
                wheels[i] = int(w)
            self._wheels = wheels

        @property
        def inverse_bools(self) -> Set[bool]:
            return self._inverse_bools

        @inverse_bools.setter
        def inverse_bools(self, bool_set: Set[bool]):
            # Again, try to avoid a set comprehension here for demo purposes.
            for b in bool_set:
                to_add = not b
                if to_add not in bool_set:
                    bool_set.discard(b)
                    bool_set.add(to_add)

            self._inverse_bools = bool_set

        @property
        def inventory(self) -> DefaultDict[str, List[Union[int, str]]]:
            return self._inventory

        @inventory.setter
        def inventory(self, inventory: DefaultDict[str, List[Union[int, str]]]):
            if 'Keys' in inventory:
                del inventory['Keys']
            self._inventory = inventory


    if __name__ == '__main__':
        # Confirm that we go through our setter methods
        v1 = Vehicle(
            wheels=['1', '2', '3'],
            inverse_bools={True, False},
            inventory=defaultdict(list, Keys=['remove me'])
        )

        v1.inventory['Spare tires'].append(2)
        print(v1)
        # prints:
        #   Vehicle(wheels=[1, 2, 3], inverse_bools={False, True}, inventory=defaultdict(<class 'list'>, {'Spare tires': [2]}))

        # Confirm that mutable (list, dict, set) types are not modified, as we will
        # use a `default factory` in this case.

        v2 = Vehicle()
        v2.wheels.append(3)
        v2.inventory['Truck'].append('fire truck')
        v2.inverse_bools.add(True)
        print(v2)
        # prints:
        #   Vehicle(wheels=[3], inverse_bools={True}, inventory=defaultdict(<class 'list'>, {'Truck': ['fire truck']}))

        v3 = Vehicle()
        v3.wheels.append(5)
        v3.inventory['Windshields'].append(3)
        v3.inverse_bools.add(False)
        print(v3)
        # prints:
        #   Vehicle(wheels=[5], inverse_bools={False}, inventory=defaultdict(<class 'list'>, {'Windshields': [3]}))

        # Confirm that mutable type fields are not shared between dataclass instances.

        assert v1.wheels == [1, 2, 3]
        assert v1.inverse_bools == {False, True}
        assert v1.inventory == {'Spare tires': [2]}

        assert v2.wheels == [3]
        assert v2.inverse_bools == {True}
        assert v2.inventory == {'Truck': ['fire truck']}

        assert v3.wheels == [5]
        assert v3.inverse_bools == {False}
        assert v3.inventory == {'Windshields': [3]}
