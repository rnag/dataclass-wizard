Map a Nested JSON Key Path to a Field
=====================================

.. note::
    **Important:** The current "nested path" functionality is being re-imagined.
    Please refer to the new docs for **V1 Opt-in** features, which introduces enhanced support for these use
    cases. For more details, see the `Field Guide to V1 Opt‐in`_ and the `V1 Alias`_ documentation.

    This change is part of the ongoing improvements in version ``v0.35.0+``, and the old functionality will no longer be maintained in future releases.

.. _Field Guide to V1 Opt‐in: https://github.com/rnag/dataclass-wizard/wiki/Field-Guide-to-V1-Opt%E2%80%90in
.. _V1 Alias: https://dcw.ritviknag.com/en/latest/common_use_cases/v1_alias.html

The ``dataclass-wizard`` library allows mapping deeply nested JSON paths to individual dataclass fields using a custom object path notation. This feature supports both :type:`Annotated` types and :class:`dataclasses.Field` for flexible and precise JSON deserialization.

.. role:: bc
  :class: bold-code

Basic Usage Example
-------------------

Define and use nested key paths for JSON deserialization with the :type:`Annotated` type and :func:`path_field`:

.. code:: python3

    from dataclasses import dataclass
    from dataclass_wizard import JSONWizard, KeyPath, path_field
    from typing import Annotated

    @dataclass
    class Example(JSONWizard):
        # Map using Annotated with KeyPath
        an_int: Annotated[int, KeyPath('data.nested.int')]
        # Map using path_field with a default value
        my_str: str = path_field(['metadata', 'info', 'name'], default='unknown')

- The field ``an_int`` maps to the nested JSON path ``data.nested.int``.
- The field ``my_str`` maps to the path ``metadata.info.name`` and defaults to ``'unknown'`` if the key is missing.

Expanded Example with JSON
---------------------------

Given the following JSON data:

.. code-block:: json

    {
        "data": {
            "nested": {
                "int": 42
            }
        },
        "metadata": {
            "info": {
                "name": "John Doe"
            }
        }
    }

Deserializing with the :meth:`from_dict` method:

.. code:: python3

    example = Example.from_dict({
        "data": {
            "nested": {
                "int": 42
            }
        },
        "metadata": {
            "info": {
                "name": "John Doe"
            }
        }
    })
    print(example.an_int)  # 42
    print(example.my_str)  # 'John Doe'

This example shows how JSON data is mapped to dataclass fields using the custom key paths.

Object Path Notation
--------------------

The object path notation used in :func:`KeyPath` and :func:`path_field` follows these rules:

- **Dot** (:bc:`.`) separates nested object keys.
- **Square brackets** (:bc:`[]`) access array elements or special keys.
- **Quotes** (:bc:`"`:bc:`'`) are required for keys with spaces, special characters, or reserved names.

.. |dot| raw:: html

    <code class="code docutils literal notranslate">.</code>

Examples:

1. **Simple Path**
   ``data.info.name``
   Accesses the ``name`` key inside the ``info`` object within ``data``.

2. **Array Indexing**
   ``data[0].value``
   Accesses the ``value`` field in the first element of the ``data`` array.

3. **Keys with Spaces or Special Characters**
   ``metadata["user name"].details``
   Accesses the ``details`` key inside ``metadata["user name"]``.

4. **Mixed Types**
   ``data[0]["user name"].info.age``
   Accesses ``age`` within ``info``, nested under ``"user name"`` in the first item of ``data``.

Path Parsing Examples
---------------------

These examples illustrate how the path is interpreted by ``KeyPath`` or ``path_field``:

- **Example 1: Boolean Path**

  .. code:: python3

      split_object_path('user[true]')

  Output: ``['user', True]``
  Accesses the ``True`` key in the ``user`` object. Booleans like ``True`` and ``False`` are automatically recognized.

- **Example 2: Integer Path**

  .. code:: python3

      split_object_path('data[5].value')

  Output: ``['data', 5, 'value']``
  Accesses ``value`` in the 6th element (index 5) of the ``data`` array.

- **Example 3: Floats in Paths**

  .. code:: python3

      split_object_path('data[0.25]')

  Output: ``['data', 0.25]``
  Floats are parsed correctly, although array indices are typically integers.

- **Example 4: Strings Without Quotes**

  .. code:: python3

      split_object_path('data[user_name]')

  Output: ``['data', 'user_name']``
  Valid identifiers are treated as strings even without quotes.

- **Example 5: Strings With Quotes**

  .. code:: python3

      split_object_path('data["user name"]')

  Output: ``['data', 'user name']``
  Quotes are required for keys with spaces or special characters.

- **Example 6: Mixed Types**

  .. code:: python3

      split_object_path('data[0]["user name"].info[age]')

  Output: ``['data', 0, 'user name', 'info', 'age']``
  Accesses ``age`` within ``info``, under ``user name``, in the first item of ``data``.

Handling Quotes
---------------

When keys or indices are wrapped in quotes, they are interpreted as strings. This is necessary for:

- Keys with spaces or special characters.
- Reserved words or identifiers that could otherwise cause parsing errors.

Example:

.. code:: python3

    split_object_path('data["123"].info')

Output: ``['data', '123', 'info']``
Here, ``"123"`` is treated as a string because of the quotes.

Best Practices
--------------

- Use :type:`Annotated` with :func:`KeyPath` for complex, deeply nested paths.
- Use :func:`path_field` for flexibility, defaults, or custom serialization.
- Keep paths concise and use quotes judiciously for clarity and correctness.
