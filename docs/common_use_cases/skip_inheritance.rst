Skip the Class Inheritance
--------------------------

It is important to note that the main purpose of sub-classing from
``JSONWizard`` Mixin class is to provide helper methods like :meth:`from_dict`
and :meth:`to_dict`, which makes it much more convenient and easier to load or
dump your data class from and to JSON.

That is, it's meant to *complement* the usage of the ``dataclass`` decorator,
rather than to serve as a drop-in replacement for data classes, or to provide type
validation for example; there are already excellent libraries like `pydantic`_ that
provide these features if so desired.

However, there may be use cases where we prefer to do away with the class
inheritance model introduced by the Mixin class. In the interests of convenience
and also so that data classes can be used *as is*, the Dataclass
Wizard library provides the helper functions :func:`fromlist` and :func:`fromdict`
for de-serialization, and :func:`asdict` for serialization. These functions also
work recursively, so there is full support for nested dataclasses -- just as with
the class inheritance approach.

Here is an example to demonstrate the usage of these helper functions:

.. code:: python3

    from dataclasses import dataclass
    from datetime import datetime
    from typing import List, Optional, Union

    from dataclass_wizard import fromdict, asdict, DumpMeta


    @dataclass
    class Container:
        id: int
        created_at: datetime
        my_elements: List['MyElement']


    @dataclass
    class MyElement:
        order_index: Optional[int]
        status_code: Union[int, str]


    source_dict = {'id': '123',
                   'createdAt': '2021-01-01 05:00:00Z',
                   'myElements': [
                       {'orderIndex': 111, 'statusCode': '200'},
                       {'order_index': '222', 'status_code': 404}
                   ]}

    # De-serialize the JSON dictionary object into a `Container` instance.
    c = fromdict(Container, source_dict)

    print(repr(c))
    # prints:
    #   Container(id=123, created_at=datetime.datetime(2021, 1, 1, 5, 0), my_elements=[MyElement(order_index=111, status_code='200'), MyElement(order_index=222, status_code=404)])

    # (Optional) Set up dump config for the inner class, as unfortunately there's
    # no option currently to have the meta config apply in a recursive fashion.
    _ = DumpMeta(MyElement, key_transform='SNAKE')

    # Serialize the `Container` instance to a Python dict object with a custom
    # dump config, for example one which converts field names to snake case.
    json_dict = asdict(c, DumpMeta(Container,
                                   key_transform='SNAKE',
                                   marshal_date_time_as='TIMESTAMP'))

    expected_dict = {'id': 123,
                     'created_at': 1609477200,
                     'my_elements': [
                         {'order_index': 111, 'status_code': '200'},
                         {'order_index': 222, 'status_code': 404}
                     ]}

    # Assert that we get the expected dictionary object.
    assert json_dict == expected_dict


.. _`pydantic`: https://pydantic-docs.helpmanual.io/
