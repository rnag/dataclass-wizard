Dataclasses in :class:`Union` types
===================================

Suppose that a dataclass field is type-annotated like ``Union[Class1, Class2]``. Unless the input
data is *specifically* either a :class:`Class1` or :class:`Class2` instance, the data won't be
de-serialized as expected. However, the good news is that there is a simple enough workaround
in this scenario.

As of the *v0.14.0* release, the ``dataclass-wizard`` supports declaring dataclasses
within ``Union`` types. Previously, it did not support dataclasses within ``Union`` types
at all, which was kind of a glaring omission, and something on my "to-do" list of things
to (eventually) add support for.

There is now full support for defining dataclasses as ``Union`` type arguments. The
reason it did not *generally* work before, is because the data being de-serialized is
often a JSON object, which only knows simple types such as arrays and dictionaries,
for example. A ``dict`` type would not otherwise match any of the ``Union[Data1, Data2]``
types, even if the object had all the correct dataclass fields as keys. This is simply
because it doesn't attempt to de-serialize the ``dict`` object, in a *round robin* fashion,
into each of the dataclass models in the ``Union`` arguments -- though that might
change in a future release.

Auto-Assign Tags
~~~~~~~~~~~~~~~~

The *v0.19.0* release adds much-needed improvements when dataclass models are defined in
``Union`` types. It introduces support to *auto-generate* tags for a dataclass model
-- based on the class name -- as well as to specify a custom *tag key* that will be
present in the JSON object, which defaults to a special ``__tag__`` key otherwise.
These two options are controlled by the :attr:`auto_assign_tags` and :attr:`tag_key`
attributes (respectively) in the ``Meta`` config.

To illustrate a specific example, a JSON object such as
``{"oneOf": {"type": "A", ...}, ...}`` will now automatically map to a dataclass
instance ``A``, provided that the :attr:`tag_key` is correctly set to "type", and
the field ``one_of`` is annotated as a Union type in the ``A | B | ...`` syntax.

Let's start out with an example, which aims to demonstrate the simplest usage of
dataclasses in ``Union`` types.

.. note::
   The below example should work for **Python 3.7+** with the included ``__future__``
   import. Note that for 3.6, the ``A | B`` syntax -- which represents `Union`_ types --
   can be replaced with ``typing.Union[A, B]`` instead. Similarly, the subscripted
   ``dict`` usage can be substituted with a ``typing.Dict`` as needed.

.. code:: python3

    from __future__ import annotations

    from dataclasses import dataclass

    from dataclass_wizard import JSONWizard


    @dataclass
    class Container(JSONWizard):

        class _(JSONWizard.Meta):
            tag_key = 'my_tag'
            auto_assign_tags = True

        objects: list[A | B]


    @dataclass
    class A:
        my_int: int
        inner_obj: dict[str, C | D]


    @dataclass
    class B:
        my_int: int
        my_bool: bool = True


    @dataclass
    class C:
        ...


    @dataclass
    class D:
        ...


    data = {
        'objects': [
            {
                'my_tag': 'A', 'my_int': 42,
                'inner_obj': {
                    'c1': {'my_tag': 'C'},
                    'd1': {'my_tag': 'D'},
                    'c2': {'my_tag': 'C'}
                }
            },
            {
                'my_tag': 'B',
                'my_int': 3
            }
        ]
    }


    c = Container.from_dict(data)
    print(f'{c!r}')

    # True
    assert c == Container(objects=[
        A(my_int=42, inner_obj={'c1': C(), 'd1': D(), 'c2': C()}),
        B(my_int=3, my_bool=True)
    ])

    print(c.to_json(indent=2))
    # {
    #   "objects": [
    #     {
    #       "myInt": 42,
    #       "innerObj": {
    #         "c1": {
    #           "my_tag": "C"
    #         },
    #         "d1": {
    #           "my_tag": "D"
    #         },
    #         "c2": {
    #           "my_tag": "C"
    #         }
    #       },
    #       "my_tag": "A"
    #     },
    #     {
    #       "myInt": 3,
    #       "myBool": true,
    #       "my_tag": "B"
    #     }
    #   ]
    # }

    # True
    assert c == c.from_json(c.to_json())

.. _Union: https://docs.python.org/3/library/typing.html#typing.Union

Manually Assigning Tags
~~~~~~~~~~~~~~~~~~~~~~~

In some cases, it might be desirable to manually assign a tag to each dataclass. The main
use case for this is to future-proof it in the off case that we decide to *rename* a dataclass
defined in a ``Union`` type.

For instance, if dataclass ``A1`` is defined as a Union type and :attr:`auto_assign_tags`
is enabled in the Meta config, it will look for a tag field with a value of ``A1`` to
parse a dictionary as an ``A1`` object. If we later decide to rename the class to ``A2``
for example, the existing data that contains a value of ``A1`` will no longer map to
the ``A2`` dataclass; in such cases, a custom tag for the dataclass will need to be
specified, so that existing data can be de-serialized as expected.

With Class Inheritance
**********************

Here is a simple example to demonstrate the usage of dataclasses in ``Union`` types,
using a class inheritance model with the :class:`JSONWizard` mixin class:

.. code:: python3

    from abc import ABC
    from dataclasses import dataclass
    from typing import Union

    from dataclass_wizard import JSONWizard


    @dataclass
    class Data(ABC):
        """ base class for a Member """
        number: float


    class DataA(Data, JSONWizard):
        """ A type of Data"""

        class _(JSONWizard.Meta):
            """
            This defines a custom tag that uniquely identifies the dataclass.
            """
            tag = 'A'


    class DataB(Data, JSONWizard):
        """ Another type of Data """

        class _(JSONWizard.Meta):
            """
            This defines a custom tag that uniquely identifies the dataclass.
            """
            tag = 'B'


    @dataclass
    class Container(JSONWizard):
        """ container holds a subclass of Data """
        data: Union[DataA, DataB]


The usage is shown below, and is again pretty straightforward. It relies on a special ``__tag__`` key
set in a dictionary or JSON object to marshal it into the correct dataclass, based on the
:attr:`Meta.tag` value for that class, that we have set up above.

.. code:: python3

    print('== Load with DataA ==')

    input_dict = {
        'data': {
            'number': '1.0',
            '__tag__': 'A'
        }
    }

    # De-serialize the `dict` object to a `Container` instance.
    container = Container.from_dict(input_dict)

    print(repr(container))
    # prints:
    #   Container(data=DataA(number=1.0))

    # Show the prettified JSON representation of the instance.
    print(container)

    # Assert we load the correct dataclass from the annotated `Union` types
    assert type(container.data) == DataA

    print()

    print('== Load with DataB ==')

    # initialize container with DataB
    data_b = DataB(number=2.0)
    container = Container(data=data_b)

    print(repr(container))
    # prints:
    #   Container(data=DataB(number=2.0))

    # Show the prettified JSON representation of the instance.
    print(container)

    # Assert we load the correct dataclass from the annotated `Union` types
    assert type(container.data) == DataB

    # Assert we end up with the same instance when serializing and de-serializing
    # our data.
    string = container.to_json()
    assert container == Container.from_json(string)

Without Class Inheritance
*************************

Here is the same example as above, but with relying solely on ``dataclasses``, without
using any special class inheritance model:


.. code:: python3

    from abc import ABC
    from dataclasses import dataclass
    from typing import Union

    from dataclass_wizard import asdict, fromdict, LoadMeta


    @dataclass
    class Data(ABC):
        """ base class for a Member """
        number: float


    class DataA(Data):
        """ A type of Data"""


    class DataB(Data):
        """ Another type of Data """


    @dataclass
    class Container:
        """ container holds a subclass of Data """
        data: Union[DataA, DataB]


    # Setup tags for the dataclasses. This can be passed into either
    # `LoadMeta` or `DumpMeta`.
    LoadMeta(tag='A').bind_to(DataA)
    LoadMeta(tag='B').bind_to(DataB)

    # The rest is the same as before.

    # initialize container with DataB
    data = DataB(number=2.0)
    container = Container(data=data)

    print(repr(container))
    # prints:
    #   Container(data=DataB(number=2.0))

    # Assert we load the correct dataclass from the annotated `Union` types
    assert type(container.data) == DataB

    # Assert we end up with the same data when serializing and de-serializing.
    out_dict = asdict(container)
    assert container == fromdict(Container, out_dict)
