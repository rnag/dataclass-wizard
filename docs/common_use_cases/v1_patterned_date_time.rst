Patterned Date and Time in V1 (``v0.35.0+``)
============================================

.. tip::
    The following documentation introduces support for patterned date and time strings
    added in ``v0.35.0``. This feature is part of an experimental "V1 Opt-in" mode,
    detailed in the `Field Guide to V1 Opt-in`_.

This feature, introduced in **v0.35.0**, allows parsing
custom date and time formats into Python's :class:`date`,
:class:`time`, and :class:`datetime` objects.
For example, strings like ``November 2, 2021`` can now
be parsed using customizable patterns.

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

Standard Date-Time Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. hint::
    Note that the "naive" implementations :class:`TimePattern` and :class:`DateTimePattern`
    do not have a *timezone* or :attr:`tzinfo` set on the de-serialized
    result.
    Also, :class:`date` does not have any *timezone*-related data, nor does its
    counterpart :class:`DatePattern`.

To use, simply annotate fields with ``DatePattern``, ``TimePattern``, or ``DateTimePattern``.
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

To handle timezone-aware ``datetime`` and ``time`` values, use the following patterns:

- :class:`AwareDateTimePattern`
- :class:`AwareTimePattern`
- :class:`AwarePattern` (with :class:`typing.Annotated`)

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

For UTC-specific ``datetime`` and ``time`` values, use the following patterns:

- :class:`UTCDateTimePattern`
- :class:`UTCTimePattern`
- :class:`UTCPattern` (with :class:`typing.Annotated`)

These patterns are used when working with
date and time in `Coordinated Universal Time (UTC)`_,
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
you can use ``Annotated`` with one of ``Pattern``,
``AwarePattern``, or ``UTCPattern`` to specify custom date-time formats.

**Example Usage:**

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

---

**Serialization:**
All date-time objects are serialized as ISO 8601 format strings by default. This ensures compatibility with other systems and optimizes parsing.

**Note:** Parsing uses ``datetime.fromisoformat`` for ISO 8601 strings, which is `much faster`_ than ``datetime.strptime``.

---

For more information, see the full `Field Guide to V1 Opt-in`_.

.. _`Field Guide to V1 Opt-in`: https://github.com/rnag/dataclass-wizard/wiki/Field-Guide-to-V1-Opt%E2%80%90in
.. _ISO 8601: https://en.wikipedia.org/wiki/ISO_8601
.. _much faster: https://stackoverflow.com/questions/13468126/a-faster-strptime
.. _`Coordinated Universal Time (UTC)`: https://en.wikipedia.org/wiki/Coordinated_Universal_Time
