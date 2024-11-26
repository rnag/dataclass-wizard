Easier Debug Mode
=================

The ``dataclass-wizard`` library provides a convenient way to enable logging for debugging. While one approach is to enable the ``debug_enabled`` flag in ``JSONWizard.Meta``, this requires proper setup of the ``logging`` module, as shown below:

.. code:: python3

    import logging
    from dataclasses import dataclass
    from dataclass_wizard import JSONWizard

    # Manually set logging level
    logging.basicConfig(level=logging.DEBUG)

    @dataclass
    class MyClass(JSONWizard):
        class _(JSONWizard.Meta):
            debug_enabled = True

Simpler Debugging with ``debug``
--------------------------------

A simpler and more flexible approach is to pass the ``debug`` argument directly when subclassing ``JSONWizard``. This not only sets the ``logging.basicConfig(level=logging.DEBUG)`` automatically, but also lets you customize the log level by passing a value like ``logging.INFO`` or ``logging.DEBUG``:

.. code:: python3

    import logging
    from dataclasses import dataclass
    from dataclass_wizard import JSONWizard

    @dataclass
    class MyClass(JSONWizard, debug=logging.INFO):
        class _(JSONWizard.Meta):
            skip_defaults = True
            key_transform_with_dump = 'PASCAL'

        my_bool: bool
        my_int: int = 2

        @classmethod
        def _pre_from_dict(cls, o):
            o['myBool'] = True
            return o

    # Setting `debug=logging.INFO` automatically configures the logger:
    # logging.getLogger('dataclass_wizard').setLevel(logging.INFO)

    c = MyClass.from_dict({'myBool': 'false'})
    print(c)
    # {
    #   "MyBool": true
    # }

Key Points
----------

1. **Automatic Logging Setup**:
   When ``debug=True`` (or ``debug=logging.DEBUG``, etc.), ``logging.basicConfig(level=logging.DEBUG)`` is automatically configured for the library.

2. **Custom Log Levels**:
   - Pass a **boolean** (``True``) to enable ``DEBUG`` level logs.
   - Pass a **logging level** (e.g., ``logging.INFO``, ``logging.WARNING``) to set a custom log level.
     This internally maps to ``JSONWizard.Meta.debug_enabled``, configuring the library’s logger with the specified level.

3. **Library Logger**:
   The library logger (``dataclass_wizard``) is dynamically set via ``logging.getLogger('dataclass_wizard').setLevel(input_level)`` based on the ``debug`` argument.

4. **Convenient Defaults**:
   No need to manually configure ``logging.basicConfig`` or adjust log levels outside your class definition.

Examples of Log Levels
----------------------

.. code:: python3

    import logging
    from dataclasses import dataclass
    from dataclass_wizard import JSONWizard

    @dataclass
    class DebugExample(JSONWizard, debug=True):
        ...  # DEBUG level (default for boolean True)

    @dataclass
    class InfoExample(JSONWizard, debug="INFO"):
        ...  # INFO level

    @dataclass
    class WarningExample(JSONWizard, debug=logging.WARNING):
        ...  # WARNING level
