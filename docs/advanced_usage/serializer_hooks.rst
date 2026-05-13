Serializer Hooks
================

.. note::
    To customize the load or dump process for annotated types
    instead of individual fields, please see the `Type
    Hooks <type_hooks.html>`__ section.

You can optionally add hooks that are run before a JSON string or a
Python ``dict`` object is loaded to a dataclass instance, or before the
dataclass instance is converted back to a Python ``dict`` object.

To customize the load process:

* To pre-process data before ``from_dict`` is called, simply
  implement a ``_pre_from_dict`` method which will be called
  whenever you invoke the ``from_dict`` or ``from_json`` methods.
  Please note that this will pass in the original ``dict`` object,
  so updating any values will affect data in the underlying ``dict``
  (**this might change in a future revision**).
* To post-process data, *after* a dataclass instance is de-serialized,
  simply implement the ``__post_init__`` method which will be run
  by the ``dataclass`` decorator.

To customize the dump process, simply implement
a ``_pre_to_dict`` method which will be called
whenever you invoke the ``to_dict`` or ``to_json``
methods. Please note that this will pass in the
original dataclass instance, so updating any values
will affect the fields of the underlying dataclass
(**this might change in a future revision**).

A simple example to illustrate both approaches is shown below:

.. code:: python3

    from dataclasses import dataclass
    from typing import Any

    from dataclass_wizard import JSONWizard


    @dataclass
    class MyClass(JSONWizard):
        my_str: str
        my_int: int
        my_bool: bool = False

        def __post_init__(self):
            self.my_str = self.my_str.title()
            self.my_int *= 2

        @classmethod
        def _pre_from_dict(cls, o: dict[str, Any]) -> dict[str, Any]:
            # o = o.copy()  # Copying the `dict` object is optional
            o['my_bool'] = True  # Adds a new key/value pair
            return o

        def _pre_to_dict(self):
            self.my_str = self.my_str.swapcase()
            return self


    data = {"my_str": "my string", "my_int": "10"}

    c = MyClass.from_dict(data)
    print(c)
    # > MyClass(my_str='My String', my_int=20, my_bool=True)

    string = c.to_json()
    print(string)
    # prints:
    #   {"my_str": "mY sTRING", "my_int": 20, "my_bool": true}
