Extending from :class:`Meta`
============================

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

Any :class:`Meta` settings only affect the Outer Class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All attributes set in the ``Meta`` class will only apply to the
outer dataclass, and should not affect the load/dump process for
other dataclasses. However if you do desire this behavior, see the
:ref:`Global Meta Settings<Global Meta>` section below.

Here's a quick example to confirm this behavior:

.. code:: python3

    import logging
    from dataclasses import dataclass
    from datetime import date

    from dataclass_wizard import JSONSerializable

    # Sets up logging, so that library logs are visible in the console.
    logging.basicConfig(level='INFO')


    @dataclass
    class FirstClass(JSONSerializable):

        class _(JSONSerializable.Meta):
            debug_enabled = True
            marshal_date_time_as = 'Timestamp'
            key_transform_with_load = 'Pascal'
            key_transform_with_dump = 'SNAKE'

        MyStr: str
        MyDate: date


    @dataclass
    class SecondClass(JSONSerializable):

        # If `SecondClass` were to define it's own `Meta` class, those changes
        # would only be applied to `SecondClass`, and no other dataclass.
        # class _(JSONSerializable.Meta):
        #     key_transform_with_dump = 'PASCAL'

        my_str: str
        my_date: date


    def main():

        data = {'my_str': 'test', 'myDATE': '2010-12-30'}

        c1 = FirstClass.from_dict(data)
        print(repr(c1))
        # prints:
        #   FirstClass(MyStr='test', MyDate=datetime.date(2010, 12, 30))

        string = c1.to_json()
        print(string)
        # prints:
        #   {"my_str": "test", "my_date": 1293685200}

        c2 = SecondClass.from_dict(data)
        print(repr(c2))
        # prints:
        #   SecondClass(my_str='test', my_date=datetime.date(2010, 12, 30))

        string = c2.to_json()
        print(string)
        # prints:
        #   {"myStr": "test", "myDate": "2010-12-30"}


    if __name__ == '__main__':
        main()

.. _Global Meta:

Global :class:`Meta` settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In case you want global ``Meta`` settings that will apply to
all dataclasses which sub-class from ``JSONSerializable``, you
can simply define ``JSONSerializable.Meta`` as an outer class
as shown in the example below.

.. code:: python3

    import logging
    from dataclasses import dataclass
    from datetime import date

    from dataclass_wizard import JSONSerializable

    # Sets up logging, so that library logs are visible in the console.
    logging.basicConfig(level='INFO')


    @dataclass
    class FirstClass(JSONSerializable):

        MyStr: str
        MyDate: date


    @dataclass
    class SecondClass(JSONSerializable):

        # If `SecondClass` were to define it's own `Meta` class, those changes
        # will effectively override the global `Meta` settings below, but only
        # for `SecondClass` itself and no other dataclass.
        # class _(JSONSerializable.Meta):
        #     key_transform_with_dump = 'CAMEL'

        AnotherStr: str
        OtherDate: date


    class GlobalJSONMeta(JSONSerializable.Meta):
        """
        Global settings for the JSON load/dump process, that should apply to
        *all* subclasses of `JSONSerializable`.

        Note: it does not matter where this class is defined, as long as it's
        declared before any methods in `JSONSerializable` are called.
        """

        debug_enabled = True
        marshal_date_time_as = 'Timestamp'
        key_transform_with_load = 'Pascal'
        key_transform_with_dump = 'SNAKE'


    def main():

        data1 = {'my_str': 'test', 'myDATE': '2010-12-30'}

        c1 = FirstClass.from_dict(data1)
        print(repr(c1))
        # prints:
        #   FirstClass(MyStr='test', MyDate=datetime.date(2010, 12, 30))

        string = c1.to_json()
        print(string)
        # prints:
        #   {"my_str": "test", "my_date": 1293685200}

        data2 = {'another_str': 'test', 'OtherDate': '2010-12-30'}

        c2 = SecondClass.from_dict(data2)
        print(repr(c2))
        # prints:
        #   SecondClass(AnotherStr='test', OtherDate=datetime.date(2010, 12, 30))

        string = c2.to_json()
        print(string)
        # prints:
        #   {"another_str": "test", "other_date": 1293685200}


    if __name__ == '__main__':
        main()

