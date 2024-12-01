================
Dataclass Wizard
================

Full documentation is available at `Read The Docs`_. (`Installation`_)

.. image:: https://img.shields.io/pypi/v/dataclass-wizard.svg
        :target: https://pypi.org/project/dataclass-wizard

.. image:: https://img.shields.io/conda/vn/conda-forge/dataclass-wizard.svg
        :target: https://anaconda.org/conda-forge/dataclass-wizard

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



**Dataclass Wizard** offers simple, elegant, *wizarding* 🪄 tools for
interacting with Python's ``dataclasses``.

    It excels at ⚡️ lightning-fast de/serialization, effortlessly
    converting dataclass instances to/from JSON -- perfect for
    *nested dataclass* models!

-------------------

**Behold, the power of the Dataclass Wizard**::

    >>> from __future__ import annotations
    >>> from dataclasses import dataclass, field
    >>> from dataclass_wizard import JSONWizard
    ...
    >>> @dataclass
    ... class MyClass(JSONWizard):
    ...     my_str: str | None
    ...     is_active_tuple: tuple[bool, ...]
    ...     list_of_int: list[int] = field(default_factory=list)
    ...
    >>> string = """
    ... {
    ...   "my_str": 20,
    ...   "ListOfInt": ["1", "2", 3],
    ...   "isActiveTuple": ["true", false, 1]
    ... }
    ... """
    ...
    >>> instance = MyClass.from_json(string)
    >>> instance
    MyClass(my_str='20', is_active_tuple=(True, False, True), list_of_int=[1, 2, 3])
    >>> instance.to_json()
    '{"myStr": "20", "isActiveTuple": [true, false, true], "listOfInt": [1, 2, 3]}'
    >>> instance == MyClass.from_dict(instance.to_dict())
    True

---

.. contents:: Contents
   :depth: 1
   :local:
   :backlinks: none


Installation
------------

Dataclass Wizard is available on `PyPI`_. Install with ``pip``:

.. code-block:: console

    $ pip install dataclass-wizard

Also available on `conda`_ via `conda-forge`_. Install with ``conda``:

.. code-block:: console

    $ conda install dataclass-wizard -c conda-forge

This library supports **Python 3.9** or higher.

.. _PyPI: https://pypi.org/project/dataclass-wizard/
.. _conda: https://anaconda.org/conda-forge/dataclass-wizard
.. _conda-forge: https://conda-forge.org/

Features
--------

Unlock the full potential of your `dataclasses`_ with these key features:

- *Flexible (de)serialization*: Marshal dataclasses to/from JSON, TOML, YAML, or ``dict`` with ease.
- *Environment magic*: Map env vars and ``dotenv`` files to strongly-typed class fields effortlessly.
- *Field properties made simple*: Add properties with default values to your dataclasses.
- *JSON-to-Dataclass wizardry*: Auto-generate a dataclass schema from any JSON file or string instantly.

Wizard Mixins
-------------

In addition to ``JSONWizard``, these handy Mixin_ classes simplify your workflow:

* `EnvWizard`_ — Seamlessly load env variables and ``.env`` files into typed schemas. Supports secret files (file names as keys).
* `JSONPyWizard`_ — A ``JSONWizard`` helper to skip *camelCase* and preserve keys as-is.
* `JSONListWizard`_ — Extends ``JSONWizard`` to return `Container`_ objects instead of *lists* when possible.
* `JSONFileWizard`_ — Effortlessly convert dataclass instances from/to JSON files on your local drive.
* `TOMLWizard`_ — Easily map dataclass instances to/from TOML format.
* `YAMLWizard`_ — Instantly convert dataclass instances to/from YAML, using the default ``PyYAML`` parser.

Supported Types
---------------

The Dataclass Wizard library natively supports standard Python
collections like ``list``, ``dict``, and ``set``, along with
popular `typing`_ module Generics such as ``Union`` and ``Any``.
Additionally, it handles commonly used types like ``Enum``,
``defaultdict``, and date/time objects (e.g., ``datetime``)
with ease.

For a detailed list of supported types and insights into the
load/dump process for special types, visit the
`Supported Types`_ section of the docs.

Usage and Examples
------------------

.. rubric:: Seamless JSON De/Serialization with ``JSONWizard``

.. code-block:: python3

    from __future__ import annotations  # Optional in Python 3.10+

    from dataclasses import dataclass, field
    from enum import Enum
    from datetime import date

    from dataclass_wizard import JSONWizard


    @dataclass
    class Data(JSONWizard):
        # Use Meta to customize JSON de/serialization
        class _(JSONWizard.Meta):
            key_transform_with_dump = 'LISP'  # Transform keys to LISP-case during dump

        a_sample_bool: bool
        values: list[Inner] = field(default_factory=list)


    @dataclass
    class Inner:
        # Nested data with optional enums and typed dictionaries
        vehicle: Car | None
        my_dates: dict[int, date]


    class Car(Enum):
        SEDAN = 'BMW Coupe'
        SUV = 'Toyota 4Runner'


    # Input JSON-like dictionary
    my_dict = {
        'values': [{'vehicle': 'Toyota 4Runner', 'My-Dates': {'123': '2023-01-31'}}],
        'aSampleBool': 'TRUE'
    }

    # Deserialize into strongly-typed dataclass instances
    data = Data.from_dict(my_dict)
    print((v := data.values[0]).vehicle)  # Prints: <Car.SUV: 'Toyota 4Runner'>
    assert v.my_dates[123] == date(2023, 1, 31)  # > True

    # Serialize back into pretty-printed JSON
    print(data.to_json(indent=2))

.. rubric:: Map Environment Variables with ``EnvWizard``

Easily map environment variables to Python dataclasses:

.. code-block:: python3

    import os
    from dataclass_wizard import EnvWizard

    os.environ.update({
        'APP_NAME': 'My App',
        'MAX_CONNECTIONS': '10',
        'DEBUG_MODE': 'true'
    })

    class AppConfig(EnvWizard):
        app_name: str
        max_connections: int
        debug_mode: bool

    config = AppConfig()
    print(config.app_name)    # My App
    print(config.debug_mode)  # True

📖 See more `on EnvWizard`_ in the full documentation.

.. rubric:: Dataclass Properties with ``property_wizard``

Add field properties to your dataclasses with default values using ``property_wizard``:

.. code-block:: python3

    from __future__ import annotations  # This can be removed in Python 3.10+

    from dataclasses import dataclass, field
    from typing_extensions import Annotated

    from dataclass_wizard import property_wizard


    @dataclass
    class Vehicle(metaclass=property_wizard):
        wheels: Annotated[int | str, field(default=4)]
        # or, alternatively:
        #   _wheels: int | str = 4

        @property
        def wheels(self) -> int:
            return self._wheels

        @wheels.setter
        def wheels(self, value: int | str):
            self._wheels = int(value)


    v = Vehicle()
    print(v.wheels)  # 4
    v.wheels = '6'
    print(v.wheels)  # 6

    assert v.wheels == 6, 'Setter correctly handles type conversion'

📖 For a deeper dive, visit the documentation on `field properties`_.

.. rubric:: Generate Dataclass Schemas with CLI

Quickly generate Python dataclasses from JSON input using the ``wiz-cli`` tool:

.. code-block:: console

    $ echo '{"myFloat": "1.23", "Items": [{"created": "2021-01-01"}]}' | wiz gs - output.py

.. code-block:: python3

    from dataclasses import dataclass
    from datetime import date
    from typing import List, Union

    from dataclass_wizard import JSONWizard

    @dataclass
    class Data(JSONWizard):
        my_float: Union[float, str]
        items: List['Item']

    @dataclass
    class Item:
        created: date

📖 Check out the full CLI documentation at wiz-cli_.

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

Mapping Nested JSON Keys
------------------------

The ``dataclass-wizard`` library lets you map deeply nested JSON keys to dataclass fields using custom path notation. This is ideal for handling complex or non-standard JSON structures.

You can specify paths to JSON keys with the ``KeyPath`` or ``path_field`` helpers. For example, the deeply nested key ``data.items.myJSONKey`` can be mapped to a dataclass field, such as ``my_str``:

.. code:: python3

    from dataclasses import dataclass
    from dataclass_wizard import path_field, JSONWizard

    @dataclass
    class MyData(JSONWizard):
        my_str: str = path_field('data.items.myJSONKey', default="default_value")

    input_dict = {'data': {'items': {'myJSONKey': 'Some value'}}}
    data_instance = MyData.from_dict(input_dict)
    print(data_instance.my_str)  # Output: 'Some value'

Custom Paths for Complex JSON
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use `custom paths to access nested keys`_ and map them to specific fields, even when keys contain special characters or follow non-standard conventions.

Example with nested and complex keys:

.. code:: python3

    from dataclasses import dataclass
    from typing import Annotated
    from dataclass_wizard import JSONWizard, path_field, KeyPath


    @dataclass
    class NestedData(JSONWizard):
        my_str: str = path_field('data[0].details["key with space"]', default="default_value")
        my_int: Annotated[int, KeyPath('data[0].items[3.14].True')] = 0


    input_dict = {
        'data': [
            {
                'details': {'key with space': 'Another value'},
                'items': {3.14: {True: "42"}}
            }
        ]
    }

    # Deserialize JSON to dataclass
    data = NestedData.from_dict(input_dict)
    print(data.my_str)  # Output: 'Another value'

    # Serialize back to JSON
    output_dict = data.to_dict()
    print(output_dict)  # {'data': {0: {'details': {'key with space': 'Another value'}, 'items': {3.14: {True: 42}}}}}

    # Verify data consistency
    assert data == NestedData.from_dict(output_dict)

    # Handle empty input gracefully
    data = NestedData.from_dict({'data': []})
    print(repr(data))  # NestedData(my_str='default_value', my_int=0)

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

.. admonition:: **Added in v0.28.0**

   There is now `Easier Debug Mode`_.

Enables additional (more verbose) log output. For example, a message can be
logged whenever an unknown JSON key is encountered when
``from_dict`` or ``from_json`` is called.

This also results in more helpful error messages during the JSON load
(de-serialization) process, such as when values are an invalid type --
i.e. they don't match the annotation for the field. This can be particularly
useful for debugging purposes.

.. note::
  There is a minor performance impact when DEBUG mode is enabled;
  for that reason, I would personally advise against enabling
  this in a *production* environment.

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
    logging.basicConfig(level='DEBUG')


    @dataclass
    class Container(JSONWizard):

        class _(JSONWizard.Meta):
            # True to enable Debug mode for additional (more verbose) log output.
            #
            # Pass in a `str` to `int` to set the minimum log level:
            #   logging.getLogger('dataclass_wizard').setLevel('INFO')
            debug_enabled = logging.INFO
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

See the section on `Handling Unknown JSON Keys`_ for more info.

Save or "Catch-All" Unknown JSON Keys
######################################

When calling ``from_dict`` or ``from_json``, any unknown or extraneous JSON keys
that are not mapped to fields in the dataclass are typically ignored or raise an error.
However, you can capture these undefined keys in a catch-all field of type ``CatchAll``,
allowing you to handle them as needed later.

For example, suppose you have the following dictionary::

    dump_dict = {
        "endpoint": "some_api_endpoint",
        "data": {"foo": 1, "bar": "2"},
        "undefined_field_name": [1, 2, 3]
    }

You can save the undefined keys in a catch-all field and process them later.
Simply define a field of type ``CatchAll`` in your dataclass. This field will act
as a dictionary to store any unmapped keys and their values. If there are no
undefined keys, the field will default to an empty dictionary.

.. code:: python

    from dataclasses import dataclass
    from typing import Any
    from dataclass_wizard import CatchAll, JSONWizard

    @dataclass
    class UnknownAPIDump(JSONWizard):
        endpoint: str
        data: dict[str, Any]
        unknown_things: CatchAll

    dump_dict = {
        "endpoint": "some_api_endpoint",
        "data": {"foo": 1, "bar": "2"},
        "undefined_field_name": [1, 2, 3]
    }

    dump = UnknownAPIDump.from_dict(dump_dict)
    print(f'{dump!r}')
    # > UnknownAPIDump(endpoint='some_api_endpoint', data={'foo': 1, 'bar': '2'},
    #       unknown_things={'undefined_field_name': [1, 2, 3]})

    print(dump.to_dict())
    # > {'endpoint': 'some_api_endpoint', 'data': {'foo': 1, 'bar': '2'}, 'undefined_field_name': [1, 2, 3]}

.. note::
    - When using a "catch-all" field, it is strongly recommended to define exactly **one** field of type ``CatchAll`` in the dataclass.

    - ``LetterCase`` transformations do not apply to keys stored in the ``CatchAll`` field; the keys remain as they are provided.

    - If you specify a default (or a default factory) for the ``CatchAll`` field, such as
      ``unknown_things: CatchAll = None``, the default value will be used instead of an
      empty dictionary when no undefined parameters are present.

    - The ``CatchAll`` functionality is guaranteed only when using ``from_dict`` or ``from_json``.
      Currently, unknown keyword arguments passed to ``__init__`` will not be written to a ``CatchAll`` field.

Date and Time with Custom Patterns
----------------------------------

As of *v0.20.0*, date and time strings in a `custom format`_ can be de-serialized
using the ``DatePattern``, ``TimePattern``, and ``DateTimePattern`` type annotations,
representing patterned `date`, `time`, and `datetime` objects respectively.

This will internally call ``datetime.strptime`` with the format specified in the annotation,
and also use the ``fromisoformat()`` method in case the date string is in ISO-8601 format.
All dates and times will continue to be serialized as ISO format strings by default. For more
info, check out the `Patterned Date and Time`_ section in the docs.

A brief example of the intended usage is shown below:

.. code:: python3

    from dataclasses import dataclass
    from datetime import time, datetime
    from typing import Annotated

    from dataclass_wizard import fromdict, asdict, DatePattern, TimePattern, Pattern


    @dataclass
    class MyClass:
        date_field: DatePattern['%m-%Y']
        dt_field: Annotated[datetime, Pattern('%m/%d/%y %H.%M.%S')]
        time_field1: TimePattern['%H:%M']
        time_field2: Annotated[list[time], Pattern('%I:%M %p')]


    data = {'date_field': '12-2022',
            'time_field1': '15:20',
            'dt_field': '1/02/23 02.03.52',
            'time_field2': ['1:20 PM', '12:30 am']}

    class_obj = fromdict(MyClass, data)

    # All annotated fields de-serialize as just date, time, or datetime, as shown.
    print(class_obj)
    # MyClass(date_field=datetime.date(2022, 12, 1), dt_field=datetime.datetime(2023, 1, 2, 2, 3, 52),
    #         time_field1=datetime.time(15, 20), time_field2=[datetime.time(13, 20), datetime.time(0, 30)])

    # All date/time fields are serialized as ISO-8601 format strings by default.
    print(asdict(class_obj))
    # {'dateField': '2022-12-01', 'dtField': '2023-01-02T02:03:52',
    #  'timeField1': '15:20:00', 'timeField2': ['13:20:00', '00:30:00']}

    # But, the patterned date/times can still be de-serialized back after
    # serialization. In fact, it'll be faster than parsing the custom patterns!
    assert class_obj == fromdict(MyClass, asdict(class_obj))

"Recursive" Dataclasses with Cyclic References
----------------------------------------------

Prior to version `v0.27.0`, dataclasses with cyclic references
or self-referential structures were not supported. This
limitation is shown in the following toy example:

.. code:: python3

    from dataclasses import dataclass

    @dataclass
    class A:
        a: 'A | None' = None

    a = A(a=A(a=A(a=A())))

This was a `longstanding issue`_.

New in ``v0.27.0``: The Dataclass Wizard now extends its support
to cyclic and self-referential dataclass models.

The example below demonstrates recursive dataclasses with cyclic
dependencies, following the pattern ``A -> B -> A -> B``. For more details, see
the `Cyclic or "Recursive" Dataclasses`_ section in the documentation.

.. code:: python3

    from __future__ import annotations  # This can be removed in Python 3.10+

    from dataclasses import dataclass

    from dataclass_wizard import JSONWizard


    @dataclass
    class A(JSONWizard):
        class _(JSONWizard.Meta):
            # enable support for self-referential / recursive dataclasses
            recursive_classes = True

        b: 'B | None' = None


    @dataclass
    class B:
        a: A | None = None


    # confirm that `from_dict` with a recursive, self-referential
    # input `dict` works as expected.
    a = A.from_dict({'b': {'a': {'b': {'a': None}}}})

    assert a == A(b=B(a=A(b=B())))

Dataclasses in ``Union`` Types
------------------------------

The ``dataclass-wizard`` library fully supports declaring dataclass models in
`Union`_ types as field annotations, such as ``list[Wizard | Archer | Barbarian]``.

As of *v0.19.0*, there is added support to  *auto-generate* tags for a dataclass model
-- based on the class name -- as well as to specify a custom *tag key* that will be
present in the JSON object, which defaults to a special ``__tag__`` key otherwise.
These two options are controlled by the ``auto_assign_tags`` and ``tag_key``
attributes (respectively) in the ``Meta`` config.

To illustrate a specific example, a JSON object such as
``{"oneOf": {"type": "A", ...}, ...}`` will now automatically map to a dataclass
instance ``A``, provided that the ``tag_key`` is correctly set to "type", and
the field ``one_of`` is annotated as a Union type in the ``A | B`` syntax.

Let's start out with an example, which aims to demonstrate the simplest usage of
dataclasses in ``Union`` types. For more info, check out the
`Dataclasses in Union Types`_ section in the docs.

.. code:: python3

    from __future__ import annotations

    from dataclasses import dataclass

    from dataclass_wizard import JSONWizard


    @dataclass
    class Container(JSONWizard):

        class Meta(JSONWizard.Meta):
            tag_key = 'type'
            auto_assign_tags = True

        objects: list[A | B | C]


    @dataclass
    class A:
        my_int: int
        my_bool: bool = False


    @dataclass
    class B:
        my_int: int
        my_bool: bool = True


    @dataclass
    class C:
        my_str: str


    data = {
        'objects': [
            {'type': 'A', 'my_int': 42},
            {'type': 'C', 'my_str': 'hello world'},
            {'type': 'B', 'my_int': 123},
            {'type': 'A', 'my_int': 321, 'myBool': True}
        ]
    }


    c = Container.from_dict(data)
    print(f'{c!r}')

    # True
    assert c == Container(objects=[A(my_int=42, my_bool=False),
                                   C(my_str='hello world'),
                                   B(my_int=123, my_bool=True),
                                   A(my_int=321, my_bool=True)])


    print(c.to_dict())
    # prints the following on a single line:
    # {'objects': [{'myInt': 42, 'myBool': False, 'type': 'A'},
    #              {'myStr': 'hello world', 'type': 'C'},
    #              {'myInt': 123, 'myBool': True, 'type': 'B'},
    #              {'myInt': 321, 'myBool': True, 'type': 'A'}]}

    # True
    assert c == c.from_json(c.to_json())

Conditional Field Skipping
--------------------------

.. admonition:: **Added in v0.30.0**

    Dataclass Wizard introduces `conditional skipping`_ to omit fields during JSON serialization based on user-defined conditions. This feature works seamlessly with:

    - **Global rules** via ``Meta`` settings.
    - **Per-field controls** using ``SkipIf()`` `annotations`_.
    - **Field wrappers** for maximum flexibility.

Quick Examples
~~~~~~~~~~~~~~

1. **Globally Skip Fields Matching a Condition**

  Define a global skip rule using ``Meta.skip_if``:

  .. code-block:: python3

    from dataclasses import dataclass
    from dataclass_wizard import JSONWizard, IS_NOT


    @dataclass
    class Example(JSONWizard):
        class _(JSONWizard.Meta):
            skip_if = IS_NOT(True)  # Skip fields if the value is not `True`

        my_bool: bool
        my_str: 'str | None'


    print(Example(my_bool=True, my_str=None).to_dict())
    # Output: {'myBool': True}

2. **Skip Defaults Based on a Condition**

  Skip fields with default values matching a specific condition using ``Meta.skip_defaults_if``:

  .. code-block:: python3

    from __future__ import annotations  # Can remove in PY 3.10+

    from dataclasses import dataclass
    from dataclass_wizard import JSONPyWizard, IS


    @dataclass
    class Example(JSONPyWizard):
        class _(JSONPyWizard.Meta):
            skip_defaults_if = IS(None)  # Skip default `None` values.

        str_with_no_default: str | None
        my_str: str | None = None
        my_bool: bool = False


    print(Example(str_with_no_default=None, my_str=None).to_dict())
    #> {'str_with_no_default': None, 'my_bool': False}


  .. note::
      Setting ``skip_defaults_if`` also enables ``skip_defaults=True`` automatically.

3. **Per-Field Conditional Skipping**

  Apply skip rules to specific fields with `annotations`_ or ``skip_if_field``:

  .. code-block:: python3

    from __future__ import annotations  # can be removed in Python 3.10+

    from dataclasses import dataclass
    from typing import Annotated

    from dataclass_wizard import JSONWizard, SkipIfNone, skip_if_field, EQ


    @dataclass
    class Example(JSONWizard):
        my_str: Annotated[str | None, SkipIfNone]  # Skip if `None`.
        other_str: str | None = skip_if_field(EQ(''), default=None)  # Skip if empty.

    print(Example(my_str=None, other_str='').to_dict())
    # Output: {}

4. **Skip Fields Based on Truthy or Falsy Values**

   Use the ``IS_TRUTHY`` and ``IS_FALSY`` helpers to conditionally skip fields based on their truthiness:

   .. code-block:: python3

    from dataclasses import dataclass, field
    from dataclass_wizard import JSONWizard, IS_FALSY


    @dataclass
    class ExampleWithFalsy(JSONWizard):
        class _(JSONWizard.Meta):
            skip_if = IS_FALSY()  # Skip fields if they evaluate as "falsy".

        my_bool: bool
        my_list: list = field(default_factory=list)
        my_none: None = None

    print(ExampleWithFalsy(my_bool=False, my_list=[], my_none=None).to_dict())
    #> {}

.. note::

   *Special Cases*

   - **SkipIfNone**: Alias for ``SkipIf(IS(None))``, skips fields with a value of ``None``.
   - **Condition Helpers**:

     - ``IS``, ``IS_NOT``: Identity checks.
     - ``EQ``, ``NE``, ``LT``, ``LE``, ``GT``, ``GE``: Comparison operators.
     - ``IS_TRUTHY``, ``IS_FALSY``: Skip fields based on truthy or falsy values.

   Combine these helpers for flexible serialization rules!

.. _conditional skipping: https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/serialization_options.html#skip-if-functionality

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

    from dataclass_wizard import JSONWizard


    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            skip_defaults = True

        my_str: str
        other_str: str = 'any value'
        optional_str: str = None
        my_list: list[str] = field(default_factory=list)
        my_dict: defaultdict[str, list[float]] = field(
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

``Environ`` Magic
-----------------

Easily map environment variables to Python dataclasses with ``EnvWizard``:

.. code-block:: python3

    import os
    from dataclass_wizard import EnvWizard

    # Set up environment variables
    os.environ.update({
        'APP_NAME': 'Env Wizard',
        'MAX_CONNECTIONS': '10',
        'DEBUG_MODE': 'true'
    })

    # Define dataclass using EnvWizard
    class AppConfig(EnvWizard):
        app_name: str
        max_connections: int
        debug_mode: bool

    # Load config from environment variables
    config = AppConfig()
    print(config.app_name)    #> Env Wizard
    print(config.debug_mode)  #> True
    assert config.max_connections == 10

    # Override with keyword arguments
    config = AppConfig(app_name='Dataclass Wizard Rocks!', debug_mode='false')
    print(config.app_name)    #> Dataclass Wizard Rocks!
    assert config.debug_mode is False

.. note::
    ``EnvWizard`` simplifies environment variable mapping with type validation, ``.env`` file support, and secret file handling (file names become keys).

    *Key Features*:

    - **Auto Parsing**: Supports complex types and nested structures.
    - **Configurable**: Customize variable names, prefixes, and dotenv files.
    - **Validation**: Errors for missing or malformed variables.

    📖 `Full Documentation <https://dataclass-wizard.readthedocs.io/en/latest/env_magic.html>`_

Advanced Example: Dynamic Prefix Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``EnvWizard`` supports dynamic prefix application, ideal for customizable environments:

.. code-block:: python3

    import os
    from dataclass_wizard import EnvWizard, env_field

    # Define dataclass with custom prefix support
    class AppConfig(EnvWizard):

        class _(EnvWizard.Meta):
            env_prefix = 'APP_'  # Default prefix for env vars

        name: str = env_field('A_NAME')  # Looks for `APP_A_NAME` by default
        debug: bool

    # Set environment variables
    os.environ['CUSTOM_A_NAME'] = 'Test!'
    os.environ['CUSTOM_DEBUG'] = 'yes'

    # Apply a dynamic prefix at runtime
    config = AppConfig(_env_prefix='CUSTOM_')  # Looks for `CUSTOM_A_NAME` and `CUSTOM_DEBUG`

    print(config)
    # > AppConfig(name='Test!', debug=True)

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

What's New in v1.0
------------------

.. warning::

   - **Default Key Transformation Update**

     Starting with ``v1.0.0``, the default key transformation for JSON serialization
     will change to keep keys *as-is* instead of converting them to `camelCase`.

     *New Default Behavior*: ``key_transform='NONE'`` will be the standard setting.

     *How to Prepare*: You can enforce this future behavior right now by using the ``JSONPyWizard`` helper:

     .. code-block:: python3

        from dataclasses import dataclass
        from dataclass_wizard import JSONPyWizard

        @dataclass
        class MyModel(JSONPyWizard):
            my_field: str

        print(MyModel(my_field="value").to_dict())
        # Output: {'my_field': 'value'}


   - **Float to Int Conversion Change**

     Starting in ``v1.0``, floats or float strings with fractional
     parts (e.g., ``123.4`` or ``"123.4"``) will no longer be silently
     converted to integers. Instead, they will raise an error.
     However, floats with no fractional parts (e.g., ``3.0``
     or ``"3.0"``) will still convert to integers as before.

     *How to Prepare*: To ensure compatibility with the new behavior:

     - Use ``float`` annotations for fields that may include fractional values.
     - Review your data and avoid passing fractional values (e.g., ``123.4``) to fields annotated as ``int``.
     - Update tests or logic that rely on the current rounding behavior.

Contributing
------------

Contributions are welcome! Open a pull request to fix a bug, or `open an issue`_
to discuss a new feature or change.

Check out the `Contributing`_ section in the docs for more info.

TODOs
-----

All feature ideas or suggestions for future consideration, have been currently added
`as milestones`_ in the project's GitHub repo.

Credits
-------

This package was created with Cookiecutter_ and the `rnag/cookiecutter-pypackage`_ project template.

.. _Read The Docs: https://dataclass-wizard.readthedocs.io
.. _Installation: https://dataclass-wizard.readthedocs.io/en/latest/installation.html
.. _Cookiecutter: https://github.com/cookiecutter/cookiecutter
.. _`rnag/cookiecutter-pypackage`: https://github.com/rnag/cookiecutter-pypackage
.. _`Contributing`: https://dataclass-wizard.readthedocs.io/en/latest/contributing.html
.. _`open an issue`: https://github.com/rnag/dataclass-wizard/issues
.. _`JSONPyWizard`: https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/wizard_mixins.html#jsonpywizard
.. _`EnvWizard`: https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/wizard_mixins.html#envwizard
.. _`on EnvWizard`: https://dataclass-wizard.readthedocs.io/en/latest/env_magic.html
.. _`JSONListWizard`: https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/wizard_mixins.html#jsonlistwizard
.. _`JSONFileWizard`: https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/wizard_mixins.html#jsonfilewizard
.. _`TOMLWizard`: https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/wizard_mixins.html#tomlwizard
.. _`YAMLWizard`: https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/wizard_mixins.html#yamlwizard
.. _`Container`: https://dataclass-wizard.readthedocs.io/en/latest/dataclass_wizard.html#dataclass_wizard.Container
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
.. _custom format: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
.. _`Patterned Date and Time`: https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/patterned_date_time.html
.. _Union: https://docs.python.org/3/library/typing.html#typing.Union
.. _`Dataclasses in Union Types`: https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/dataclasses_in_union_types.html
.. _`Cyclic or "Recursive" Dataclasses`: https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/cyclic_or_recursive_dataclasses.html
.. _as milestones: https://github.com/rnag/dataclass-wizard/milestones
.. _longstanding issue: https://github.com/rnag/dataclass-wizard/issues/62
.. _Easier Debug Mode: https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/easier_debug_mode.html
.. _Handling Unknown JSON Keys: https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/handling_unknown_json_keys.html
.. _custom paths to access nested keys: https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/nested_key_paths.html
.. _annotations: https://docs.python.org/3/library/typing.html#typing.Annotated
.. _typing: https://docs.python.org/3/library/typing.html
.. _dataclasses: https://docs.python.org/3/library/dataclasses.html
