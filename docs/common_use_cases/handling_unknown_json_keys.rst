Handling Unknown JSON Keys
###########################

When working with JSON data, you may encounter unknown or extraneous keys -- those that do not map to any defined dataclass fields.
This guide explains the default behavior, how to raise errors for unknown keys, and how to capture them using a ``CatchAll`` field.

Default Behavior
================

By default, when unknown JSON keys are encountered during the de-serialization process
(using ``from_dict`` or ``from_json``), the library emits a warning if *debug* mode is enabled
and logging is properly configured. These keys are ignored and not included in the resulting object.

However, you can customize this behavior to raise an error or capture unknown data.

Raising Errors on Unknown Keys
==============================

To enforce strict validation, you can configure the library to raise an error when
unknown keys are encountered. This is useful when you need to ensure that all JSON
data adheres to a specific schema.

Example: Raising an Error
--------------------------

The example below demonstrates how to configure the library to raise a
``UnknownJSONKey`` error when unknown keys are encountered.

.. code:: python3

    import logging
    from dataclasses import dataclass

    from dataclass_wizard import JSONWizard
    from dataclass_wizard.errors import UnknownJSONKey

    # Sets up application logging if we haven't already done so
    logging.basicConfig(level='INFO')


    @dataclass
    class Container(JSONWizard):
        class _(JSONWizard.Meta):
            debug_enabled = 'INFO'
            raise_on_unknown_json_key = True

        element: 'MyElement'


    @dataclass
    class MyElement:
        my_str: str
        my_float: float


    d = {
        'element': {
            'myStr': 'string',
            'my_float': '1.23',
            'my_bool': 'Testing'  # This key is not mapped to a known dataclass field!
        }
    }

    try:
        c = Container.from_dict(d)
    except UnknownJSONKey as e:
        print('Error:', e)

    # Expected Output:
    # >  Error: A JSON key is missing from the dataclass schema for class `MyElement`.
    #      unknown key: 'my_bool'
    #      dataclass fields: ['my_str', 'my_float']
    #      input JSON object: {"myStr": "string", "my_float": "1.23", "my_bool": "Testing"}

Capturing Unknown Keys with ``CatchAll``
========================================

Starting from version **v0.29**, unknown JSON keys can be captured into a designated field
using the ``CatchAll`` type. This allows you to store all unmapped key-value pairs for
later use, without discarding them.

Example: Capturing Unknown Keys
-------------------------------

The following example demonstrates how to use a ``CatchAll`` field to capture
unknown JSON keys during de-serialization.

.. code:: python

    from dataclasses import dataclass
    from dataclass_wizard import CatchAll, JSONWizard


    @dataclass
    class MyData(JSONWizard):
        class _(JSONWizard.Meta):
            skip_defaults = True

        my_str: str
        my_float: float
        extra_data: CatchAll = False  # Initialize with a default value.


    # Case 1: JSON object with extra data
    input_dict = {
        'my_str': "test",
        'my_float': 3.14,
        'my_other_str': "test!",
        'my_bool': True
    }

    data = MyData.from_dict(input_dict)

    print(data.extra_data)
    # > {'my_other_str': 'test!', 'my_bool': True}

    # Save back to JSON
    output_dict = data.to_dict()

    print(output_dict)
    # > {'myStr': 'test', 'myFloat': 3.14, 'my_other_str': 'test!', 'my_bool': True}

    # Case 2: JSON object without extra data
    input_dict = {
        'my_str': "test",
        'my_float': 3.14,
    }

    data = MyData.from_dict(input_dict)

    print(data.extra_data)
    # > False

Key Points:
-----------

- The ``extra_data`` field automatically captures all unknown JSON keys.
- If no extra data is present, the field defaults to ``False`` in this example.
- When serialized back to JSON, the extra data is retained.

Best Practices
==============

- Use ``raise_on_unknown_json_key`` when strict validation of JSON data is required.
- Use ``CatchAll`` to gracefully handle dynamic or extensible JSON data structures.
- Combine both features for advanced use cases, such as logging unknown keys
  while capturing them into a designated field.

---

This guide offers a comprehensive overview of handling unknown JSON keys.
By customizing the behavior, you can ensure your application works seamlessly
with various JSON structures, whether strict or dynamic.
