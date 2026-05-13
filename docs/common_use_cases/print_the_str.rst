Print the :meth:`__str__`
=========================

.. note::
    It is now easier to view ``DEBUG``-level log messages from this library! Check out
    the `Easier Debug Mode <easier_debug_mode.html>`__ section.

You might want an opt-in ``__str__`` method on classes that inherit from
``DataclassWizard``. This opt-in method will format the dataclass
instance as a prettified JSON string, for example whenever ``str(obj)``
or ``print(obj)`` is called.

If you want to opt in to this ``__str__`` method,
you can pass ``str=True`` as shown below:


.. code:: python3

    from dataclass_wizard import DataclassWizard


    class MyClass(DataclassWizard, str=True):
        my_str: str = 'hello world'
        my_int: int = 2


    c = MyClass()
    print(c)
    # prints:
    #   {'my_int': 2, 'my_str': 'hello world'}
