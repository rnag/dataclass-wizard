Common Use Cases
================

Skip the ``__str__``
--------------------

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


Extending from ``Meta``
-----------------------

There are a couple well-known use cases where we might want to customize
behavior of how fields are transformed during the JSON load and dump
process (for example, to *camel case* or *snake case*), or when we want
``datetime`` and ``date`` objects to be converted to an epoch timestamp
(as an ``int``) instead of the default behavior, which converts these
objects to their ISO 8601 string representation via
`isoformat <https://docs.python.org/3/library/datetime.html#datetime.datetime.isoformat>`__.

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
            marshal_date_time_as = DateTimeTo.TIMESTAMP
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
