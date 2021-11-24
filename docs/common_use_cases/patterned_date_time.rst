Patterned Date and Time
=======================

Loading an `ISO 8601`_ format string into a :class:`date` / :class:`time` /
:class:`datetime` object is already handled as part of the de-serialization
process by default. For example, a date string in ISO format such as
``2022-01-17T21:52:18.000Z`` is correctly parsed to :class:`datetime` as expected.

However, what happens when you have a date string in |another format|_, such
as ``November 2, 2021``, and you want to load it to a :class:`date`
or :class:`datetime` object?

As of *v0.20.0*, the accepted solution is to use the builtin support for
parsing strings with custom date-time patterns; this internally calls
:meth:`datetime.strptime` to match input strings against a specified pattern.

There are two approaches (shown below) that can be used to specify custom patterns
for date-time strings. The simplest approach is to annotate fields as either
a :class:`DatePattern`, :class:`TimePattern`, or a :class:`DateTimePattern`.

.. note::
    The input date-time strings are parsed in the following sequence:

    - In case it's an `ISO 8601`_ format string, or a numeric timestamp,
      we attempt to parse with the default load function such as
      :func:`as_datetime`. Note that we initially parse strings using the
      builtin :meth:`fromisoformat` method, as this is `much faster`_ than
      using :meth:`datetime.strptime`. If the date string is matched, we
      immediately return the new date-time object.
    - Next, we parse with :meth:`datetime.strptime` by passing in the
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

    from typing_extensions import Annotated

    from dataclass_wizard import JSONWizard, Pattern, DatePattern, TimePattern


    @dataclass
    class MyClass(JSONWizard):
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
    #   "dateField": "2022-01-03",
    #   "timeField": "15:45:00",
    #   "dtField": "2023-01-02T02:03:52"
    # }

    # Confirm that we can load the serialized data as expected.
    c2 = MyClass.from_json(c1.to_json())

    # Assert that the data is the same
    assert c1 == c2

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
    from typing import List, Dict

    from typing_extensions import Annotated

    from dataclass_wizard import JSONWizard, Pattern


    class MyTime(time):
        """A custom `time` subclass"""
        def get_hour(self):
            return self.hour


    @dataclass
    class MyClass(JSONWizard):

        time_field: Annotated[List[MyTime], Pattern('%I:%M %p')]
        dt_mapping: Annotated[Dict[int, datetime], Pattern('%b.%d.%y %H,%M,%S')]


    data = {'time_field': ['3:45 PM', '1:20 am', '12:30 pm'],
            'dt_mapping': {'1133': 'Jan.2.20 15,20,57',
                           '5577': 'Nov.27.23 2,52,11'},
            }

    # Deserialize the data into a `MyClass` object
    c1 = MyClass.from_dict(data)

    print('Deserialized object:', repr(c1))
    # MyClass(time_field=[MyTime(15, 45), MyTime(1, 20), MyTime(12, 30)],
    #         dt_mapping={1133: datetime.datetime(2020, 1, 2, 15, 20, 57),
    #                     5577: datetime.datetime(2023, 11, 27, 2, 52, 11)})

    # Print the prettified JSON representation. Note that date/times are
    # converted to ISO 8601 format here.
    print(c1)
    # {
    #   "timeField": [
    #     "15:45:00",
    #     "01:20:00",
    #     "12:30:00"
    #   ],
    #   "dtMapping": {
    #     "1133": "2020-01-02T15:20:57",
    #     "5577": "2023-11-27T02:52:11"
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
