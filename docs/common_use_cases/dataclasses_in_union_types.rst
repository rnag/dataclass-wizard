Dataclasses in :class:`Union` types
===================================

Suppose that a dataclass field is type-annotated like ``Union[Class1, Class2]``. Unless the input
data is *specifically* either a :class:`Class1` or :class:`Class2` instance, the data won't be
de-serialized as expected. However, the good news is that there is a simple enough workaround
in this scenario.

As of v0.14.0, the ``dataclass-wizard`` supports declaring dataclasses within ``Union`` types. Previously,
it did not support dataclasses within ``Union`` types at all, which was kind of a glaring omission,
and something on my "to-do" list of things to (eventually) add support for.

As of the latest, it should now support defining dataclasses as ``Union`` type arguments. The reason
it did not *generally* work before, is because the data being de-serialized is often a JSON object,
which only knows simple types such as arrays and  dictionaries, for example. A ``dict`` type would
not otherwise match any of the ``Union[Data1, Data2]`` types, even if the object had all the
correct dataclass fields as keys. This is simply because it doesn't compare the ``dict`` object
against each of the dataclass fields of models in the ``Union`` arguments, though that might
change in a future release.

So in any case, here is a simple example to demonstrate the usage of dataclasses in
``Union`` types, using a class inheritance model with the :class:`JSONWizard` mixin class:

With Class Inheritance
~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~

Here is the same example as above, but with relying solely on ``dataclasses``, without using
any special class inheritance model:


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
