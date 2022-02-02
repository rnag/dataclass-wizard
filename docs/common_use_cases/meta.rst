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
defining an inner class which extends from ``JSONSerializable.Meta`` (or the
aliased name ``JSONWizard.Meta``), as shown below. The name of the inner class
does not matter, but for demo purposes it's named the same as the base class here.

.. note::
  As of *v0.18.0*, the Meta config for the main dataclass will "cascade down"
  and be merged with the Meta config (if specified) of each nested dataclass. To
  disable this behavior, you can pass in ``recursive=False`` to the Meta config.

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

            # True to enable Debug mode for additional (more verbose) log output.
            #
            # For example, a message is logged whenever an unknown JSON key is
            # encountered when `from_dict` or `from_json` is called.
            #
            # This also results in more helpful messages during error handling, which
            # can be useful when debugging the cause when values are an invalid type
            # (i.e. they don't match the annotation for the field) when unmarshalling
            # a JSON object to a dataclass instance.
            #
            # Note there is a minor performance impact when DEBUG mode is enabled.
            debug_enabled = True

            # When enabled, a specified Meta config for the main dataclass (i.e. the
            # class on which `from_dict` and `to_dict` is called) will cascade down
            # and be merged with the Meta config for each *nested* dataclass; note
            # that during a merge, priority is given to the Meta config specified on
            # each class.
            #
            # The default behavior is True, so the Meta config (if provided) will
            # apply in a recursive manner.
            recursive = True

            # True to raise an class:`UnknownJSONKey` when an unmapped JSON key is
            # encountered when `from_dict` or `from_json` is called; an unknown key is
            # one that does not have a known mapping to a dataclass field.
            #
            # The default is to only log a "warning" for such cases, which is visible
            # when `debug_enabled` is true and logging is properly configured.
            raise_on_unknown_json_key = False

            # A customized mapping of JSON keys to dataclass fields, that is used
            # whenever `from_dict` or `from_json` is called.
            #
            # Note: this is in addition to the implicit field transformations, like
            #   "myStr" -> "my_str"
            #
            # If the reverse mapping is also desired (i.e. dataclass field to JSON
            # key), then specify the "__all__" key as a truthy value. If multiple JSON
            # keys are specified for a dataclass field, only the first one provided is
            # used in this case.
            json_key_to_field = {}

            # How should :class:`date` and :class:`datetime` objects be serialized
            # when converted to a Python dictionary object or a JSON string.
            marshal_date_time_as = DateTimeTo.TIMESTAMP

            # How JSON keys should be transformed to dataclass fields.
            key_transform_with_load = LetterCase.PASCAL

            # How dataclass fields should be transformed to JSON keys.
            key_transform_with_dump = LetterCase.SNAKE

            # The field name that identifies the tag for a class.
            #
            # When set to a value, a '__tag__' field will be populated in the
            # dictionary object in the dump (serialization) process. When loading
            # (or de-serializing) a dictionary object, the '__tag__' field will be
            # used to load the corresponding dataclass, assuming the dataclass field
            # is properly annotated as a Union type, ex.:
            #   my_data: Union[Data1, Data2, Data3]
            tag = ''

            # The dictionary key that identifies the tag field for a class. This is
            # only set when the `tag` field or the `auto_assign_tags` flag is enabled
            # in the `Meta` config for a dataclass.
            #
            # Defaults to '__tag__' if not specified.
            tag_key = ''

            # Auto-assign the class name as a dictionary "tag" key, for any dataclass
            # fields which are in a `Union` declaration, ex.:
            #   my_data: Union[Data1, Data2, Data3]
            auto_assign_tags = False

            # Determines whether we should we skip / omit fields with default values
            # (based on the `default` or `default_factory` argument specified for
            # the :func:`dataclasses.field`) in the serialization process.
            skip_defaults = True

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

Any :class:`Meta` settings only affect a class model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All attributes set in the ``Meta`` class will only apply to the
class model that ``from_dict`` or ``to_dict`` runs on; that is,
it will apply recursively to any nested dataclasses by default, and
merge with the ``Meta`` config (if specified) for each class. Note that
you can pass ``recursive=False`` in the ``Meta`` config, if you only want
it to apply to the main dataclass, and not to any nested dataclasses
in the model.

When the ``Meta`` config for the main dataclass is merged with any nested
dataclass, priority is given to any fields explicitly set in the ``Meta``
config for each class. In addition, the following attributes in each class's
``Meta`` are excluded from a merge:

- :attr:`recursive`
- :attr:`json_key_to_field`
- :attr:`tag`

Also, note that a ``Meta`` config should not affect the load/dump process
for other, unrelated dataclasses. Though if you do desire this behavior, see
the :ref:`Global Meta Settings<Global Meta>` section below.

Here's a quick example to confirm this behavior:

.. code:: python3

    import logging
    from dataclasses import dataclass
    from datetime import date

    from dataclass_wizard import JSONWizard

    # Sets up logging, so that library logs are visible in the console.
    logging.basicConfig(level='INFO')


    @dataclass
    class FirstClass(JSONWizard):
        class _(JSONWizard.Meta):
            debug_enabled = True
            marshal_date_time_as = 'Timestamp'
            key_transform_with_load = 'PASCAL'
            key_transform_with_dump = 'SNAKE'

        MyStr: str
        MyNestedClass: 'MyNestedClass'


    @dataclass
    class MyNestedClass:
        MyDate: date


    @dataclass
    class SecondClass(JSONWizard):
        # If `SecondClass` were to define it's own `Meta` class, those changes
        # would only be applied to `SecondClass` and any nested dataclass
        # by default.
        # class _(JSONWizard.Meta):
        #     key_transform_with_dump = 'PASCAL'

        my_str: str
        my_date: date


    def main():
        data = {'my_str': 'test', 'myNestedClass': {'myDATE': '2010-12-30'}}

        c1 = FirstClass.from_dict(data)
        print(repr(c1))
        # prints:
        #   FirstClass(MyStr='test', MyNestedClass=MyNestedClass(MyDate=datetime.date(2010, 12, 30)))

        string = c1.to_json()
        print(string)
        # prints:
        #   {"my_str": "test", "my_nested_class": {"my_date": 1293685200}}

        data2 = {'my_str': 'test', 'myDATE': '2022-01-15'}

        c2 = SecondClass.from_dict(data2)
        print(repr(c2))
        # prints:
        #   SecondClass(my_str='test', my_date=datetime.date(2022, 1, 15))

        string = c2.to_json()
        print(string)
        # prints:
        #   {"myStr": "test", "myDate": "2022-01-15"}


    if __name__ == '__main__':
        main()

.. _Global Meta:

Global :class:`Meta` settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In case you want global ``Meta`` settings that will apply to
all dataclasses which sub-class from ``JSONWizard``, you
can simply define ``JSONWizard.Meta`` as an outer class
as shown in the example below.

.. attention::
   Although not recommended, a global ``Meta`` class should resolve the issue.
   Note that this is a specialized use case and should be considered carefully.

   This may also have unforeseen consequences - for example, if your application
   depends on another library that uses the ``JSONWizard`` Mixin class from the
   Dataclass Wizard library, then that library will be likewise affected by any
   global ``Meta`` values that are set.

.. code:: python3

    import logging
    from dataclasses import dataclass
    from datetime import date

    from dataclass_wizard import JSONWizard
    from dataclass_wizard.enums import DateTimeTo


    # Sets up logging, so that library logs are visible in the console.
    logging.basicConfig(level='INFO')


    class GlobalJSONMeta(JSONWizard.Meta):
        """
        Global settings for the JSON load/dump process, that should apply to
        *all* subclasses of `JSONWizard`.

        Note: it does not matter where this class is defined, as long as it's
        declared before any methods in `JSONWizard` are called.
        """

        debug_enabled = True
        marshal_date_time_as = DateTimeTo.TIMESTAMP
        key_transform_with_load = 'PASCAL'
        key_transform_with_dump = 'SNAKE'


    @dataclass
    class FirstClass(JSONWizard):

        MyStr: str
        MyDate: date


    @dataclass
    class SecondClass(JSONWizard):

        # If `SecondClass` were to define it's own `Meta` class, those changes
        # will effectively override the global `Meta` settings below, but only
        # for `SecondClass` itself and no other dataclass.
        # class _(JSONWizard.Meta):
        #     key_transform_with_dump = 'CAMEL'

        AnotherStr: str
        OtherDate: date


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

