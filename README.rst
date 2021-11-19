================
Dataclass Wizard
================


.. image:: https://img.shields.io/pypi/v/dataclass-wizard.svg
        :target: https://pypi.org/project/dataclass-wizard

.. image:: https://img.shields.io/pypi/pyversions/dataclass-wizard.svg
        :target: https://pypi.org/project/dataclass-wizard

.. image:: https://github.com/rnag/dataclass-wizard/actions/workflows/dev.yml/badge.svg
        :target: https://github.com/rnag/dataclass-wizard/actions/workflows/dev.yml

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
-  *JSON to Dataclass generation*: construct a dataclass schema with a JSON file
   or string input.

Usage
-----

Using the built-in JSON marshalling support for dataclasses:

    Note: The following example should work in **Python 3.7+** with the included ``__future__``
    import.

.. code:: python3

    from __future__ import annotations  # This can be removed in Python 3.10+

    from dataclasses import dataclass, field

    from dataclass_wizard import JSONWizard


    @dataclass
    class MyClass(JSONWizard):
        my_str: str | None
        is_active_tuple: tuple[bool, ...]
        list_of_int: list[int] = field(default_factory=list)


    string = """
    {
      "my_str": 20,
      "ListOfInt": ["1", "2", 3],
      "isActiveTuple": ["true", "false", 1, false]
    }
    """

    # De-serialize the JSON string into a `MyClass` object.
    c = MyClass.from_json(string)

    print(repr(c))
    # prints:
    #   MyClass(my_str='20', is_active_tuple=(True, False, True, False), list_of_int=[1, 2, 3])

    print(c.to_json())
    # prints:
    #   {"myStr": "20", "isActiveTuple": [true, false, true, false], "listOfInt": [1, 2, 3]}

    # True
    assert c == c.from_dict(c.to_dict())

... and with the ``property_wizard``, which provides support for
`field properties`_ with default values in dataclasses:

.. code:: python3

    from __future__ import annotations  # This can be removed in Python 3.10+

    from dataclasses import dataclass, field
    from typing_extensions import Annotated

    from dataclass_wizard import property_wizard


    @dataclass
    class Vehicle(metaclass=property_wizard):
        # Note: The example below uses the default value from the `field` extra in
        # the `Annotated` definition; if `wheels` were annotated as `int | str`,
        # it would default to 0, because `int` appears as the first type argument.
        #
        # Any right-hand value assigned to `wheels` is ignored as it is simply
        # re-declared by the property; here it is simply omitted for brevity.
        wheels: Annotated[int | str, field(default=4)]

        # This is a shorthand version of the above; here an IDE suggests
        # `_wheels` as a keyword argument to the constructor method, though
        # it will actually be named as `wheels`.
        # _wheels: int | str = 4

        @property
        def wheels(self) -> int:
            return self._wheels

        @wheels.setter
        def wheels(self, wheels: int | str):
            self._wheels = int(wheels)


    if __name__ == '__main__':
        v = Vehicle()
        print(v)
        # prints:
        #   Vehicle(wheels=4)

        v = Vehicle(wheels=3)
        print(v)

        v = Vehicle('6')
        print(v)

        assert v.wheels == 6, 'The constructor should use our setter method'

        # Confirm that we go through our setter method
        v.wheels = '123'
        assert v.wheels == 123

... or generate a dataclass schema for JSON input, via the `wiz-cli`_ tool:

.. code:: shell

    $ echo '{"myFloat": "1.23", "Products": [{"created_at": "2021-11-17"}]}' | wiz gs - my_file

    # Contents of my_file.py
    from dataclasses import dataclass
    from datetime import date
    from typing import List, Union

    from dataclass_wizard import JSONWizard


    @dataclass
    class Data(JSONWizard):
        """
        Data dataclass

        """
        my_float: Union[float, str]
        products: List['Product']


    @dataclass
    class Product:
        """
        Product dataclass

        """
        created_at: date


Installing Dataclass Wizard and Supported Versions
--------------------------------------------------
The Dataclass Wizard library is available on PyPI:

.. code-block:: shell

    $ python -m pip install dataclass-wizard

The ``dataclass-wizard`` library officially supports **Python 3.6** or higher.


Supported Types
---------------

The Dataclass Wizard library provides inherent support for standard Python collections
such as ``list``, ``dict`` and ``set``, as well as most Generics from the typing
module, such as ``Union`` and ``Any``. Other commonly used types such as ``Enum``,
``defaultdict``, and date and time objects such as ``datetime`` are also natively
supported.

For a complete list of the supported Python types, including info on the
load/dump process for special types, check out the `Supported Types`_ section
in the docs.

JSON Marshalling
----------------

``JSONSerializable`` (aliased to ``JSONWizard``) is a Mixin_ class which
provides the following helper methods that are useful for serializing (and loading)
a dataclass instance to/from JSON, as defined by the ``AbstractJSONWizard``
interface.

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
   * - ``list_to_json``
     - `string = Product.list_to_json(list_of_item)`
     - Converts a list of dataclass instances to a JSON string
       representation.

Additionally, it adds a default ``__str__`` method to subclasses, which will
pretty print the JSON representation of an object; this is quite useful for
debugging purposes. Whenever you invoke ``print(obj)`` or ``str(obj)``, for
example, it'll call this method which will format the dataclass object as
a prettified JSON string. If you prefer a ``__str__`` method to not be
added, you can pass in ``str=False`` when extending from the Mixin class
as mentioned `here <https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/skip_the_str.html>`_.

Note that the ``__repr__`` method, which is implemented by the
``dataclass`` decorator, is also available. To invoke the Python object
representation of the dataclass instance, you can instead use
``repr(obj)`` or ``f'{obj!r}'``.

To mark a dataclass as being JSON serializable (and
de-serializable), simply sub-class from ``JSONSerializable`` as shown
below. You can also extend from the aliased name ``JSONWizard``, if you
prefer to use that instead.

Check out a `more complete example`_ of using the ``JSONSerializable``
Mixin class.

No Inheritance Needed
---------------------

It is important to note that the main purpose of sub-classing from
``JSONWizard`` Mixin class is to provide helper methods like ``from_dict``
and ``to_dict``, which makes it much more convenient and easier to load or
dump your data class from and to JSON.

That is, it's meant to *complement* the usage of the ``dataclass`` decorator,
rather than to serve as a drop-in replacement for data classes, or to provide type
validation for example; there are already excellent libraries like `pydantic`_ that
provide these features if so desired.

However, there may be use cases where we prefer to do away with the class
inheritance model introduced by the Mixin class. In the interests of convenience
and also so that data classes can be used *as is*, the Dataclass
Wizard library provides the helper functions ``fromlist`` and ``fromdict``
for de-serialization, and ``asdict`` for serialization. These functions also
work recursively, so there is full support for nested dataclasses -- just as with
the class inheritance approach.

Here is an example to demonstrate the usage of these helper functions:

.. note::
  As of *v0.18.0*, the Meta config for the main dataclass will cascade down
  and be merged with the Meta config (if specified) of each nested dataclass. To
  disable this behavior, you can pass in ``recursive=False`` to the Meta config.

.. code:: python3

    from __future__ import annotations

    from dataclasses import dataclass, field
    from datetime import datetime, date

    from dataclass_wizard import fromdict, asdict, DumpMeta


    @dataclass
    class A:
        created_at: datetime
        list_of_b: list[B] = field(default_factory=list)


    @dataclass
    class B:
        my_status: int | str
        my_date: date | None = None


    source_dict = {'createdAt': '2010-06-10 15:50:00Z',
                   'List-Of-B': [
                       {'MyStatus': '200', 'my_date': '2021-12-31'}
                   ]}

    # De-serialize the JSON dictionary object into an `A` instance.
    a = fromdict(A, source_dict)

    print(repr(a))
    # A(created_at=datetime.datetime(2010, 6, 10, 15, 50, tzinfo=datetime.timezone.utc),
    #   list_of_b=[B(my_status='200', my_date=datetime.date(2021, 12, 31))])

    # Set an optional dump config for the main dataclass, for example one which
    # converts converts date and datetime objects to a unix timestamp (as an int)
    #
    # Note that `recursive=True` is the default, so this Meta config will be
    # merged with the Meta config (if specified) of each nested dataclass.
    DumpMeta(marshal_date_time_as='TIMESTAMP',
             key_transform='SNAKE',
             # Finally, apply the Meta config to the main dataclass.
             ).bind_to(A)

    # Serialize the `A` instance to a Python dict object.
    json_dict = asdict(a)

    expected_dict = {'created_at': 1276185000, 'list_of_b': [{'my_status': '200', 'my_date': 1640926800}]}

    print(json_dict)
    # Assert that we get the expected dictionary object.
    assert json_dict == expected_dict

Custom Key Mappings
-------------------

If you ever find the need to add a `custom mapping`_ of a JSON key to a dataclass
field (or vice versa), the helper function ``json_field`` -- which can be
considered an alias to ``dataclasses.field()`` -- is one approach that can
resolve this.

Example below:

.. code:: python3

    from dataclasses import dataclass

    from dataclass_wizard import JSONSerializable, json_field


    @dataclass
    class MyClass(JSONSerializable):

        my_str: str = json_field('myString1', all=True)


    # De-serialize a dictionary object with the newly mapped JSON key.
    d = {'myString1': 'Testing'}
    c = MyClass.from_dict(d)

    print(repr(c))
    # prints:
    #   MyClass(my_str='Testing')

    # Assert we get the same dictionary object when serializing the instance.
    assert c.to_dict() == d

Extending from ``Meta``
-----------------------

Looking to change how ``date`` and ``datetime`` objects are serialized to JSON? Or
prefer that field names appear in *snake case* when a dataclass instance is serialized?

The inner ``Meta`` class allows easy configuration of such settings, as
shown below; and as a nice bonus, IDEs should be able to assist with code completion
along the way.

.. note::
  As of *v0.18.0*, the Meta config for the main dataclass will cascade down
  and be merged with the Meta config (if specified) of each nested dataclass. To
  disable this behavior, you can pass in ``recursive=False`` to the Meta config.

.. code:: python3

    from dataclasses import dataclass
    from datetime import date

    from dataclass_wizard import JSONWizard
    from dataclass_wizard.enums import DateTimeTo


    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            marshal_date_time_as = DateTimeTo.TIMESTAMP
            key_transform_with_dump = 'SNAKE'

        my_str: str
        my_date: date


    data = {'my_str': 'test', 'myDATE': '2010-12-30'}

    c = MyClass.from_dict(data)

    print(repr(c))
    # prints:
    #   MyClass(my_str='test', my_date=datetime.date(2010, 12, 30))

    string = c.to_json()
    print(string)
    # prints:
    #   {"my_str": "test", "my_date": 1293685200}

Other Uses for ``Meta``
~~~~~~~~~~~~~~~~~~~~~~~

Here are a few additional use cases for the inner ``Meta`` class. Note that
a full list of available settings can be found in the `Meta`_ section in the docs.

Debug Mode
##########

Enables additional (more verbose) log output. For example, a message can be
logged whenever an unknown JSON key is encountered when
``from_dict`` or ``from_json`` is called.

This also results in more helpful error messages during the JSON load
(de-serialization) process, such as when values are an invalid type --
i.e. they don't match the annotation for the field. This can be particularly
useful for debugging purposes.

Handle Unknown JSON Keys
########################

The default behavior is to ignore any unknown or extraneous JSON keys that are
encountered when ``from_dict`` or ``from_json`` is called, and emit a "warning"
which is visible when *debug* mode is enabled (and logging is properly configured).
An unknown key is one that does not have a known mapping to a dataclass field.

However, we can also raise an error in such cases if desired. The below
example demonstrates a use case where we want to raise an error when
an unknown JSON key is encountered in the  *load* (de-serialization) process.

.. code:: python3

    import logging
    from dataclasses import dataclass

    from dataclass_wizard import JSONWizard
    from dataclass_wizard.errors import UnknownJSONKey


    # Sets up application logging if we haven't already done so
    logging.basicConfig(level='INFO')


    @dataclass
    class Container(JSONWizard):

        class _(JSONWizard.Meta):
            # True to enable Debug mode for additional (more verbose) log output.
            debug_enabled = True
            # True to raise an class:`UnknownJSONKey` when an unmapped JSON key is
            # encountered when `from_dict` or `from_json` is called. Note that by
            # default, this is also recursively applied to any nested dataclasses.
            raise_on_unknown_json_key = True

        element: 'MyElement'


    @dataclass
    class MyElement:
        my_str: str
        my_float: float


    d = {
        'element': {
            'myStr': 'string',
            'my_float': '1.23',
            # Notice how this key is not mapped to a known dataclass field!
            'my_bool': 'Testing'
        }
    }

    # Try to de-serialize the dictionary object into a `MyClass` object.
    try:
        c = Container.from_dict(d)
    except UnknownJSONKey as e:
        print('Received error:', type(e).__name__)
        print('Class:', e.class_name)
        print('Unknown JSON key:', e.json_key)
        print('JSON object:', e.obj)
        print('Known Fields:', e.fields)
    else:
        print('Successfully de-serialized the JSON object.')
        print(repr(c))

Serialization Options
---------------------

The following parameters can be used to fine-tune and control how the serialization of a
dataclass instance to a Python ``dict`` object or JSON string is handled.

Skip Defaults
~~~~~~~~~~~~~

A common use case is skipping fields with default values - based on the ``default``
or ``default_factory`` argument to ``dataclasses.field`` - in the serialization
process.

The attribute ``skip_defaults`` in the inner ``Meta`` class can be enabled, to exclude
such field values from serialization.The ``to_dict`` method (or the ``asdict`` helper
function) can also be passed an ``skip_defaults`` argument, which should have the same
result. An example of both these approaches is shown below.

.. code:: python3

    from collections import defaultdict
    from dataclasses import field, dataclass
    from typing import DefaultDict, List

    from dataclass_wizard import JSONWizard


    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            skip_defaults = True

        my_str: str
        other_str: str = 'any value'
        optional_str: str = None
        my_list: List[str] = field(default_factory=list)
        my_dict: DefaultDict[str, List[float]] = field(
            default_factory=lambda: defaultdict(list))


    print('-- Load (Deserialize)')
    c = MyClass('abc')
    print(f'Instance: {c!r}')

    print('-- Dump (Serialize)')
    string = c.to_json()
    print(string)

    assert string == '{"myStr": "abc"}'

    print('-- Dump (with `skip_defaults=False`)')
    print(c.to_dict(skip_defaults=False))

Exclude Fields
~~~~~~~~~~~~~~

You can also exclude specific dataclass fields (and their values) from the serialization
process. There are two approaches that can be used for this purpose:

* The argument ``dump=False`` can be passed in to the ``json_key`` and ``json_field``
  helper functions. Note that this is a more permanent option, as opposed to the one
  below.

* The ``to_dict`` method (or the ``asdict`` helper function ) can be passed
  an ``exclude`` argument, containing a list of one or more dataclass field names
  to exclude from the serialization process.

Additionally, here is an example to demonstrate usage of both these approaches:

.. code:: python3

    from dataclasses import dataclass
    from typing import Annotated

    from dataclass_wizard import JSONWizard, json_key, json_field


    @dataclass
    class MyClass(JSONWizard):

        my_str: str
        my_int: int
        other_str: Annotated[str, json_key('AnotherStr', dump=False)]
        my_bool: bool = json_field('TestBool', dump=False)


    data = {'MyStr': 'my string',
            'myInt': 1,
            'AnotherStr': 'testing 123',
            'TestBool': True}

    print('-- From Dict')
    c = MyClass.from_dict(data)
    print(f'Instance: {c!r}')

    # dynamically exclude the `my_int` field from serialization
    additional_exclude = ('my_int',)

    print('-- To Dict')
    out_dict = c.to_dict(exclude=additional_exclude)
    print(out_dict)

    assert out_dict == {'myStr': 'my string'}

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

Contributing
------------

Contributions are welcome! Open a pull request to fix a bug, or `open an issue`_
to discuss a new feature or change.

Check out the `Contributing`_ section in the docs for more info.

Credits
-------

This package was created with Cookiecutter_ and the `rnag/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/cookiecutter/cookiecutter
.. _`rnag/cookiecutter-pypackage`: https://github.com/rnag/cookiecutter-pypackage
.. _`Contributing`: https://dataclass-wizard.readthedocs.io/en/latest/contributing.html
.. _`open an issue`: https://github.com/rnag/dataclass-wizard/issues
.. _`Supported Types`: https://dataclass-wizard.readthedocs.io/en/latest/overview.html#supported-types
.. _`Mixin`: https://stackoverflow.com/a/547714/10237506
.. _`Meta`: https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/meta.html
.. _`pydantic`: https://pydantic-docs.helpmanual.io/
.. _`Using Field Properties`: https://dataclass-wizard.readthedocs.io/en/latest/using_field_properties.html
.. _`field properties`: https://dataclass-wizard.readthedocs.io/en/latest/using_field_properties.html
.. _`custom mapping`: https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/custom_key_mappings.html
.. _`wiz-cli`: https://dataclass-wizard.readthedocs.io/en/latest/wiz_cli.html
.. _`key limitations`: https://florimond.dev/en/posts/2018/10/reconciling-dataclasses-and-properties-in-python/
.. _`more complete example`: https://dataclass-wizard.readthedocs.io/en/latest/examples.html#a-more-complete-example
