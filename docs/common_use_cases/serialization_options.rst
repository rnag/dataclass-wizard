Serialization Options
=====================

The following parameters can be used to fine-tune and control how the serialization of a
dataclass instance to a Python ``dict`` object or JSON string is handled.

Skip Defaults
~~~~~~~~~~~~~

A common use case is skipping fields with default values - based on the ``default``
or ``default_factory`` argument to :func:`dataclasses.field` - in the serialization
process.

The attribute ``skip_defaults`` in the inner :class:`Meta` class can be enabled, to exclude
such field values from serialization.The :meth:`to_dict` method (or the :func:`asdict` helper
function) can also be passed an ``exclude`` argument, containing a list of one or more
dataclass field names to exclude from the serialization process. An example of both these
approaches is shown below.

.. code:: python3

    from collections import defaultdict
    from dataclasses import field, dataclass
    from typing import DefaultDict, List

    from dataclass_wizard import JSONWizard


    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            skip_defaults = True

        my_str: str
        other_str: str = 'any value'
        optional_str: str = None
        my_list: List[str] = field(default_factory=list)
        my_dict: DefaultDict[str, List[float]] = field(
            default_factory=lambda: defaultdict(list))


    print('-- Load (Deserialize)')
    c = MyClass('abc')
    print(f'Instance: {c!r}')

    print('-- Dump (Serialize)')
    string = c.to_json()
    print(string)

    assert string == '{"myStr": "abc"}'

    print('-- Dump (with `skip_defaults=False`)')
    print(c.to_dict(skip_defaults=False))

Exclude Fields
~~~~~~~~~~~~~~

You can also exclude specific dataclass fields (and their values) from the serialization
process. There are two approaches that can be used for this purpose:

* The argument ``dump=False`` can be passed in to the :func:`json_key` and :func:`json_field`
  helper functions. Note that this is a more permanent option, as opposed to the one
  below.

* The :meth:`to_dict` method (or the :func:`asdict` helper function ) can be passed
  an ``exclude`` argument, containing a list of one or more dataclass field names
  to exclude from the serialization process.

Additionally, here is an example to demonstrate usage of both these approaches:

.. code:: python3

    from dataclasses import dataclass
    from typing import Annotated

    from dataclass_wizard import JSONWizard, json_key, json_field


    @dataclass
    class MyClass(JSONWizard):

        my_str: str
        my_int: int
        other_str: Annotated[str, json_key('AnotherStr', dump=False)]
        my_bool: bool = json_field('TestBool', dump=False)


    data = {'MyStr': 'my string',
            'myInt': 1,
            'AnotherStr': 'testing 123',
            'TestBool': True}

    print('-- From Dict')
    c = MyClass.from_dict(data)
    print(f'Instance: {c!r}')

    # dynamically exclude the `my_int` field from serialization
    additional_exclude = ('my_int',)

    print('-- To Dict')
    out_dict = c.to_dict(exclude=additional_exclude)
    print(out_dict)

    assert out_dict == {'myStr': 'my string'}
