Patterned Date and Time in V1
=============================

.. tip::
    The following documentation introduces support for patterned date and time strings
    added in ``v0.35.0``. This feature is part of an experimental "V1 Opt-in" mode,
    detailed in the `Field Guide to V1 Opt-in`_.

.. _`Field Guide to V1 Opt-in`: https://github.com/rnag/dataclass-wizard/wiki/Field-Guide-to-V1-Opt%E2%80%90in

This feature, introduced in version **0.35.0**, enhances flexibility
by allowing the parsing of non-standard date-time
formats into Python's built-in :class:`date`, :class:`time`, and :class:`datetime` objects.
For example, strings such as ``November 2, 2021`` can now be seamlessly parsed and
converted using customizable patterns.

**Key Features:**

- Supports standard, timezone-aware, and UTC-specific date-time patterns.
- Enables ``Annotated`` option to specify desired formats.
- Retains `ISO 8601`_ serialization for compatibility.

There are three main approaches that can be used to specify custom patterns
for date-time strings:

    * *Naive* date and time patterns (default)
        * :class:`DatePattern <dataclass_wizard.v1.DatePattern>`
        * :class:`TimePattern`
        * :class:`DateTimePattern`
    * Timezone-aware ``datetime`` and ``time`` patterns
        * :class:`AwareDateTimePattern`
        * :class:`AwareTimePattern`
    * UTC ``datetime`` and ``time`` patterns
        * :class:`UTCDateTimePattern`
        * :class:`UTCTimePattern`

The simplest approach is to annotate fields as either
a :class:`DatePattern`, :class:`TimePattern`, or a :class:`DateTimePattern`.

Standard Patterns
~~~~~~~~~~~~~~~~~

There are two approaches (shown below) that can be used to specify custom patterns
for date-time strings. The simplest approach is to annotate fields as either
a :class:`DatePattern`, :class:`TimePattern`, or a :class:`DateTimePattern`.

.. hint::
    Note that the "naive" implementations :class:`TimePattern` and :class:`DateTimePattern`
    do not have a *timezone* or :attr:`tzinfo` set on the de-serialized
    result.

    Also, :class:`date` does not have any *timezone*-related data, nor does its
    counterpart :class:`DatePattern`.

.. note::
    The input date-time strings are parsed in the following sequence:

    - In case it's an `ISO 8601`_ format string, we first attempt to
      parse using the builtin :meth:`datetime.fromisoformat` method,
      as this is `much faster`_ than using :meth:`datetime.strptime`.
      If the date string is matched, we
      immediately return the new date-time object.
    - If it's instead a numeric timestamp, we attempt to parse
      with the fallback load function such as :func:`as_datetime`.
    - Next, we parse the string with :meth:`datetime.strptime` by passing in the
      *pattern* to match against. If the pattern is invalid, a
      ``ParseError`` is raised at this stage.

In any case, the :class:`date`, :class:`time`, and :class:`datetime` objects
are dumped (serialized) as `ISO 8601`_ format strings, which is the default
behavior. As we initially attempt to parse with :meth:`fromisoformat` in the
load (de-serialization) process as mentioned, it turns out
`much faster`_ to load any data that has been previously serialized in
ISO-8601 format.

The usage is shown below, and is again pretty straightforward.

.. code:: python3

    from dataclasses import dataclass
    from datetime import datetime
    from typing import Annotated

    from dataclass_wizard import JSONWizard
    from dataclass_wizard.v1 import Pattern, DatePattern, TimePattern


    @dataclass
    class MyClass(JSONWizard):
        class _(JSONWizard.Meta):
            v1 = True
            key_transform_with_dump = 'NONE'
        # 1 -- Annotate with `DatePattern`, `TimePattern`, or `DateTimePattern`.
        #      Upon de-serialization, the underlying types will be `date`,
        #      `time`, and `datetime` respectively.
        date_field: DatePattern['%b %d, %Y']
        time_field: TimePattern['%I:%M %p']
        # 2 -- Use `Annotated` to annotate the field as `list[time]` for example,
        #      and pass in `Pattern` as an extra.
        dt_field: Annotated[datetime, Pattern('%m/%d/%y %H:%M:%S')]


    data = {'date_field': 'Jan 3, 2022',
            'time_field': '3:45 PM',
            'dt_field': '01/02/23 02:03:52'}

    # Deserialize the data into a `MyClass` object
    c1 = MyClass.from_dict(data)

    print('Deserialized object:', repr(c1))
    # MyClass(date_field=datetime.date(2022, 1, 3),
    #         time_field=datetime.time(15, 45),
    #         dt_field=datetime.datetime(2023, 1, 2, 2, 3, 52))

    # Print the prettified JSON representation. Note that date/times are
    # converted to ISO 8601 format here.
    print(c1)
    # {
    #   "date_field": "2022-01-03",
    #   "time_field": "15:45:00",
    #   "dt_field": "2023-01-02T02:03:52"
    # }

    # Confirm that we can load the serialized data as expected.
    c2 = MyClass.from_json(c1.to_json())

    # Assert that the data is the same
    assert c1 == c2

Timezone-Aware Patterns
~~~~~~~~~~~~~~~~~~~~~~~

For *timezone-aware* patterned ``datetime`` and ``time``,
there are three choices:
    - :class:`AwarePattern` -- used primarily with ``typing.Annotated[...]``
    - :class:`AwareDateTimePattern`
    - :class:`AwareTimePattern`

Here is usage of that:

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

    d = {'my_aware_dt': '6:15:45',
         'key': '10-2020-15:30-UTC'}

    c = fromdict(MyClass, d)
    pprint(c)
    #> MyClass(my_aware_dt=datetime.time(6, 15, 45, tzinfo=zoneinfo.ZoneInfo(key='Europe/London')),
    #          my_aware_dt2=datetime.datetime(2020, 10, 1, 15, 30, tzinfo=zoneinfo.ZoneInfo(key='Asia/Tokyo')))

    print(asdict(c))
    # {'my_aware_dt': '06:15:45', 'key': '2020-10-01T15:30:00+09:00'}

    # check data validity
    assert c == fromdict(MyClass, asdict(c))

UTC Patterns
~~~~~~~~~~~~

For *UTC* patterned ``datetime`` and ``time``,
there are three choices:
    - :class:`UTCPattern` -- used primarily with ``typing.Annotated[...]``
    - :class:`UTCDateTimePattern`
    - :class:`UTCTimePattern`

Example:

.. code:: python3

    from dataclasses import dataclass
    from pprint import pprint
    from typing import Annotated

    from dataclass_wizard import JSONPyWizard
    from dataclass_wizard.v1 import UTCTimePattern, UTCDateTimePattern, Alias


    @dataclass
    class MyClass(JSONPyWizard):
        class _(JSONPyWizard.Meta):
            v1 = True

        my_utc_time: UTCTimePattern['%H:%M:%S']
        my_utc_dt: Annotated[UTCDateTimePattern['%m-%Y-%H:%M-%Z'], Alias('key')]


    d = {'my_utc_time': '6:15:45',
         'key': '10-2020-15:30-UTC'}

    c = MyClass.from_dict(d)
    pprint(c)
    #> MyClass(my_utc_time=datetime.time(6, 15, 45, tzinfo=zoneinfo.ZoneInfo(key='UTC')),
    #          my_utc_dt=datetime.datetime(2020, 10, 1, 15, 30, tzinfo=zoneinfo.ZoneInfo(key='UTC')))

    print(c.to_dict())
    # {'my_utc_time': '06:15:45Z', 'key': '2020-10-01T15:30:00Z'}

    # check data validity
    assert c == MyClass.from_dict(c.to_dict())

Containers of Date and Time
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Suppose the type annotation for a dataclass field is more complex -- for example,
an annotation might be a ``list[date]`` instead, representing an ordered
collection of :class:`date` objects.

In such cases, you can use ``Annotated`` along with :func:`Pattern`, as shown
below. Note that this also allows you to more easily annotate using a subtype
of date-time, for example a subclass of :class:`date` if so desired.

.. code:: python3

    from dataclasses import dataclass
    from datetime import datetime, time

    from typing import Annotated

    from dataclass_wizard import JSONPyWizard
    from dataclass_wizard.v1 import Pattern, AwarePattern


    class MyTime(time):
        """A custom `time` subclass"""
        def get_hour(self):
            return self.hour


    @dataclass
    class MyClass(JSONPyWizard):
        class _(JSONPyWizard.Meta):
            v1 = True

        time_field: Annotated[list[MyTime], Pattern['%I:%M %p']]
        dt_mapping: Annotated[dict[int, datetime], AwarePattern('US/Pacific', '%b.%d.%y %H,%M,%S')]


    data = {'time_field': ['3:45 PM', '1:20 am', '12:30 pm'],
            'dt_mapping': {'1133': 'Jan.2.20 15,20,57',
                           '5577': 'Nov.27.23 2,52,11'},
            }

    # Deserialize the data into a `MyClass` object
    c1 = MyClass.from_dict(data)

    print('Deserialized object:\n', c1)
    #  MyClass(time_field=[MyTime(15, 45), MyTime(1, 20), MyTime(12, 30)],
    #         dt_mapping={1133: datetime.datetime(2020, 1, 2, 15, 20, 57, tzinfo=zoneinfo.ZoneInfo(key='US/Pacific')),
    #                     5577: datetime.datetime(2023, 11, 27, 2, 52, 11, tzinfo=zoneinfo.ZoneInfo(key='US/Pacific'))})

    # Print the prettified JSON representation. Note that date/times are
    # converted to ISO 8601 format here.
    print(c1.to_json(indent=2))
    # {
    #   "time_field": [
    #     "15:45:00",
    #     "01:20:00",
    #     "12:30:00"
    #   ],
    #   "dt_mapping": {
    #     "1133": "2020-01-02T15:20:57-08:00",
    #     "5577": "2023-11-27T02:52:11-08:00"
    #   }
    # }

    # Confirm that we can load the serialized data as expected.
    c2 = MyClass.from_json(c1.to_json())

    # Assert that the data is the same
    assert c1 == c2


.. _ISO 8601: https://en.wikipedia.org/wiki/ISO_8601
.. _much faster: https://stackoverflow.com/questions/13468126/a-faster-strptime
.. See: https://stackoverflow.com/a/4836544/10237506
.. |another format| replace:: *another* format
.. _another format: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
