.. title:: Patterned Date and Time in V1 (v0.35.0+)

Patterned Date and Time in V1 (``v0.35.0+``)
============================================

.. tip::
    The following documentation introduces support for patterned date and time strings
    added in ``v0.35.0``. This feature is part of an experimental "V1 Opt-in" mode,
    detailed in the `Field Guide to V1 Opt-in`_.

    V1 features are available starting from ``v0.33.0``. See `Enabling V1 Experimental Features`_ for more details.

This feature, introduced in **v0.35.0**, allows parsing
custom date and time formats into Python's :class:`date`,
:class:`time`, and :class:`datetime` objects.
For example, strings like ``November 2, 2021`` can now
be parsed using customizable patterns -- specified as `format codes`_.

**Key Features:**

- Supports standard, timezone-aware, and UTC patterns.
- Annotate fields using ``DatePattern``, ``TimePattern``, or ``DateTimePattern``.
- Retains `ISO 8601`_ serialization for compatibility.

**Supported Patterns:**

    1. **Naive Patterns** (default)
        * :class:`DatePattern`, :class:`DateTimePattern`, :class:`TimePattern`
    2. **Timezone-Aware Patterns**
        * :class:`AwareDateTimePattern`, :class:`AwareTimePattern`
    3. **UTC Patterns**
        * :class:`UTCDateTimePattern`, :class:`UTCTimePattern`

Pattern Comparison
~~~~~~~~~~~~~~~~~~

The following table compares the different types of date-time patterns: **Naive**, **Timezone-Aware**, and **UTC** patterns. It summarizes key features and example use cases for each.

+-----------------------------+----------------------------+-----------------------------------------------------------+
| Pattern Type                | Key Characteristics        | Example Use Cases                                         |
+=============================+============================+===========================================================+
| **Naive Patterns**          | No timezone info           | * :class:`DatePattern` (local date)                       |
|                             |                            | * :class:`TimePattern` (local time)                       |
|                             |                            | * :class:`DateTimePattern` (local datetime)               |
+-----------------------------+----------------------------+-----------------------------------------------------------+
| **Timezone-Aware Patterns** | Specifies a timezone       | * :class:`AwareDateTimePattern` (e.g., *'Europe/London'*) |
|                             |                            | * :class:`AwareTimePattern` (timezone-aware time)         |
+-----------------------------+----------------------------+-----------------------------------------------------------+
| **UTC Patterns**            | Interprets as UTC time     | * :class:`UTCDateTimePattern` (UTC datetime)              |
|                             |                            | * :class:`UTCTimePattern` (UTC time)                      |
+-----------------------------+----------------------------+-----------------------------------------------------------+

Standard Date-Time Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. hint::
    Note that the "naive" implementations :class:`TimePattern` and :class:`DateTimePattern`
    do not store *timezone* information -- or :attr:`tzinfo` -- on the de-serialized
    object (as explained in the `Naive datetime`_ concept). However, `Timezone-Aware Date and Time Patterns`_ *do* store this information.

    Additionally, :class:`date` does not have any *timezone*-related data, nor does its
    counterpart :class:`DatePattern`.

To use, simply annotate fields with ``DatePattern``, ``TimePattern``, or ``DateTimePattern``
with supported `format codes`_.
These patterns support the most common date formats.

.. code:: python3

    from dataclasses import dataclass
    from dataclass_wizard import JSONPyWizard
    from dataclass_wizard.v1 import DatePattern, TimePattern

    @dataclass
    class MyClass(JSONPyWizard):
        class _(JSONPyWizard.Meta):
            v1 = True

        date_field: DatePattern['%b %d, %Y']
        time_field: TimePattern['%I:%M %p']

    data = {'date_field': 'Jan 3, 2022', 'time_field': '3:45 PM'}
    c1 = MyClass.from_dict(data)
    print(c1)
    print(c1.to_dict())
    assert c1 == MyClass.from_dict(c1.to_dict())  #> True

Timezone-Aware Date and Time Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. hint::
    Timezone-aware date-time objects store timezone information,
    as detailed in the Timezone-aware_ section. This is accomplished
    using the built-in zoneinfo_ module in Python 3.9+.

To handle timezone-aware ``datetime`` and ``time`` values, use the following patterns:

- :class:`AwareDateTimePattern`
- :class:`AwareTimePattern`
- :class:`AwarePattern` (with :obj:`typing.Annotated`)

These patterns allow you to specify the timezone for the
date and time, ensuring that the values are interpreted
correctly relative to the given timezone.

**Example: Using Timezone-Aware Patterns**

.. code:: python3

    from dataclasses import dataclass
    from pprint import pprint
    from typing import Annotated

    from dataclass_wizard import LoadMeta, DumpMeta, fromdict, asdict
    from dataclass_wizard.v1 import AwareTimePattern, AwareDateTimePattern, Alias

    @dataclass
    class MyClass:
        my_aware_dt: AwareTimePattern['Europe/London', '%H:%M:%S']
        my_aware_dt2: Annotated[AwareDateTimePattern['Asia/Tokyo', '%m-%Y-%H:%M-%Z'], Alias('key')]

    LoadMeta(v1=True).bind_to(MyClass)
    DumpMeta(key_transform='NONE').bind_to(MyClass)

    d = {'my_aware_dt': '6:15:45', 'key': '10-2020-15:30-UTC'}
    c = fromdict(MyClass, d)

    pprint(c)
    print(asdict(c))
    assert c == fromdict(MyClass, asdict(c))  #> True

UTC Date and Time Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. hint::
    For UTC-specific time, use UTC patterns, which handle Coordinated Universal Time
    (UTC) as described in the UTC_ article.

For UTC-specific ``datetime`` and ``time`` values, use the following patterns:

- :class:`UTCDateTimePattern`
- :class:`UTCTimePattern`
- :class:`UTCPattern` (with :obj:`typing.Annotated`)

These patterns are used when working with
date and time in Coordinated Universal Time (UTC_),
and ensure that *timezone* data -- or :attr:`tzinfo` -- is
correctly set to ``UTC``.

**Example: Using UTC Patterns**

.. code:: python3

    from dataclasses import dataclass
    from typing import Annotated

    from dataclass_wizard import JSONPyWizard
    from dataclass_wizard.v1 import UTCTimePattern, UTCDateTimePattern, Alias

    @dataclass
    class MyClass(JSONPyWizard):
        class _(JSONPyWizard.Meta):
            v1 = True

        my_utc_time: UTCTimePattern['%H:%M:%S']
        my_utc_dt: Annotated[UTCDateTimePattern['%m-%Y-%H:%M-%Z'], Alias('key')]

    d = {'my_utc_time': '6:15:45', 'key': '10-2020-15:30-UTC'}
    c = MyClass.from_dict(d)
    print(c)
    print(c.to_dict())

Containers of Date and Time
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For more complex annotations like ``list[date]``,
you can use :obj:`typing.Annotated` with one of ``Pattern``,
``AwarePattern``, or ``UTCPattern`` to specify custom date-time formats.


.. tip::
    The :obj:`typing.Annotated` type is used to apply additional metadata (like
    timezone information) to a field. When combined with a date-time
    pattern, it tells the library how to interpret the field’s value
    in terms of its format or timezone.

**Example: Using Pattern with Annotated**

.. code:: python3

    from dataclasses import dataclass
    from datetime import time
    from typing import Annotated
    from dataclass_wizard import JSONPyWizard
    from dataclass_wizard.v1 import Pattern

    class MyTime(time):
        def get_hour(self):
            return self.hour

    @dataclass
    class MyClass(JSONPyWizard):
        class _(JSONPyWizard.Meta):
            v1 = True

        time_field: Annotated[list[MyTime], Pattern['%I:%M %p']]

    data = {'time_field': ['3:45 PM', '1:20 am', '12:30 pm']}
    c1 = MyClass.from_dict(data)
    print(c1)  #> MyClass(time_field=[MyTime(15, 45), MyTime(1, 20), MyTime(12, 30)])

Multiple Date and Time Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In **V1 Opt-in**, you can now use multiple date and time patterns (format codes) to parse and serialize your date and time fields.
This feature allows for flexibility when handling different formats, making it easier to work with various date and time strings.

Example: Using Multiple Patterns
---------------------------------

In the example below, the ``DatePattern`` and ``TimePattern`` are configured to support multiple formats. The class ``MyClass`` demonstrates how the fields can accept different formats for both dates and times.

.. code:: python3

    from dataclasses import dataclass
    from dataclass_wizard import JSONPyWizard
    from dataclass_wizard.v1 import DatePattern, UTCTimePattern

    @dataclass
    class MyClass(JSONPyWizard):
        class _(JSONPyWizard.Meta):
            v1 = True

        date_field: DatePattern['%b %d, %Y', '%I %p %Y-%m-%d']
        time_field: UTCTimePattern['%I:%M %p', '(%H)+(%S)']

    # Using the first date pattern format: 'Jan 3, 2022'
    data = {'date_field': 'Jan 3, 2022', 'time_field': '3:45 PM'}
    c1 = MyClass.from_dict(data)

    print(c1)
    print(c1.to_dict())
    assert c1 == MyClass.from_dict(c1.to_dict())  #> True
    print()

    # Using the second date pattern format: '3 PM 2025-01-15'
    data = {'date_field': '3 PM 2025-01-15', 'time_field': '(15)+(45)'}
    c2 = MyClass.from_dict(data)
    print(c2)
    print(c2.to_dict())
    assert c2 == MyClass.from_dict(c2.to_dict())  #> True
    print()

    # ERROR! The date is not a valid format for the available patterns.
    data = {'date_field': '2025-01-15 3 PM', 'time_field': '(15)+(45)'}
    _ = MyClass.from_dict(data)

How It Works
^^^^^^^^^^^^

1. **DatePattern and TimePattern:** These are special types that support multiple patterns (format codes). Each pattern is tried in the order specified, and the first one that matches the input string is used for parsing or formatting.

2. **DatePattern Usage:** The ``date_field`` in the example accepts two formats:

   - ``%b %d, %Y`` (e.g., 'Jan 3, 2022')
   - ``%I %p %Y-%m-%d`` (e.g., '3 PM 2025-01-15')

3. **TimePattern Usage:** The ``time_field`` accepts two formats:

   - ``%I:%M %p`` (e.g., '3:45 PM')
   - ``(%H)+(%S)`` (e.g., '(15)+(45)')

4. **Error Handling:** If the input string doesn't match any of the available patterns, an error will be raised.

This feature is especially useful for handling date and time formats from various sources, ensuring flexibility in how data is parsed and serialized.

Key Points
----------

- Multiple patterns are specified as a list of format codes in ``DatePattern`` and ``TimePattern``.
- The system automatically tries each pattern in the order provided until a match is found.
- If no match is found, an error is raised, as shown in the example with the invalid date format ``'2025-01-15 3 PM'``.

---

**Serialization:**

.. hint::
    **ISO 8601**: Serialization of all date-time objects follows
    the `ISO 8601`_ standard, a widely-used format for representing
    date and time.

All date-time objects are serialized as ISO 8601 format strings by default. This ensures compatibility with other systems and optimizes parsing.

**Note:** Parsing uses ``datetime.fromisoformat`` for ISO 8601 strings, which is `much faster`_ than ``datetime.strptime``.

---

For more information, see the full `Field Guide to V1 Opt-in`_.

.. _`Enabling V1 Experimental Features`: https://github.com/rnag/dataclass-wizard/wiki/V1:-Enabling-Experimental-Features
.. _`Field Guide to V1 Opt-in`: https://github.com/rnag/dataclass-wizard/wiki/Field-Guide-to-V1-Opt%E2%80%90in
.. _much faster: https://stackoverflow.com/questions/13468126/a-faster-strptime
.. _`Coordinated Universal Time (UTC)`: https://en.wikipedia.org/wiki/Coordinated_Universal_Time
.. _Naive datetime: https://stackoverflow.com/questions/9999226/timezone-aware-vs-timezone-naive-in-python
.. _Timezone-aware: https://docs.python.org/3/library/datetime.html#datetime.tzinfo
.. _UTC: https://en.wikipedia.org/wiki/Coordinated_Universal_Time
.. _ISO 8601: https://en.wikipedia.org/wiki/ISO_8601
.. _zoneinfo: https://docs.python.org/3/library/zoneinfo.html#using-zoneinfo
.. _format codes: https://docs.python.org/3/library/datetime.html#format-codes
