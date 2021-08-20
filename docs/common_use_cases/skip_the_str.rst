Skip the :meth:`__str__`
========================

The ``JSONSerializable`` class implements a default
``__str__`` method if a sub-class doesn't already define
this method. This method will format the dataclass
instance as a prettified JSON string, for example whenever ``str(obj)``
or ``print(obj)`` is called.

If you want to opt out of this default ``__str__`` method,
you can pass ``str=False`` as shown below:


.. code:: python3

    from dataclasses import dataclass

    from dataclass_wizard import JSONSerializable


    @dataclass
    class MyClass(JSONSerializable, str=False):
        my_str: str = 'hello world'
        my_int: int = 2


    c = MyClass()
    print(c)
    # prints the same as `repr(c)`:
    #   MyClass(my_str='hello world', my_int=2)
