
.. image:: https://raw.githubusercontent.com/rnag/dataclass-wizard/main/images/logo.png
   :alt: Dataclass Wizard logo
   :width: 160px
   :align: center

**Simple, elegant wizarding tools for Python’s** ``dataclasses``.

📘 Docs → `dcw.ritviknag.com`_

.. image:: https://github.com/rnag/dataclass-wizard/actions/workflows/dev.yml/badge.svg
   :target: https://github.com/rnag/dataclass-wizard/actions/workflows/dev.yml
   :alt: CI Status

.. image:: https://img.shields.io/pypi/v/dataclass-wizard.svg
   :target: https://pypi.org/project/dataclass-wizard/
   :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/dataclass-wizard.svg
   :target: https://pypi.org/project/dataclass-wizard/
   :alt: Supported Python Versions

.. image:: https://static.pepy.tech/badge/dataclass-wizard
   :target: https://pepy.tech/project/dataclass-wizard
   :alt: Downloads per Month

**Dataclass Wizard** is a fast, well-tested serialization library for Python dataclasses.

-------------------

**Behold, the power of Dataclass Wizard**::

    >>> from __future__ import annotations
    >>> from dataclasses import field
    >>> from dataclass_wizard import DataclassWizard
    ...
    >>> class MyClass(DataclassWizard, load_case='AUTO', dump_case='CAMEL'):
    ...     my_str: str | None
    ...     is_active_tuple: tuple[bool, ...]
    ...     list_of_int: list[int] = field(default_factory=list)
    ...
    >>> MyClass.from_json(
    ...     '{"my_str": 20, "ListOfInt": ["1", "2", 3], "isActiveTuple": [true, false, 1]}'
    ... )
    MyClass(my_str='20', is_active_tuple=(True, False, True), list_of_int=[1, 2, 3])

.. note::
  The example above demonstrates automatic type coercion, key casing transforms,
  and support for nested dataclass structures.
  ``DataclassWizard`` also auto-applies ``@dataclass`` to subclasses.
  See the docs for more examples and advanced usage.

.. contents:: Contents
   :depth: 1
   :local:
   :backlinks: none

``v1`` Opt-In 🚀
----------------

Early access to **V1** is available! To opt in, simply enable ``v1=True`` in the ``Meta`` settings:

.. code-block:: python3

    from dataclasses import dataclass
    from dataclass_wizard import JSONPyWizard
    from dataclass_wizard.v1 import Alias

    @dataclass
    class A(JSONPyWizard):
        class _(JSONPyWizard.Meta):
            v1 = True

        my_str: str
        version_info: float = Alias(load='v-info')

    # Alternatively, for simple dataclasses that don't subclass `JSONPyWizard`:
    # LoadMeta(v1=True).bind_to(A)

    a = A.from_dict({'my_str': 'test', 'v-info': '1.0'})
    assert a.version_info == 1.0
    assert a.to_dict() == {'my_str': 'test', 'version_info': 1.0}

For more information, see the `Field Guide to V1 Opt-in`_.

Performance Improvements
~~~~~~~~~~~~~~~~~~~~~~~~

The upcoming **V1** release brings significant performance improvements in de/serialization. Personal benchmarks show that **V1** can make Dataclass Wizard
approximately **2x faster** than ``pydantic``!

While some features are still being refined and fully supported, **v1** positions Dataclass Wizard alongside other high-performance serialization libraries in Python.

Why Use Dataclass Wizard?
-------------------------

Effortlessly handle complex data with one of the *fastest* and *lightweight* libraries available! Perfect for APIs, JSON wrangling, and more.

- 🚀 **Blazing Fast** — One of the fastest libraries out there!
- 🪶 **Lightweight** — Pure Python, minimal dependencies
- 👶 Easy Setup — Intuitive, hassle-free
- ☝️ **Battle-Tested** — Proven reliability with solid test coverage
- ⚙️ Highly Customizable — Endless de/serialization options to fit your needs
- 🎉 Built-in Support — JSON, YAML, TOML, and environment/settings management
- 📦 **Full Python Type Support** — Powered by type hints with full support for native types and ``typing-extensions``
- 📝 Auto-Generate Schemas — JSON to Dataclass made easy

Key Features
------------

- 🔄 Flexible (de)serialization — Marshal dataclasses to/from JSON, TOML, YAML, or ``dict`` with ease.
- 🌿 Environment Magic — Map env vars and ``.env`` files to strongly-typed class fields effortlessly.
- 🧑‍💻 Field Properties Made Simple — Add properties with default values to your dataclasses.
- 🧙‍♂️ JSON-to-Dataclass Wizardry — Auto-generate a dataclass schema from any JSON file or string instantly.

Installation
------------

*Dataclass Wizard* is available on `PyPI`_. You can install it with ``pip``:

.. code-block:: console

    $ pip install dataclass-wizard

Also available on `conda`_ via `conda-forge`_. To install via ``conda``:

.. code-block:: console

    $ conda install dataclass-wizard -c conda-forge

This library supports **Python 3.9+**. Support for Python 3.6 – 3.8 was
available in earlier releases but is no longer maintained, as those
versions no longer receive security updates.

For convenience, the table below outlines the last compatible release
of *Dataclass Wizard* for unsupported Python versions (3.6 – 3.8):

.. list-table::
   :header-rows: 1
   :widths: 15 35 15

   * - Python Version
     - Last Version of ``dataclass-wizard``
     - Python EOL
   * - 3.8
     - 0.26.1_
     - 2024-10-07
   * - 3.7
     - 0.26.1_
     - 2023-06-27
   * - 3.6
     - 0.26.1_
     - 2021-12-23

.. _0.26.1: https://pypi.org/project/dataclass-wizard/0.26.1/
.. _PyPI: https://pypi.org/project/dataclass-wizard/
.. _conda: https://anaconda.org/conda-forge/dataclass-wizard
.. _conda-forge: https://conda-forge.org/
.. _Changelog: https://dcw.ritviknag.com/en/latest/history.html

See the package on `PyPI`_ and the `Changelog`_ in the docs for the latest version details.

Wizard Mixins ✨
----------------

In addition to ``JSONWizard``, these `Mixin`_ classes simplify common tasks and make your data handling *spellbindingly* efficient:

- 🪄 `EnvWizard`_ — Load environment variables and `.env` files into typed schemas, even supporting secret files (keys as file names).
- 🎩 `JSONPyWizard`_ — A helper for ``JSONWizard`` that preserves your keys as-is (no camelCase changes).
- 🔮 `JSONListWizard`_ — Extend ``JSONWizard`` to convert lists into `Container`_ objects.
- 💼 `JSONFileWizard`_ — Convert dataclass instances to/from local JSON files with ease.
- 🌳 `TOMLWizard`_ — Map your dataclasses to/from TOML format.
- 🧙‍♂️ `YAMLWizard`_ — Convert between YAML and dataclass instances using ``PyYAML``.

Supported Types 🧑‍💻
---------------------

*Dataclass Wizard* supports:

- 📋 **Collections**: Handle ``list``, ``dict``, and ``set`` effortlessly.
- 🔢 **Typing Generics**: Manage ``Union``, ``Any``, and other types from the `typing`_ module.
- 🌟 **Advanced Types**: Work with ``Enum``, ``defaultdict``, and ``datetime`` with ease.

For more info, check out the `Supported Types`_ section in the docs for detailed insights into each type and the load/dump process!

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
as mentioned `here <https://dcw.ritviknag.com/en/latest/common_use_cases/skip_the_str.html>`_.

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

.. note::
    **Important:** The functionality for **custom key mappings** (such as JSON-to-dataclass field mappings) is being re-imagined with the introduction of **V1 Opt-in**. Enhanced support for these features is now available, improving the user experience for working with custom mappings.

    For more details, see the `Field Guide to V1 Opt-in`_ and the `V1 Alias`_ documentation.

    This change is part of the ongoing improvements in version ``v0.35.0+``, and the old functionality will no longer be maintained in future releases.

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

.. note::
    **Important:** The current "nested path" functionality is being re-imagined.
    Please refer to the new docs for **V1 Opt-in** features, which introduce enhanced support for these use
    cases. For more details, see the `Field Guide to V1 Opt-in`_ and the `V1 Alias`_ documentation.

    This change is part of the ongoing improvements in version ``v0.35.0+``, and the old functionality will no longer be maintained in future releases.

The ``dataclass-wizard`` library allows you to map deeply nested JSON keys to dataclass fields using custom path notation. This is ideal for handling complex or non-standard JSON structures.

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

You can now use `custom paths to access nested keys`_ and map them to specific fields, even when keys contain special characters or follow non-standard conventions.

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

.. tip::
    As of **v0.35.0** with V1 Opt-in, Dataclass Wizard now supports timezone-aware and UTC ``datetime``
    and ``time`` patterns, as well as multiple pattern strings (i.e. multiple `custom formats`) for greater
    flexibility in pattern matching. These features are **not** available in the current ``v0.*`` versions.

    The new features include:

    - Timezone-aware ``datetime`` and ``time`` patterns.
    - UTC ``datetime`` and ``time`` patterns.
    - Multiple `custom formats`_ for a single field, providing more control over pattern matching.

    For more details and examples on how to use these new features, refer to the `V1 Opt-in documentation for Patterned Date and Time`_.

As of **v0.20.0**, date and time strings in `custom formats`_ can be de-serialized using the ``DatePattern``,
``TimePattern``, and ``DateTimePattern`` type annotations, which represent patterned ``date``, ``time``, and
``datetime`` objects, respectively.

Internally, these annotations use ``datetime.strptime`` with the specified format and the ``fromisoformat()``
method for ISO-8601 formatted strings. All date and time values are still serialized to ISO format strings by
default. For more information, refer to the `Patterned Date and Time`_ section in the documentation.

Here is an example demonstrating how to use these annotations:

.. code-block:: python3

    from dataclasses import dataclass
    from datetime import time, datetime
    from typing import Annotated

    from dataclass_wizard import fromdict, asdict, DatePattern, TimePattern, Pattern


    @dataclass
    class MyClass:
        # Custom format for date (Month-Year)
        date_field: DatePattern['%m-%Y']
        # Custom format for datetime (Month/Day/Year Hour.Minute.Second)
        dt_field: Annotated[datetime, Pattern('%m/%d/%y %H.%M.%S')]
        # Custom format for time (Hour:Minute)
        time_field1: TimePattern['%H:%M']
        # Custom format for a list of times (12-hour format with AM/PM)
        time_field2: Annotated[list[time], Pattern('%I:%M %p')]


    data = {'date_field': '12-2022',
            'time_field1': '15:20',
            'dt_field': '1/02/23 02.03.52',
            'time_field2': ['1:20 PM', '12:30 am']}

    class_obj = fromdict(MyClass, data)

    # All annotated fields de-serialize to date, time, or datetime objects, as shown.
    print(class_obj)
    # MyClass(date_field=datetime.date(2022, 12, 1), dt_field=datetime.datetime(2023, 1, 2, 2, 3, 52),
    #         time_field1=datetime.time(15, 20), time_field2=[datetime.time(13, 20), datetime.time(0, 30)])

    # All date/time fields are serialized as ISO-8601 format strings by default.
    print(asdict(class_obj))
    # {'dateField': '2022-12-01', 'dtField': '2023-01-02T02:03:52',
    #  'timeField1': '15:20:00', 'timeField2': ['13:20:00', '00:30:00']}

    # The patterned date/times can be de-serialized back after serialization, which will be faster than
    # re-parsing the custom patterns!
    assert class_obj == fromdict(MyClass, asdict(class_obj))

Recursive Types and Dataclasses with Cyclic References
------------------------------------------------------

Prior to version **0.27.0**, dataclasses with cyclic references
or self-referential structures were not supported. This
limitation is shown in the following toy example:

.. code:: python3

    from dataclasses import dataclass

    @dataclass
    class A:
        a: 'A | None' = None

    a = A(a=A(a=A(a=A())))

This was a `longstanding issue`_, but starting with ``v0.27.0``, Dataclass Wizard now supports
recursive dataclasses, including cyclic references.

The example below demonstrates recursive
dataclasses with cyclic dependencies, following the pattern ``A -> B -> A -> B``.
For more details, see the `Cyclic or "Recursive" Dataclasses`_ section in the documentation.

.. code:: python3

    from __future__ import annotations  # This can be removed in Python 3.10+

    from dataclasses import dataclass
    from dataclass_wizard import JSONWizard

    @dataclass
    class A(JSONWizard):
        class _(JSONWizard.Meta):
            # Enable support for self-referential / recursive dataclasses
            recursive_classes = True

        b: 'B | None' = None


    @dataclass
    class B:
        a: A | None = None

    # Confirm that `from_dict` with a recursive, self-referential
    # input `dict` works as expected.
    a = A.from_dict({'b': {'a': {'b': {'a': None}}}})

    assert a == A(b=B(a=A(b=B())))

Starting with version **0.34.0**, recursive types are supported *out of the box* (OOTB) with ``v1`` opt-in,
removing the need for any ``Meta`` settings like ``recursive_classes = True``.

This makes working with recursive dataclasses even easier and more streamlined. In addition, recursive types
are now supported for the following Python type constructs:

- NamedTuple_
- TypedDict_
- Union_
- Literal_
- Nested dataclasses_
- `Type aliases`_ (introduced in Python 3.12+)

.. _NamedTuple: https://docs.python.org/3/library/typing.html#typing.NamedTuple
.. _TypedDict: https://docs.python.org/3/library/typing.html#typing.TypedDict
.. _Union: https://docs.python.org/3/library/typing.html#typing.Union
.. _Literal: https://docs.python.org/3/library/typing.html#typing.Literal
.. _Type aliases: https://docs.python.org/3/library/typing.html#type-aliases

Example Usage
~~~~~~~~~~~~~

Recursive types allow handling complex nested data structures, such as deeply nested JSON objects or lists.
With ``v0.34.0`` of Dataclass Wizard, de/serializing these structures becomes seamless
and more intuitive.

Recursive ``Union``
###################

.. code-block:: python3

    from dataclasses import dataclass
    from dataclass_wizard import JSONWizard

    # For Python 3.9, use this `Union` approach:
    from typing_extensions import TypeAlias
    JSON: TypeAlias = 'str | int | float | bool | dict[str, JSON] | list[JSON] | None'

    # For Python 3.10 and above, use this simpler approach:
    # JSON = str | int | float | bool | dict[str, 'JSON'] | list['JSON'] | None

    # For Python 3.12+, you can use the `type` statement:
    # type JSON = str | int | float | bool | dict[str, JSON] | list[JSON] | None

    @dataclass
    class MyTestClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        name: str
        meta: str
        msg: JSON

    x = MyTestClass.from_dict(
        {
            "name": "name",
            "meta": "meta",
            "msg": [{"x": {"x": [{"x": ["x", 1, 1.0, True, None]}]}}],
        }
    )
    assert x == MyTestClass(
        name="name",
        meta="meta",
        msg=[{"x": {"x": [{"x": ["x", 1, 1.0, True, None]}]}}],
    )

.. note::
   The ``type`` statement in Python 3.12+ simplifies type alias definitions by avoiding string annotations for recursive references.

Recursive ``Union`` with Nested ``dataclasses``
###############################################

.. code-block:: python3

    from dataclasses import dataclass, field
    from dataclass_wizard import JSONWizard

    @dataclass
    class A(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True

        value: int
        nested: 'B'
        next: 'A | None' = None


    @dataclass
    class B:
        items: list[A] = field(default_factory=list)


    x = A.from_dict(
        {
            "value": 1,
            "next": {"value": 2, "next": None, "nested": {}},
            "nested": {"items": [{"value": 3, "nested": {}}]},
        }
    )
    assert x == A(
        value=1,
        next=A(value=2, next=None, nested=B(items=[])),
        nested=B(items=[A(value=3, nested=B())]),
    )

.. note::
   Nested ``dataclasses`` are particularly useful for representing hierarchical structures, such as trees or graphs, in a readable and maintainable way.

Official References
~~~~~~~~~~~~~~~~~~~

For more information, see:

- `Typing in Python <https://docs.python.org/3/library/typing.html>`_
- `PEP 695: Type Syntax <https://peps.python.org/pep-0695/>`_

These examples illustrate the power of recursive types in simplifying complex data structures while leveraging the functionality of ``dataclass-wizard``.

Dataclasses in ``Union`` Types
------------------------------

The ``dataclass-wizard`` library fully supports declaring dataclass models in
`Union`_ types, such as ``list[Wizard | Archer | Barbarian]``.

Starting from *v0.19.0*, the library introduces two key features:
- **Auto-generated tags** for dataclass models (based on class names).
- A customizable **tag key** (default: ``__tag__``) that identifies the model in JSON.

These options are controlled by the ``auto_assign_tags`` and ``tag_key`` attributes in the ``Meta`` config.

For example, if a JSON object looks like ``{"type": "A", ...}``, you can set ``tag_key = "type"`` to automatically deserialize it into the appropriate class, like `A`.

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
    print(repr(c))

    # Output:
    # Container(objects=[A(my_int=42, my_bool=False),
    #                    C(my_str='hello world'),
    #                    B(my_int=123, my_bool=True),
    #                    A(my_int=321, my_bool=True)])

    print(c.to_dict())

    # True
    assert c == c.from_json(c.to_json())

Supercharged ``Union`` Parsing
------------------------------

**What about untagged dataclasses in** ``Union`` **types or** ``|`` **syntax?** With the major release **V1** opt-in, ``dataclass-wizard`` supercharges *Union* parsing, making it intuitive and flexible, even without tags.

This is especially useful for collections like ``list[Wizard]`` or when tags (discriminators) are not feasible.

To enable this feature, opt in to **v1** using the ``Meta`` settings. For details, see the `Field Guide to V1 Opt-in`_.

.. code-block:: python3

    from __future__ import annotations  # Remove in Python 3.10+

    from dataclasses import dataclass
    from typing import Literal

    from dataclass_wizard import JSONWizard

    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            v1 = True  # Enable v1 opt-in
            v1_unsafe_parse_dataclass_in_union = True

        literal_or_float: Literal['Auto'] | float
        entry: int | MoreDetails
        collection: list[MoreDetails | int]

    @dataclass
    class MoreDetails:
        arg: str

    # OK: Union types work seamlessly
    c = MyClass.from_dict({
        "literal_or_float": 1.23,
        "entry": 123,
        "collection": [{"arg": "test"}]
    })
    print(repr(c))
    #> MyClass(literal_or_float=1.23, entry=123, collection=[MoreDetails(arg='test')])

    # OK: Handles primitive and dataclass parsing
    c = MyClass.from_dict({
        "literal_or_float": "Auto",
        "entry": {"arg": "example"},
        "collection": [123]
    })
    print(repr(c))
    #> MyClass(literal_or_float='Auto', entry=MoreDetails(arg='example'), collection=[123])

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

.. _conditional skipping: https://dcw.ritviknag.com/en/latest/common_use_cases/serialization_options.html#skip-if-functionality

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

    📖 `Full Documentation <https://dcw.ritviknag.com/en/latest/env_magic.html>`_

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

.. admonition:: Opt-in for v1 Now Available

   The early opt-in for **v1** is now available with enhanced features, including intuitive ``Union`` parsing and optimized performance. To enable this,
   set ``v1=True`` in your ``Meta`` settings.

   For more details and migration guidance, see the `Field Guide to V1 Opt-in`_.

.. warning:: *Important Changes in v1.0*

    - **Default Key Transformation Update**

      Starting with **v1.0.0**, the default key transformation for JSON serialization
      will change to keep keys *as-is* instead of converting them to ``camelCase``.

      **New Default Behavior**:
      The default setting for key transformation will be ``key_transform='NONE'``.

      **How to Prepare**:
      You can enforce this behavior immediately by using the ``JSONPyWizard`` helper, as shown below:

      .. code-block:: python3

            from dataclasses import dataclass
            from dataclass_wizard import JSONPyWizard

            @dataclass
            class MyModel(JSONPyWizard):
                my_field: str

            print(MyModel(my_field="value").to_dict())
            # Output: {'my_field': 'value'}

- **Default __str__() Behavior Change**

      Starting with **v1.0.0**, we no longer pretty-print the serialized JSON value with keys in ``camelCase``.
      Instead, we now use the ``pprint`` module to handle serialization formatting.

      **New Default Behavior**:
      The ``__str__()`` method in the ``JSONWizard`` class will use ``pprint`` by default.

      **How to Prepare**:
      You can immediately test this new behavior using the ``JSONPyWizard`` helper, as demonstrated below:

      .. code-block:: python3

            from dataclasses import dataclass
            from dataclass_wizard import JSONWizard, JSONPyWizard

            @dataclass
            class CurrentModel(JSONWizard):
                my_field: str

            @dataclass
            class NewModel(JSONPyWizard):
                my_field: str

            print(CurrentModel(my_field="value"))
            #> {
            #   "myField": "value"
            # }

            print(NewModel(my_field="value"))
            #> NewModel(my_field='value')

    - **Float to Int Conversion Change**
      Starting with **v1.0**, floats or float strings with fractional parts (e.g., ``123.4`` or ``"123.4"``) will no longer be silently converted to integers. Instead, they will raise an error. However, floats without fractional parts (e.g., ``3.0`` or ``"3.0"``) will continue to convert to integers as before.

      **How to Prepare**:
      You can opt in to **v1** via ``v1=True`` to test this behavior right now. Additionally, to ensure compatibility with the new behavior:

      - Use ``float`` annotations for fields that may include fractional values.
      - Review your data to avoid passing fractional values (e.g., ``123.4``) to fields annotated as ``int``.
      - Update tests or logic that depend on the current rounding behavior.

      .. code-block:: python3

            from dataclasses import dataclass
            from dataclass_wizard import JSONPyWizard

            @dataclass
            class Test(JSONPyWizard):
                class _(JSONPyWizard.Meta):
                    v1 = True

                list_of_int: list[int]

            input_dict = {'list_of_int': [1, '2.0', '3.', -4, '-5.00', '6', '-7']}
            t = Test.from_dict(input_dict)
            print(t)  #> Test(list_of_int=[1, 2, 3, -4, -5, 6, -7])

            # ERROR!
            _ = Test.from_dict({'list_of_int': [123.4]})

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

.. _dcw.ritviknag.com: https://dcw.ritviknag.com
.. _Cookiecutter: https://github.com/cookiecutter/cookiecutter
.. _`rnag/cookiecutter-pypackage`: https://github.com/rnag/cookiecutter-pypackage
.. _`Contributing`: https://dcw.ritviknag.com/en/latest/contributing.html
.. _`open an issue`: https://github.com/rnag/dataclass-wizard/issues
.. _`JSONPyWizard`: https://dcw.ritviknag.com/en/latest/common_use_cases/wizard_mixins.html#jsonpywizard
.. _`EnvWizard`: https://dcw.ritviknag.com/en/latest/common_use_cases/wizard_mixins.html#envwizard
.. _`on EnvWizard`: https://dcw.ritviknag.com/en/latest/env_magic.html
.. _`JSONListWizard`: https://dcw.ritviknag.com/en/latest/common_use_cases/wizard_mixins.html#jsonlistwizard
.. _`JSONFileWizard`: https://dcw.ritviknag.com/en/latest/common_use_cases/wizard_mixins.html#jsonfilewizard
.. _`TOMLWizard`: https://dcw.ritviknag.com/en/latest/common_use_cases/wizard_mixins.html#tomlwizard
.. _`YAMLWizard`: https://dcw.ritviknag.com/en/latest/common_use_cases/wizard_mixins.html#yamlwizard
.. _`Container`: https://dcw.ritviknag.com/en/latest/dataclass_wizard.html#dataclass_wizard.Container
.. _`Supported Types`: https://dcw.ritviknag.com/en/latest/overview.html#supported-types
.. _`Mixin`: https://stackoverflow.com/a/547714/10237506
.. _`Meta`: https://dcw.ritviknag.com/en/latest/common_use_cases/meta.html
.. _`pydantic`: https://pydantic-docs.helpmanual.io/
.. _`Using Field Properties`: https://dcw.ritviknag.com/en/latest/using_field_properties.html
.. _`field properties`: https://dcw.ritviknag.com/en/latest/using_field_properties.html
.. _`custom mapping`: https://dcw.ritviknag.com/en/latest/common_use_cases/custom_key_mappings.html
.. _`wiz-cli`: https://dcw.ritviknag.com/en/latest/wiz_cli.html
.. _`key limitations`: https://florimond.dev/en/posts/2018/10/reconciling-dataclasses-and-properties-in-python/
.. _`more complete example`: https://dcw.ritviknag.com/en/latest/examples.html#a-more-complete-example
.. _custom formats: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
.. _`Patterned Date and Time`: https://dcw.ritviknag.com/en/latest/common_use_cases/patterned_date_time.html
.. _Union: https://docs.python.org/3/library/typing.html#typing.Union
.. _`Dataclasses in Union Types`: https://dcw.ritviknag.com/en/latest/common_use_cases/dataclasses_in_union_types.html
.. _`Cyclic or "Recursive" Dataclasses`: https://dcw.ritviknag.com/en/latest/common_use_cases/cyclic_or_recursive_dataclasses.html
.. _as milestones: https://github.com/rnag/dataclass-wizard/milestones
.. _longstanding issue: https://github.com/rnag/dataclass-wizard/issues/62
.. _Easier Debug Mode: https://dcw.ritviknag.com/en/latest/common_use_cases/easier_debug_mode.html
.. _Handling Unknown JSON Keys: https://dcw.ritviknag.com/en/latest/common_use_cases/handling_unknown_json_keys.html
.. _custom paths to access nested keys: https://dcw.ritviknag.com/en/latest/common_use_cases/nested_key_paths.html
.. _annotations: https://docs.python.org/3/library/typing.html#typing.Annotated
.. _typing: https://docs.python.org/3/library/typing.html
.. _dataclasses: https://docs.python.org/3/library/dataclasses.html
.. _V1 Opt-in documentation for Patterned Date and Time: https://dcw.ritviknag.com/en/latest/common_use_cases/v1_patterned_date_time.html
.. _`Field Guide to V1 Opt-in`: https://github.com/rnag/dataclass-wizard/wiki/Field-Guide-to-V1-Opt%E2%80%90in
.. _V1 Alias: https://dcw.ritviknag.com/en/latest/common_use_cases/v1_alias.html
