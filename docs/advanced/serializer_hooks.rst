Serializer Hooks
================

    Note: To customize the load or dump process for annotated types
    instead of individual fields, please see the `Type
    Hooks <#type-hooks>`__ section.

You can optionally add hooks that are run before a JSON string or a
Python ``dict`` object is loaded to a dataclass instance, or before the
dataclass instance is converted back to a Python ``dict`` object.

To customize the load process, simply implement the ``__post_init__``
method which will be run by the ``dataclass`` decorator.

To customize the dump process, simply extend from ``DumpMixin`` and
override the ``__pre_as_dict__`` method which will be called whenever
you invoke the ``to_dict`` or ``to_json`` methods. Please note that this
will pass in the original dataclass instance, so updating any values
will affect the fields of the underlying dataclass (**this might change
in a future revision**).

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
