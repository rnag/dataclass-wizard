Examples
========

A (More) Complete Example
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python3

    from collections import defaultdict
    from dataclasses import dataclass, field
    from datetime import datetime
    from typing import Optional, List, Union, Dict, Any, NamedTuple, DefaultDict
    # Note: for Python 3.9+, you can import the following from `typing` instead
    from typing_extensions import Literal

    from dataclass_wizard import JSONSerializable


    @dataclass
    class MyTestClass(JSONSerializable):
        my_ledger: Dict[str, Any]
        the_answer_to_life: Optional[int]
        people: List['Person']
        is_enabled: bool = True


    @dataclass
    class Person:
        name: 'Name'
        age: int
        birthdate: datetime
        gender: Literal['M', 'F', 'N/A']
        occupation: Union[str, List[str]]
        hobbies: DefaultDict[str, List[str]] = field(
            default_factory=lambda: defaultdict(list))


    class Name(NamedTuple):
        """A person's name"""
        first: str
        last: str
        salutation: Optional[Literal['Mr.', 'Mrs.', 'Ms.', 'Dr.']] = 'Mr.'


    data = {
        'myLedger': {
            'Day 1': 'some details',
            'Day 17': ['a', 'sample', 'list']
        },
        'theAnswerTOLife': '42',
        'People': [
            {
                'name': ('Roberto', 'Fuirron'),
                'age': 21,
                'birthdate': '1950-02-28T17:35:20Z',
                'gender': 'M',
                'occupation': ['sailor', 'fisher'],
                'Hobbies': {'M-F': ('chess', 123, 'reading'), 'Sat-Sun': ['parasailing']}
            },
            {
                'name': ('Janice', 'Darr', 'Dr.'),
                'age': 45,
                'birthdate': '1971-11-05 05:10:59',
                'gender': 'F',
                'occupation': 'Dentist'
            }
        ]
    }

    c = MyTestClass.from_dict(data)

    print(repr(c))
    # prints the following result on a single line:
    #   MyTestClass(
    #       my_ledger={'Day 1': 'some details', 'Day 17': ['a', 'sample', 'list']},
    #       the_answer_to_life=42,
    #       people=[
    #           Person(
    #               name=Name(first='Roberto', last='Fuirron', salutation='Mr.'),
    #               age=21, birthdate=datetime.datetime(1950, 2, 28, 17, 35, 20, tzinfo=datetime.timezone.utc),
    #               gender='M', occupation=['sailor', 'fisher'],
    #               hobbies=defaultdict(<class 'list'>, {'M-F': ['chess', '123', 'reading'], 'Sat-Sun': ['parasailing']})
    #           ),
    #           Person(
    #               name=Name(first='Janice', last='Darr', salutation='Dr.'),
    #               age=45, birthdate=datetime.datetime(1971, 11, 5, 5, 10, 59),
    #               gender='F', occupation='Dentist',
    #               hobbies=defaultdict(<class 'list'>, {})
    #           )
    #       ], is_enabled=True)

    # calling `print` on the object invokes the `__str__` method, which will
    # pretty-print the JSON representation of the object by default. You can
    # also call the `to_json` method to print the JSON string on a single line.

    print(c)
    # prints:
    #     {
    #       "myLedger": {
    #         "Day 1": "some details",
    #         "Day 17": [
    #           "a",
    #           "sample",
    #           "list"
    #         ]
    #       },
    #       "theAnswerToLife": 42,
    #       "people": [
    #         {
    #           "name": [
    #             "Roberto",
    #             "Fuirron",
    #             "Mr."
    #           ],
    #           "age": 21,
    #           "birthdate": "1950-02-28T17:35:20Z",
    #           "gender": "M",
    #           "occupation": [
    #             "sailor",
    #             "fisher"
    #           ],
    #           "hobbies": {
    #             "M-F": [
    #               "chess",
    #               "123",
    #               "reading"
    #             ],
    #             "Sat-Sun": [
    #               "parasailing"
    #             ]
    #           }
    #         },
    #         {
    #           "name": [
    #             "Janice",
    #             "Darr",
    #             "Dr."
    #           ],
    #           "age": 45,
    #           "birthdate": "1971-11-05T05:10:59",
    #           "gender": "F",
    #           "occupation": "Dentist",
    #           "hobbies": {}
    #         }
    #       ],
    #       "isEnabled": true
    #     }
