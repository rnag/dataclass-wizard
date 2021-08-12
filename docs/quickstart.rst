==========
Quickstart
==========

Here are the supported features that Dataclass Wizard currently provides:

-  *JSON (de)serialization*: marshal dataclasses to/from JSON and Python
   ``dict`` objects.
-  *Field properties*: support for using properties with default
   values in dataclass instances.

The below is an quick demo of both of these features - how to marshal dataclasses to/from JSON and Python ``dict`` objects,
and declare and use field properties with default values.


.. code:: python3

    from dataclasses import dataclass, field
    from datetime import datetime
    from typing import Optional, List

    from dataclass_wizard import JSONSerializable, property_wizard


    @dataclass
    class MyClass(JSONSerializable, metaclass=property_wizard):

        my_str: Optional[str]
        list_of_int: List[int] = field(default_factory=list)
        # You can also define this as `my_dt`, however only the annotation
        # will carry over in that case, since the value is re-declared by
        # the property below. See also the 'Using Field Properties' section
        # in the docs for a more elegant approach.
        _my_dt: datetime = datetime(2000, 1, 1)

        @property
        def my_dt(self):
            """
            A sample `getter` which returns the datetime with year set as 2010
            """
            if self._my_dt is not None:
                return self._my_dt.replace(year=2010)
            return self._my_dt

        @my_dt.setter
        def my_dt(self, new_dt: datetime):
            """
            A sample `setter` which sets the inverse (roughly) of the `month` and `day`
            """
            self._my_dt = new_dt.replace(
                month=13 - new_dt.month,
                day=31 - new_dt.day)


    string = '''{"myStr": 42, "listOFInt": [1, "2", 3]}'''
    # Uses the default value for `my_dt`, with year=2000, month=1, day=1
    c = MyClass.from_json(string)

    print(repr(c))
    # prints:
    #   MyClass(my_str='42', list_of_int=[1, 2, 3], my_dt=datetime.datetime(2010, 12, 30, 0, 0))

    my_dict = {'My_Str': 'string', 'myDT': '2021-01-20T15:55:30Z'}
    c = MyClass.from_dict(my_dict)

    print(repr(c))
    # prints:
    #   MyClass(my_str='string', list_of_int=[], my_dt=datetime.datetime(2010, 12, 11, 15, 55, 30, tzinfo=datetime.timezone.utc))

    print(c.to_json())
    # prints:
    #   {"myStr": "string", "listOfInt": [], "myDt": "2010-12-11T15:55:30Z"}
