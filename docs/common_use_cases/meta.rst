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

    from dataclass_wizard import JSONWizard, IS, NE
    from dataclass_wizard.enums import DateTimeTo, LetterCase

    # (Optional) sets up logging, so that library logs are visible in the console.
    logging.basicConfig(level='INFO')


    @dataclass
    class MyClass(JSONWizard):

        class Meta(JSONWizard.Meta):

            # Enable Debug mode for more verbose log output.
            #
            # This setting can be a `bool`, `int`, or `str`:
            # - `True` enables debug mode with default verbosity.
            # - A `str` or `int` specifies the minimum log level (e.g., 'DEBUG', 10).
            #
            # Debug mode provides additional helpful log messages, including:
            # - Logging unknown JSON keys encountered during `from_dict` or `from_json`.
            # - Detailed error messages for invalid types during unmarshalling.
            #
            # Note: Enabling Debug mode may have a minor performance impact.
            #
            # @deprecated and will be removed in V1 - Use `v1_debug` instead.
            debug_enabled: bool | int | str = logging.DEBUG

            # When enabled, a specified Meta config for the main dataclass (i.e. the
            # class on which `from_dict` and `to_dict` is called) will cascade down
            # and be merged with the Meta config for each *nested* dataclass; note
            # that during a merge, priority is given to the Meta config specified on
            # each class.
            #
            # The default behavior is True, so the Meta config (if provided) will
            # apply in a recursive manner.
            recursive: bool = True

            # True to support cyclic or self-referential dataclasses. For example,
            # the type of a dataclass field in class `A` refers to `A` itself.
            #
            # See https://github.com/rnag/dataclass-wizard/issues/62 for more details.
            recursive_classes: bool = False

            # True to raise an class:`UnknownJSONKey` when an unmapped JSON key is
            # encountered when `from_dict` or `from_json` is called; an unknown key is
            # one that does not have a known mapping to a dataclass field.
            #
            # The default is to only log a "warning" for such cases, which is visible
            # when `v1_debug` is true and logging is properly configured.
            raise_on_unknown_json_key: bool = False

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
            json_key_to_field: dict[str, str] = None

            # How should :class:`time` and :class:`datetime` objects be serialized
            # when converted to a Python dictionary object or a JSON string.
            marshal_date_time_as: 'DateTimeTo | str' = None

            # How JSON keys should be transformed to dataclass fields.
            key_transform_with_load: 'LetterCase | str' = LetterCase.PASCAL

            # How dataclass fields should be transformed to JSON keys.
            key_transform_with_dump: 'LetterCase | str' = LetterCase.SNAKE

            # The field name that identifies the tag for a class.
            #
            # When set to a value, an :attr:`TAG` field will be populated in the
            # dictionary object in the dump (serialization) process. When loading
            # (or de-serializing) a dictionary object, the :attr:`TAG` field will be
            # used to load the corresponding dataclass, assuming the dataclass field
            # is properly annotated as a Union type, ex.:
            #   my_data: Union[Data1, Data2, Data3]
            tag: str = ''

            # The dictionary key that identifies the tag field for a class. This is
            # only set when the `tag` field or the `auto_assign_tags` flag is enabled
            # in the `Meta` config for a dataclass.
            #
            # Defaults to '__tag__' if not specified.
            tag_key: str = ''

            # Auto-assign the class name as a dictionary "tag" key, for any dataclass
            # fields which are in a `Union` declaration, ex.:
            #   my_data: Union[Data1, Data2, Data3]
            auto_assign_tags: bool = False

            # Determines whether we should we skip / omit fields with default values
            # (based on the `default` or `default_factory` argument specified for
            # the :func:`dataclasses.field`) in the serialization process.
            skip_defaults: bool = True

            # Determines the :class:`Condition` to skip / omit dataclass
            # fields in the serialization process.
            skip_if: 'Condition' = IS(None)

            # Determines the condition to skip / omit fields with default values
            # (based on the `default` or `default_factory` argument specified for
            # the :func:`dataclasses.field`) in the serialization process.
            skip_defaults_if: 'Condition' = NE('value')

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

:class:`Meta` fields for **v1 Opt-in**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following :class:`Meta` attributes only apply with **v1 Opt-in**. See the `Field Guide to V1 Opt-in`_
for more details.

.. _`Field Guide to V1 Opt-in`: https://github.com/rnag/dataclass-wizard/wiki/Field-Guide-to-V1-Opt%E2%80%90in

.. code:: python3

    # Enable opt-in to the "experimental" major release `v1` feature.
    # This feature offers optimized performance for de/serialization.
    # Defaults to False.
    v1: bool = True

    # Enable Debug mode for more verbose log output.
    #
    # This setting can be a `bool`, `int`, or `str`:
    # - `True` enables debug mode with default verbosity.
    # - A `str` or `int` specifies the minimum log level (e.g., 'DEBUG', 10).
    #
    # Debug mode provides additional helpful log messages, including:
    # - Logging unknown JSON keys encountered during `from_dict` or `from_json`.
    # - Detailed error messages for invalid types during unmarshalling.
    #
    # Note: Enabling Debug mode may have a minor performance impact.
    v1_debug: 'bool | int | str' = False

    # Custom load hooks for extending type support in the v1 engine.
    #
    # Mapping: {Type -> hook}
    #
    # A hook must accept either:
    #   - one positional argument (runtime hook): value -> object
    #   - two positional arguments (v1 hook): (TypeInfo, Extras) -> str | TypeInfo
    #
    # The hook is invoked when loading a value annotated with the given type.
    v1_type_to_load_hook: V1TypeToHook = None

    # Custom dump hooks for extending type support in the v1 engine.
    #
    # Mapping: {Type -> hook}
    #
    # A hook must accept either:
    #   - one positional argument (runtime hook): object -> JSON-serializable value
    #   - two positional arguments (v1 hook): (TypeInfo, Extras) -> str | TypeInfo
    #
    # The hook is invoked when dumping a value whose runtime type matches
    # the given type.
    v1_type_to_dump_hook: V1TypeToHook = None

    # ``v1_pre_decoder``: Optional hook called before ``v1`` type loading.
    # Receives the container type plus (cls, TypeInfo, Extras) and may return a
    # transformed ``TypeInfo`` (e.g., wrapped in a function which decodes
    # JSON/delimited strings into list/dict for env loading). Returning the
    # input value leaves behavior unchanged.
    #
    #  Pre-decoder signature:
    #   (cls, container_tp, tp, extras) -> new_tp
    v1_pre_decoder: V1PreDecoder | None = None

    # Specifies the letter case to use for JSON keys when both loading and dumping.
    #
    # This is a convenience setting that applies the same key casing rule to
    # both deserialization (load) and serialization (dump).
    #
    # If set, it is used as the default for both `v1_load_case` and
    # `v1_dump_case`, unless either is explicitly specified.
    #
    # The setting is case-insensitive and supports shorthand assignment,
    # such as using the string 'C' instead of 'CAMEL'.
    v1_case: 'KeyCase | str' = None

    # Specifies the letter case used to match JSON keys when mapping them
    # to dataclass fields during deserialization.
    #
    # This setting determines how dataclass field names are transformed
    # when looking up corresponding keys in the input JSON object. It does
    # not affect keys in `TypedDict` or `NamedTuple` subclasses.
    #
    # By default, JSON keys are assumed to be in `snake_case`, and fields
    # are matched directly without transformation.
    #
    # The setting is case-insensitive and supports shorthand assignment,
    # such as using the string 'C' instead of 'CAMEL'.
    #
    # If set to `A` or `AUTO`, all supported key casing transforms are
    # attempted at runtime, and the resolved transform is cached for
    # subsequent lookups.
    #
    # If unset, this value defaults to `v1_case` when provided.
    v1_load_case: 'KeyCase | str' = None

    # Specifies the letter case used for JSON keys during serialization.
    #
    # This setting determines how dataclass field names are transformed
    # when generating keys in the output JSON object.
    #
    # By default, field names are emitted in `snake_case`.
    #
    # The setting is case-insensitive and supports shorthand assignment,
    # such as using the string 'P' instead of 'PASCAL'.
    #
    # If unset, this value defaults to `v1_case` when provided.
    v1_dump_case: 'KeyCase | str' = None

    # A custom mapping of dataclass fields to their JSON aliases (keys).
    #
    # Values may be a single alias string or a sequence of alias strings.
    #
    # - During deserialization (load), any listed alias for a field is accepted.
    # - During serialization (dump), the first alias is used by default.
    #
    # This mapping overrides default key casing and implicit field-to-key
    # transformations (e.g., "my_field" → "myField") for the affected fields.
    #
    # This setting applies to both load and dump unless explicitly overridden
    # by `v1_field_to_alias_load` or `v1_field_to_alias_dump`.
    v1_field_to_alias: 'Mapping[str, str | Sequence[str]]' = None

    # A custom mapping of dataclass fields to their JSON aliases (keys) used
    # during deserialization only.
    #
    # Values may be a single alias string or a sequence of alias strings.
    # Any listed alias is accepted when mapping input JSON keys to
    # dataclass fields.
    #
    # When set, this mapping overrides `v1_field_to_alias` for load behavior
    # only.
    v1_field_to_alias_load: 'Mapping[str, str | Sequence[str]]' = None

    # A custom mapping of dataclass fields to their JSON aliases (keys) used
    # during serialization only.
    #
    # Values may be a single alias string or a sequence of alias strings.
    # When a sequence is provided, the first alias is used as the output key.
    #
    # When set, this mapping overrides `v1_field_to_alias` for dump behavior
    # only.
    v1_field_to_alias_dump: 'Mapping[str, str | Sequence[str]]' = None

    # Defines the action to take when an unknown JSON key is encountered during
    # `from_dict` or `from_json` calls. An unknown key is one that does not map
    # to any dataclass field.
    #
    # Valid options are:
    # - `"ignore"` (default): Silently ignore unknown keys.
    # - `"warn"`: Log a warning for each unknown key. Requires `v1_debug`
    #   to be `True` and properly configured logging.
    # - `"raise"`: Raise an `UnknownKeyError` for the first unknown key encountered.
    v1_on_unknown_key: KeyAction = None

    # Unsafe: Enables parsing of dataclasses in unions without requiring
    # the presence of a `tag_key`, i.e., a dictionary key identifying the
    # tag field in the input. Defaults to False.
    v1_unsafe_parse_dataclass_in_union: bool = False

    # Specifies how :class:`datetime` (and :class:`time`, where applicable)
    # objects are serialized during output.
    #
    # This setting controls how temporal values are emitted when converting
    # a dataclass to a Python dictionary (`to_dict`) or a JSON string
    # (`to_json`). It applies to serialization only and does not affect
    # deserialization.
    #
    # By default, values are serialized using ISO 8601 string format.
    #
    # Supported values are defined by :class:`DateTimeTo`.
    v1_dump_date_time_as: 'V1DateTimeTo | str' = None

    # Specifies the timezone to assume for naive :class:`datetime` values
    # during serialization.
    #
    # By default, naive datetimes are rejected to avoid ambiguous or
    # environment-dependent behavior.
    #
    # When set, naive datetimes are interpreted as being in the specified
    # timezone before conversion to a UTC epoch timestamp.
    #
    # Common usage:
    #     v1_assume_naive_datetime_tz = timezone.utc
    #
    # This setting applies to serialization only and does not affect
    # deserialization.
    v1_assume_naive_datetime_tz: 'tzinfo | None' = None

    # Controls how `typing.NamedTuple` and `collections.namedtuple`
    # fields are loaded and serialized.
    #
    # - False (DEFAULT): load from list/tuple and serialize
    #                     as a positional list.
    # - True: load from mapping and serialize as a dict
    #           keyed by field name.
    #
    # In strict mode, inputs that do not match the selected mode
    # raise TypeError.
    #
    # Note:
    #   This option enforces strict shape matching for performance reasons.
    v1_namedtuple_as_dict: bool = False

    # If True (default: False), ``None`` is coerced to an empty string (``""``)
    # when loading ``str`` fields.
    #
    # When False, ``None`` is coerced using ``str(value)``, so ``None`` becomes
    # the literal string ``'None'`` for ``str`` fields.
    #
    # For ``Optional[str]`` fields, ``None`` is preserved by default.
    v1_coerce_none_to_empty_str: bool = False

    # Controls how leaf (non-recursive) types are detected during serialization.
    #
    # - "exact" (DEFAULT): only exact built-in leaf types are treated as leaf values.
    # - "issubclass": subclasses of leaf types are also treated as leaf values.
    #
    # Leaf types are returned without recursive traversal. Bytes are still
    # handled separately according to their serialization rules.
    #
    # Note:
    #     The default "exact" mode avoids treating third-party scalar-like
    #     objects (e.g. NumPy scalars) as built-in leaf types.
    v1_leaf_handling: Literal['exact', 'issubclass'] = None

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

