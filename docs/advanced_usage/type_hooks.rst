Type Hooks
==========

Sometimes you might want to customize the load and dump process for
(annotated) variable types, rather than for specific dataclass fields.
Type hooks are very useful and will let you do exactly that.

If you want to customize the load process for any type, extend from
``LoadMixin`` and override the ``load_to_...`` methods. To instead
customize the dump process for a type, extend from ``DumpMixin`` and
override the ``dump_with_...`` methods.

For instance, the default load process for ``Enum`` types is to look
them up by value, and similarly convert them back to strings using the
``value`` field. Suppose that you want to load ``Enum`` types using the
``name`` field instead.

The below example will do exactly that: it will convert using the *Enum*
``name`` field when ``from_dict`` is called, and use the default
approach to convert back using the *Enum* ``value`` field when
``to_dict`` is called; it additionally customizes the dump process for
strings, so they are converted to all uppercase when ``to_dict`` or
``to_json`` is called.

.. code:: python3

    from dataclasses import dataclass
    from enum import Enum
    from typing import Union, AnyStr, Type

    from dataclass_wizard import JSONSerializable, DumpMixin, LoadMixin
    from dataclass_wizard.type_def import N


    @dataclass
    class MyClass(JSONSerializable, LoadMixin, DumpMixin):

        my_str: str
        my_enum: 'MyEnum'

        def load_to_enum(o: Union[AnyStr, N], base_type: Type[Enum]) -> Enum:
            return base_type[o.replace(' ', '_')]

        def dump_with_str(o: str, *_):
            return o.upper()


    class MyEnum(Enum):
        NAME_1 = 'one'
        NAME_2 = 'two'


    data = {"my_str": "my string", "my_enum": "NAME 1"}

    c = MyClass.from_dict(data)
    print(repr(c))
    # prints:
    #   MyClass(my_str='my string', my_enum=<MyEnum.NAME_1: 'one'>)

    string = c.to_json()
    print(string)
    # prints:
    #   {"myStr": "MY STRING", "myEnum": "one"}
