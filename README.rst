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
-  *JSON to Dataclass*: generate a dataclass schema for a JSON file or string input.

Usage
-----

Using the built-in JSON marshalling support for dataclasses:

.. code:: python3

    from dataclasses import dataclass, field
    from typing import Optional, List, Tuple

    from dataclass_wizard import JSONWizard


    @dataclass
    class MyClass(JSONWizard):
        my_str: Optional[str]
        is_active_tuple: Tuple[bool, ...]
        list_of_int: List[int] = field(default_factory=list)


    string = """
    {
      "my_str": 20,
      "ListOfInt": ["1", "2", 3],
      "isActiveTuple": ["true", "false", 1, false]
    }
    """

    c = MyClass.from_json(string)
    print(repr(c))
    # prints:
    #   MyClass(my_str='20', is_active_tuple=(True, False, True, False), list_of_int=[1, 2, 3])

    print(c.to_json())
    # prints:
    #   {"myStr": "20", "isActiveTuple": [true, false, true, false], "listOfInt": [1, 2, 3]}

... and with the ``property_wizard``, which provides support for
`field properties`_ with default values in dataclasses:

.. code:: python3

    from dataclasses import dataclass, field
    from typing import Union
    from typing_extensions import Annotated

    from dataclass_wizard import property_wizard


    @dataclass
    class Vehicle(metaclass=property_wizard):

        # Note: The example below uses the default value from the `field` extra in
        # the `Annotated` definition; if `wheels` were annotated as a `Union` type,
        # it would default to 0, because `int` appears as the first type argument.
        #
        # Any right-hand value assigned to `wheels` is ignored as it is simply
        # re-declared by the property; here it is simply omitted for brevity.
        wheels: Annotated[Union[int, str], field(default=4)]

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

... or generate a dataclass schema for JSON input, via the `wiz-cli`_ tool:

.. code:: shell

    $ echo '{"myFloat": "1.23", "created_at": "2021-11-17"}' | wiz gs - my_file

    # Contents of my_file.py
    from dataclasses import dataclass
    from datetime import date
    from typing import Union


    @dataclass
    class Data:
        """
        Data dataclass

        """
        my_float: Union[float, str]
        created_at: date

Installing Dataclass Wizard and Supported Versions
--------------------------------------------------
The Dataclass Wizard library is available on PyPI:

.. code-block:: shell

    $ python -m pip install dataclass-wizard

The ``dataclass-wizard`` library officially supports **Python 3.6** or higher.


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
.. _`field properties`: https://dataclass-wizard.readthedocs.io/en/latest/using_field_properties.html
.. _`wiz-cli`: https://dataclass-wizard.readthedocs.io/en/latest/wiz_cli.html
.. _`key limitations`: https://florimond.dev/en/posts/2018/10/reconciling-dataclasses-and-properties-in-python/
.. _`more complete example`: https://dataclass-wizard.readthedocs.io/en/latest/examples.html#a-more-complete-example
