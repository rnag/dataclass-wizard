================
Dataclass Wizard
================


.. image:: https://img.shields.io/pypi/v/dataclass-wizard.svg
        :target: https://pypi.org/project/dataclass-wizard

.. image:: https://img.shields.io/pypi/pyversions/dataclass-wizard.svg
        :target: https://pypi.org/project/dataclass-wizard

.. image:: https://travis-ci.com/rnag/dataclass-wizard.svg?branch=main
        :target: https://travis-ci.com/rnag/dataclass-wizard

.. image:: https://readthedocs.org/projects/dataclass-wizard/badge/?version=latest
        :target: https://dataclass-wizard.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status


.. image:: https://pyup.io/repos/github/rnag/dataclass-wizard/shield.svg
     :target: https://pyup.io/repos/github/rnag/dataclass-wizard/
     :alt: Updates



This library provides a set of simple, yet elegant *wizarding* tools for
interacting with the Python ``dataclasses`` module.

Full documentation is at:

* https://dataclass-wizard.readthedocs.io

Features
--------
Here are the supported features that ``dataclass-wizard`` currently provides:

-  *JSON (de)serialization*: marshal dataclasses to/from JSON and Python
   ``dict`` objects.
-  *Field properties*: support for using properties with default
   values in dataclass instances.

Usage
-----

Using the built-in JSON marshalling support for dataclasses:

.. code:: python3

    from dataclasses import dataclass, field
    from typing import Optional, List

    from dataclass_wizard import JSONSerializable


    @dataclass
    class MyClass(JSONSerializable):

        my_str: Optional[str]
        list_of_int: List[int] = field(default_factory=list)
        is_active: bool = False


    string = """{"my_str": 20, "ListOfInt": ["1", "2", 3], "isActive": "true"}"""
    c = MyClass.from_json(string)
    print(repr(c))
    # prints:
    #   MySampleClass(my_str='20', list_of_int=[1, 2, 3], is_active=True)

    print(c.to_json())
    # prints:
    #   {"myStr": "20", "listOfInt": [1, 2, 3], "isActive": true}

... and with the ``property_wizard``, which provides supports for
field properties with default values in dataclasses:

.. code:: python3

    from dataclasses import dataclass
    from typing import Union

    from dataclass_wizard import property_wizard


    @dataclass
    class Vehicle(metaclass=property_wizard):

        # Note: The example below uses the default value for the annotated type
        # (0 here, because `int` appears first). The right-hand value assigned to
        # `wheels` is ignored, as it is simply re-declared by the property. To
        # specify a default value of 4, comment out the `wheels` field and
        # replace it with the `_wheels` declaration below.
        #   _wheels: Union[int, str] = 4
        wheels: Union[int, str] = 0

        @property
        def wheels(self) -> int:
            return self._wheels

        @wheels.setter
        def wheels(self, wheels: Union[int, str]):
            self._wheels = int(wheels)


    if __name__ == '__main__':
        v = Vehicle()
        print(v)
        # prints:
        #   Vehicle(wheels=0)

        v = Vehicle(wheels=3)
        print(v)
        # prints:
        #   Vehicle(wheels=3)

        v = Vehicle('6')
        print(v)
        # prints:
        #   Vehicle(wheels=6)

        assert v.wheels == 6, 'The constructor should use our setter method'

        # Confirm that we go through our setter method
        v.wheels = '123'
        assert v.wheels == 123


Installing Dataclass Wizard and Supported Versions
--------------------------------------------------
The Dataclass Wizard library is available on PyPI:

.. code-block:: shell

    $ python -m pip install dataclass-wizard

The ``dataclass-wizard`` library officially supports **Python 3.6** or higher.


JSON Marshalling
----------------

``JSONSerializable`` is a Mixin_ class which provides the following helper
methods that are useful for serializing (and loading) a dataclass instance
to/from JSON, as defined by the ``AbstractJSONWizard`` interface.

.. list-table::
   :widths: 10 40 35
   :header-rows: 1

   * - Method
     - Example
     - Description
   * - ``from_json``
     - `item = Product.from_json(string)`
     - Converts a JSON string to an instance of the
       dataclass, or a list of the dataclass instances.
   * - ``from_list``
     - `list_of_item = Product.from_list(l)`
     - Converts a Python ``list`` object to a list of the
       dataclass instances.
   * - ``from_dict``
     - `item = Product.from_dict(d)`
     - Converts a Python ``dict`` object to an instance
       of the dataclass.
   * - ``to_dict``
     - `d = item.to_dict()`
     - Converts the dataclass instance to a Python ``dict``
       object that is JSON serializable.
   * - ``to_json``
     - `string = item.to_json()`
     - Converts the dataclass instance to a JSON string
       representation.

Additionally, it adds a default ``__str__`` method to subclasses, which will
pretty print the JSON representation of an object; this is quite useful for
debugging purposes. Whenever you invoke ``print(obj)`` or ``str(obj)``, for
example, it'll call this method which will format the dataclass object as
a prettified JSON string. If you prefer a ``__str__`` method to not be
added, you can pass in ``str=False`` when extending from the Mixin class
as mentioned `here <https://dataclass-wizard.readthedocs.io/en/latest/advanced/common_use_cases.html#skip-the-str>`_.

Note that the ``__repr__`` method, which is implemented by the
``dataclass`` decorator, is also available. To invoke the Python object
representation of the dataclass instance, you can instead use
``repr(obj)`` or ``f'{obj!r}'``.

To mark a dataclass as being JSON serializable (and
de-serializable), simply sub-class from ``JSONSerializable`` as shown
below. You can also extend from the class alias ``JSONWizard``, if you
prefer to use that instead.

Here is a (more) complete example of using the ``JSONSerializable``
Mixin class:

.. code:: python3

    from dataclasses import dataclass
    from datetime import datetime
    from typing import Optional, List, Literal, Union, Dict, Any, NamedTuple

    from dataclass_wizard import JSONSerializable


    @dataclass
    class MyTestClass(JSONSerializable):
        my_ledger: Dict[str, Any]
        the_answer_to_life: Optional[int]
        people: List['Person']
        is_enabled: bool = True


    @dataclass
    class Person:
        name: 'Name'
        age: int
        birthdate: datetime
        gender: Literal['M', 'F', 'N/A']
        occupation: Union[str, List[str]]
        details: Optional[str] = None


    class Name(NamedTuple):
        """A person's name"""
        first: str
        last: str
        salutation: Optional[Literal['Mr.', 'Mrs.', 'Ms.', 'Dr.']] = 'Mr.'


    data = {
        'myLedger': {
            'Day 1': 'some details',
            'Day 17': ['a', 'sample', 'list']
        },
        'theAnswerTOLife': '42',
        'People': [
            {
                'name': ('Roberto', 'Fuirron'),
                'age': 21,
                'birthdate': '1950-02-28T17:35:20Z',
                'gender': 'M',
                'occupation': ['sailor', 'fisher'],
                'details': 'My sample details here'
            },
            {
                'name': ('Janice', 'Darr', 'Dr.'),
                'age': 45,
                'birthdate': '1971-11-05 05:10:59',
                'gender': 'F',
                'occupation': 'Dentist'
            }
        ]
    }

    c = MyTestClass.from_dict(data)

    print(repr(c))
    # prints the following result on a single line:
    #   MyTestClass(
    #       my_ledger={'Day 1': 'some details', 'Day 17': ['a', 'sample', 'list']},
    #       the_answer_to_life=42,
    #       people=[
    #           Person(
    #               name=Name(first='Roberto', last='Fuirron', salutation='Mr.'),
    #               age=21, birthdate=datetime.datetime(1950, 2, 28, 17, 35, 20, tzinfo=datetime.timezone.utc),
    #               gender='M', occupation=['sailor', 'fisher'], details='My sample details here'
    #           ),
    #           Person(
    #               name=Name(first='Janice', last='Darr', salutation='Dr.'),
    #               age=45, birthdate=datetime.datetime(1971, 11, 5, 5, 10, 59),
    #               gender='F', occupation='Dentist', details=None
    #           )
    #       ], is_enabled=True)

    # calling `print` on the object invokes the `__str__` method, which will
    # pretty-print the JSON representation of the object by default. You can
    # also call the `to_json` method to print the JSON string on a single line.

    print(c)
    # prints:
    #     {
    #       "myLedger": {
    #         "Day 1": "some details",
    #         "Day 17": [
    #           "a",
    #           "sample",
    #           "list"
    #         ]
    #       },
    #       "theAnswerToLife": 42,
    #       "people": [
    #         {
    #           "name": [
    #             "Roberto",
    #             "Fuirron",
    #             "Mr."
    #           ],
    #           "age": 21,
    #           "birthdate": "1950-02-28T17:35:20Z",
    #           "gender": "M",
    #           "occupation": [
    #             "sailor",
    #             "fisher"
    #           ],
    #           "details": "My sample details here"
    #         },
    #         {
    #           "name": [
    #             "Janice",
    #             "Darr",
    #             "Dr."
    #           ],
    #           "age": 45,
    #           "birthdate": "1971-11-05T05:10:59",
    #           "gender": "F",
    #           "occupation": "Dentist",
    #           "details": null
    #         }
    #       ],
    #       "isEnabled": true
    #     }

Field Properties
----------------

The Python ``dataclasses`` library has some `key limitations`_
with how it currently handles properties and default values.

The ``dataclass-wizard`` package natively provides support for using
field properties with default values in dataclasses. The main use case
here is to assign an initial value to the field property, if one is not
explicitly passed in via the constructor method.

To use it, simply import
the ``property_wizard`` helper function, and add it as a metaclass on
any dataclass where you would benefit from using field properties with
default values. The metaclass also pairs well with the ``JSONSerializable``
mixin class.

For more examples and important how-to's on properties with default values,
refer to the `Using Field Properties`_ section in the documentation.

Credits
-------

This package was created with Cookiecutter_ and the `rnag/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/cookiecutter/cookiecutter
.. _`rnag/cookiecutter-pypackage`: https://github.com/rnag/cookiecutter-pypackage
.. _`Mixin`: https://stackoverflow.com/a/547714/10237506
.. _`Using Field Properties`: https://dataclass-wizard.readthedocs.io/en/latest/using_field_properties.html
.. _`key limitations`: https://florimond.dev/en/posts/2018/10/reconciling-dataclasses-and-properties-in-python/
