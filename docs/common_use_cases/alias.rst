.. title:: Alias

Alias
=====

.. tip::

    :func:`Alias` and :func:`AliasPath` provide mechanisms to map JSON keys or nested paths to dataclass fields, enhancing serialization
    and deserialization in the ``dataclass-wizard`` library. These utilities build upon Python's :func:`dataclasses.field`, enabling
    custom mappings for more flexible and powerful data handling.

An alias is an alternative name for a field, used when de/serializing data. This feature is introduced in **v0.35.0**.

You can specify an alias in the following ways:

* Using :func:`Alias` and passing alias(es) to ``all``, ``load``, or ``dump``

* Using ``Meta`` setting ``field_to_alias``

For examples of how to use ``all``, ``load``, and ``dump``, see `Field Aliases`_.

Field Aliases
-------------

Field aliases allow mapping one or more JSON key names to a dataclass field for de/serialization. This feature
provides flexibility when working with JSON structures that may not directly match your Python dataclass definitions.

Defining Aliases
~~~~~~~~~~~~~~~~

There are three primary ways to define an alias:

* **Single alias for all operations**
    * ``Alias('foo')``

* **Separate aliases for de/serialization**
    * ``Alias(load='foo')`` for de-serialization
    * ``Alias(dump='foo')`` for serialization

The ``load`` and ``dump`` parameters enable fine-grained control over how fields are handled
during deserialization and serialization, respectively. If both are provided, the field can
behave differently depending on the operation.

Examples of Field Aliases
~~~~~~~~~~~~~~~~~~~~~~~~~

Using a Single Alias
^^^^^^^^^^^^^^^^^^^^

You can use a single alias for both serialization and deserialization by passing the alias name directly to :func:`Alias`:

.. code-block:: python3

    from dataclass_wizard import Alias, DataclassWizard


    class User(DataclassWizard):
        name: str = Alias('username')


    user = User.from_dict({'username': 'johndoe'})
    print(user)
    # > User(name='johndoe')
    print(user.to_dict())
    # > {'username': 'johndoe'}

Using Separate Aliases for Serialization and Deserialization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To define distinct aliases for `load` and `dump` operations:

.. code-block:: python3

    from dataclass_wizard import Alias, DataclassWizard


    class User(DataclassWizard):
        name: str = Alias(load='username', dump='user_name')


    user = User.from_dict({'username': 'johndoe'})
    print(user)
    # > User(name='johndoe')
    print(user.to_dict())
    # > {'user_name': 'johndoe'}

Skipping Fields During Serialization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To exclude a field during serialization, use the ``skip`` parameter:

.. code-block:: python3

    from dataclass_wizard import Alias, DataclassWizard


    class User(DataclassWizard):
        name: str = Alias('username', skip=True)


    user = User.from_dict({'username': 'johndoe'})
    print(user.to_dict())  # > {}

Advanced Usage
^^^^^^^^^^^^^^

Aliases can be combined with :obj:`typing.Annotated` to support complex scenarios. You can also use the ``field_to_alias`` meta-setting
for bulk aliasing:

.. code-block:: python3

    from typing import Annotated
    from dataclass_wizard import Alias, DataclassWizard


    class Test(DataclassWizard):
        class _(DataclassWizard.Meta):
            load_case = 'CAMEL'
            field_to_alias_dump = {
                'my_int': 'MyInt',
            }

        my_str: str = Alias(load=('a_str', 'other_str'))
        my_bool_test: Annotated[bool, Alias(dump='myDumpedBool')]
        my_int: int
        other_int: int = Alias(dump='DumpedInt')


    t = Test.from_dict({'other_str': 'test', 'myBoolTest': 'T', 'myInt': '123', 'otherInt': 321.0})
    print(t.to_dict())
    # > {'my_str': 'test', 'myDumpedBool': True, 'MyInt': 123, 'DumpedInt': 321}

Alias Paths
-----------

Maps one or more nested JSON paths to a dataclass field. See documentation on :func:`AliasPath` for more details.

**Examples**

Mapping multiple nested paths to a field::

    from dataclasses import dataclass
    from dataclass_wizard import fromdict, AliasPath


    @dataclass
    class Example:
        my_str: str = AliasPath('a.b.c.1', 'x.y["-1"].z', default="default_value")


    print(fromdict(Example, {'x': {'y': {'-1': {'z': 'some_value'}}}}))
    # > Example(my_str='some_value')

Using :obj:`typing.Annotated` with nested paths::

    from typing import Annotated
    from dataclass_wizard import AliasPath, DataclassWizard


    class Example(DataclassWizard):
        my_str: Annotated[str, AliasPath('my."7".nested.path.-321')]


    ex = Example.from_dict({'my': {'7': {'nested': {'path': {-321: 'Test'}}}}})
    print(ex)  # > Example(my_str='Test')
