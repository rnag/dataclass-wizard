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

For full documentation, please see below:

* https://dataclass-wizard.readthedocs.io

Features
--------
Here are the supported features that ``dataclass-wizard`` currently provides:

-  *JSON (de)serialization*: marshal dataclasses to/from JSON and Python
   ``dict`` objects.
-  *Properties with defaults*: support for using properties with default
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
properties with default values in dataclasses:

.. code:: python3

    from dataclasses import dataclass
    from typing import Union

    from dataclass_wizard import property_wizard


    @dataclass
    class Vehicle(metaclass=property_wizard):
        _wheels: Union[int, str] = 4

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
        #   Vehicle(wheels=4)

        # My IDE does complain on this part - it also suggests `_wheels` as a
        # keyword argument to the constructor, and that's expected, but it will
        # error if you try it that way.
        v = Vehicle(wheels=3)
        print(v)
        # prints:
        #   Vehicle(wheels=3)

        # Passing positional arguments seems to be preferable as the IDE does not
        # complain here.
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


JSON Serializable
-----------------

``JSONSerializable`` is a
`Mixin <https://stackoverflow.com/a/547714/10237506>`__ class which
provides the following helper methods that are useful for loading (and
serializing) a dataclass to JSON, as defined by the
``AbstractJSONWizard`` interface.

-  ``from_json`` - Converts a JSON string to an instance of the
   dataclass, or a list of the dataclass instances.

-  ``from_list`` - Converts a Python ``list`` object to a list of the
   dataclass instances.

-  ``from_dict`` - Converts a Python ``dict`` object to an instance of
   the dataclass.

-  ``to_dict`` - Converts the dataclass instance to a Python dictionary
   object that is JSON serializable.

-  ``to_json`` - Converts the dataclass instance to a JSON ``string``
   representation.

Additionally, it implements a ``__str__`` method, which will pretty
print the JSON representation of an object; this is quite useful for
debugging purposes. Whenever you invoke ``print(obj)`` or ``str(obj)``,
for example, it'll invoke this method which will pretty print the
dataclass object.

Note that the ``__repr__`` method, which is implemented by the
``dataclass`` decorator, is still available. To invoke the Python object
representation of the dataclass instance, you can instead use
``repr(obj)`` or ``f'{obj!r}'``.

To mark a dataclass instance as being JSON serializable (and
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
                'birthdate': '1971-11-05 05:10:59Z',
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
    #               age=45, birthdate=datetime.datetime(1971, 11, 5, 5, 10, 59, tzinfo=datetime.timezone.utc),
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
    #           "birthdate": "1971-11-05T05:10:59Z",
    #           "gender": "F",
    #           "occupation": "Dentist",
    #           "details": null
    #         }
    #       ],
    #       "isEnabled": true
    #     }

Properties with Default Values
------------------------------

The Python ``dataclass`` library currently has some `key
issues <https://florimond.dev/en/posts/2018/10/reconciling-dataclasses-and-properties-in-python/>`__
with how it currently handles properties and default values.

The ``dataclass-wizard`` library natively provides support for using
properties with default values in dataclasses. To use it, simply import
the ``property_wizard`` helper function, and add it as a metaclass on
any dataclass. The metaclass also pairs well with the
``JSONSerializable`` mixin class. Note that this allows initial values
for properties to be specified via the constructor, if needed.

Examples
~~~~~~~~

TODO

Advanced Usage
--------------

Common Use Cases
~~~~~~~~~~~~~~~~

There are a couple well-known use cases where we might want to customize
behavior of how fields are transformed during the JSON load and dump
process (for example, to *camel case* or *snake case*), or when we want
``datetime`` and ``date`` objects to be converted to an epoch timestamp
(as an ``int``) instead of the default behavior, which converts these
objects to their ISO 8601 string representation via
```isoformat`` <https://docs.python.org/3/library/datetime.html#datetime.datetime.isoformat>`__.

Such common behaviors can be easily specified on a per-class basis by
defining an inner class which extends from ``JSONSerializable.Meta``, as
shown below. The name of the inner class does not matter, but for demo
purposes it's named the same as the base class here.

.. code:: python3

    import logging
    from dataclasses import dataclass
    from datetime import date

    from dataclass_wizard import JSONSerializable
    from dataclass_wizard.enums import DateTimeTo, LetterCase

    # Sets up logging, so that library logs are visible in the console.
    logging.basicConfig(level='INFO')


    @dataclass
    class MyClass(JSONSerializable):

        class Meta(JSONSerializable.Meta):
            # Enable better, more detailed error messages that may be helpful for
            # debugging when values are an invalid type (i.e. they don't match
            # the annotation for the field) when marshaling dataclass objects.
            # Note there is a minor performance impact when DEBUG mode is enabled.
            debug_enabled = True
            # How should :class:`date` and :class:`datetime` objects be serialized
            # when converted to a Python dictionary object or a JSON string.
            date_time_with_dump = DateTimeTo.TIMESTAMP
            # How JSON keys should be transformed to dataclass fields.
            key_transform_with_load = LetterCase.PASCAL
            # How dataclass fields should be transformed to JSON keys.
            key_transform_with_dump = LetterCase.SNAKE

        MyStr: str
        MyDate: date


    data = {'my_str': 'test', 'myDATE': '2010-12-30'}

    c = MyClass.from_dict(data)

    print(repr(c))
    # prints:
    #   MyClass(MyStr='test', MyDate=datetime.date(2010, 12, 30))
    string = c.to_json()

    print(string)
    # prints:
    #   {"my_str": "test", "my_date": 1293685200}

Note that the ``key_transform_...`` attributes only apply to the field
names that are defined in the dataclass; other keys such as the ones for
``TypedDict`` or ``NamedTuple`` sub-classes won't be similarly
transformed. If you need similar behavior for any of the ``typing``
sub-classes mentioned, simply convert them to dataclasses and the key
transform should then apply for those fields.

Serializer Hooks
~~~~~~~~~~~~~~~~

    Note: To customize the load or dump process for annotated types
    instead of individual fields, please see the `Type
    Hooks <#type-hooks>`__ section below.

You can optionally add hooks that are run before a JSON string or a
Python ``dict`` object is loaded to a dataclass instance, or before the
dataclass instance is converted back to a Python ``dict`` object.

To customize the load process, simply implement the ``__post_init__``
method which will be run by the ``dataclass`` decorator.

To customize the dump process, simply extend from ``DumpMixin`` and
override the ``__pre_as_dict__`` method which will be called whenever
you invoke the ``to_dict`` or ``to_json`` methods. Please note that this
will pass in the original dataclass instance, so updating any values
will affect the fields of the underlying dataclass.

A simple example to illustrate both approaches is shown below:

.. code:: python3

    from dataclasses import dataclass
    from dataclass_wizard import JSONSerializable, DumpMixin


    @dataclass
    class MyClass(JSONSerializable, DumpMixin):
        my_str: str
        my_int: int

        def __post_init__(self):
            self.my_str = self.my_str.title()

        def __pre_as_dict__(self):
            self.my_str = self.my_str.swapcase()


    data = {"my_str": "my string", "myInt": "10"}

    c = MyClass.from_dict(data)
    print(repr(c))
    # prints:
    #   MyClass(my_str='My String', my_int=10)

    string = c.to_json()
    print(string)
    # prints:
    #   {"myStr": "mY sTRING", "myInt": 10}

Type Hooks
~~~~~~~~~~

Sometimes you might want to customize the load and dump process for
(annotated) variable types, rather than for specific dataclass fields.
Type hooks are very useful and will let you do exactly that.

If you want to customize the load process for any type, extend from
``LoadMixin`` and override the ``load_to_...`` methods. To instead
customize the dump process for a type, extend from ``DumpMixin`` and
override the ``dump_with_...`` methods.

For instance, the default load process for ``Enum`` types is to look
them up by value, and similarly convert them back to strings using the
``value`` field. Suppose that you want to load ``Enum`` types using the
``name`` field instead.

The below example will do exactly that: it will convert using the *Enum*
``name`` field when ``from_dict`` is called, and use the default
approach to convert back using the *Enum* ``value`` field when
``to_dict`` is called; it additionally customizes the dump process for
strings, so they are converted to all uppercase when ``to_dict`` or
``to_json`` is called.

.. code:: python3

    from dataclasses import dataclass
    from enum import Enum
    from typing import Union, AnyStr, Type

    from dataclass_wizard import JSONSerializable, DumpMixin, LoadMixin
    from dataclass_wizard.type_defs import N


    @dataclass
    class MyClass(JSONSerializable, LoadMixin, DumpMixin):

        my_str: str
        my_enum: 'MyEnum'

        def load_to_enum(o: Union[AnyStr, N], base_type: Type[Enum]) -> Enum:
            return base_type[o.replace(' ', '_')]

        def dump_with_str(o: str, *_):
            return o.upper()


    class MyEnum(Enum):
        NAME_1 = 'one'
        NAME_2 = 'two'


    data = {"my_str": "my string", "my_enum": "NAME 1"}

    c = MyClass.from_dict(data)
    print(repr(c))
    # prints:
    #   MyClass(my_str='my string', my_enum=<MyEnum.NAME_1: 'one'>)

    string = c.to_json()
    print(string)
    # prints:
    #   {"myStr": "MY STRING", "myEnum": "one"}


Credits
-------

This package was created with Cookiecutter_ and the `rnag/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/cookiecutter/cookiecutter
.. _`rnag/cookiecutter-pypackage`: https://github.com/rnag/cookiecutter-pypackage
