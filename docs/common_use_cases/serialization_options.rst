.. currentmodule:: dataclass_wizard

Serialization Options
=====================

.. note::

    **Future Behavior Change**: Starting in ``v1.0.0``, keys will no longer be automatically converted to `camelCase`.
    Instead, the default behavior will match the field names defined in the dataclass.

    To preserve the current `camelCase` conversion, you can explicitly enable it using :class:`JSONPyWizard`.

    For a deeper dive into upcoming changes and new features introduced in **V1 Opt-in**, refer to the
    `Field Guide to V1 Opt‐in`_.

.. _Field Guide to V1 Opt‐in: https://github.com/rnag/dataclass-wizard/wiki/Field-Guide-to-V1-Opt%E2%80%90in

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

    from dataclass_wizard import JSONWizard


    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            skip_defaults = True

        my_str: str
        other_str: str = 'any value'
        optional_str: str = None
        my_list: list[str] = field(default_factory=list)
        my_dict: defaultdict[str, list[float]] = field(
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

"Skip If" Functionality
~~~~~~~~~~~~~~~~~~~~~~~

The **Dataclass Wizard** offers powerful, configurable options to **skip serializing fields** under specific conditions. This functionality is available both **globally** (via the `Meta` class) and **per-field** (using type annotations or `dataclasses.Field` wrappers).

Overview
--------

You can:
- **Globally skip** fields that match a condition using ``Meta.skip_if`` or ``Meta.skip_defaults_if``.
- **Conditionally skip fields individually** using type annotations with ``SkipIf``, or the ``skip_if_field`` wrapper for ``dataclasses.Field``.

**Built-in Helpers**: For added flexibility, use helpers like ``IS_TRUTHY``, ``IS_FALSY``, and others for common conditions.
**Note**: ``SkipIfNone`` is an alias for ``SkipIf(IS(None))``.

1. Global Field Skipping
------------------------

1.1 Skip Any Field Matching a Condition
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the ``skip_if`` option in your dataclass's ``Meta`` configuration to skip fields that meet a specific condition during serialization.

.. code-block:: python3

    from dataclasses import dataclass
    from dataclass_wizard import JSONWizard, IS_NOT

    @dataclass
    class Example(JSONWizard):
        class _(JSONWizard.Meta):
            skip_if = IS_NOT(True)  # Skip if the field is not `True`.

        my_str: 'str | None'
        my_bool: bool
        other_bool: bool = False

    ex = Example(my_str=None, my_bool=True)
    assert ex.to_dict() == {'my_bool': True}  # Only `my_bool` is serialized.

1.2 Skip Fields with Default Values Matching a Condition
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the ``skip_defaults_if`` option to skip serializing **fields with default values** that match a condition.

.. code-block:: python3

    from dataclasses import dataclass
    from dataclass_wizard import JSONWizard, IS

    @dataclass
    class Example(JSONWizard):
        class _(JSONWizard.Meta):
            skip_defaults_if = IS(None)  # Skip fields with default value `None`.

        my_str: str | None
        my_bool: bool = False

    ex = Example(my_str=None)
    assert ex.to_dict() == {'my_str': None}  # Explicitly set `None` values are not skipped.

1.3 Skip Fields Based on Truthy/Falsy Values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the ``IS_TRUTHY`` and ``IS_FALSY`` helpers for conditions based on truthiness or falsiness.

.. code-block:: python3

    from dataclasses import dataclass
    from dataclass_wizard import JSONWizard, IS_TRUTHY

    @dataclass
    class Example(JSONWizard):
        class _(JSONWizard.Meta):
            skip_if = IS_TRUTHY()  # Skip fields that evaluate to True.

        my_bool: bool
        my_none: None = None

    ex = Example(my_bool=True, my_none=None)
    assert ex.to_dict() == {'my_none': None}  # Only `my_none` is serialized.

2. Per-Field Skipping
---------------------

For finer control, fields can be skipped **individually** using type annotations with ``SkipIf`` or by wrapping ``dataclasses.Field`` with ``skip_if_field``.

2.1 Using Type Annotations
^^^^^^^^^^^^^^^^^^^^^^^^^^

You can use ``SkipIf`` in conjunction with ``Annotated`` to conditionally skip individual fields during serialization.

.. code-block:: python3

    from dataclasses import dataclass
    from typing import Annotated
    from dataclass_wizard import JSONWizard, SkipIf, IS

    @dataclass
    class Example(JSONWizard):
        my_str: Annotated['str | None', SkipIf(IS(None))]  # Skip if `my_str is None`.

2.2 Using ``skip_if_field`` Wrapper
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``skip_if_field`` to add conditions directly to ``dataclasses.Field``:

.. code-block:: python3

    from dataclasses import dataclass
    from dataclass_wizard import JSONWizard, skip_if_field, EQ

    @dataclass
    class Example(JSONWizard):
        third_str: 'str | None' = skip_if_field(EQ(''), default=None)  # Skip if empty string.

2.3 Combined Example
^^^^^^^^^^^^^^^^^^^^

Both approaches can be used together to achieve granular control:

.. code-block:: python3

    from dataclasses import dataclass
    from typing import Annotated
    from dataclass_wizard import JSONWizard, SkipIf, skip_if_field, IS, EQ

    @dataclass
    class Example(JSONWizard):
        my_str: Annotated['str | None', SkipIf(IS(None))]  # Skip if `my_str is None`.
        third_str: 'str | None' = skip_if_field(EQ(''), default=None)  # Skip if `third_str` is ''.

    ex = Example(my_str='test', third_str='')
    assert ex.to_dict() == {'my_str': 'test'}

Key Classes and Utilities
-------------------------

- ``SkipIf``: Adds skipping logic to a field via type annotations.
- ``skip_if_field``: Wraps ``dataclasses.Field`` for inline skipping logic.
- **Condition Helpers**:

  - ``IS``, ``IS_NOT``: Skip based on identity.
  - ``EQ``, ``NE``, ``LT``, ``LE``, ``GT``, ``GE``: Skip based on comparison.
  - ``IS_TRUTHY``, ``IS_FALSY``: Skip fields based on truthiness or falsiness.
  - **Alias**: ``SkipIfNone`` is equivalent to ``SkipIf(IS(None))``.

Performance and Clarity
-----------------------

This design ensures both **performance** and **self-documenting code**, while enabling complex serialization rules effortlessly.
