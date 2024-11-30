`Env` Magic
===========

The *Environment Wizard* (or ``EnvWizard``) is a powerful Mixin class for effortlessly mapping environment variables and ``.env`` files to strongly-typed Python dataclass fields.

It provides built-in type validation, automatic string-to-type conversion, and the ability to handle secret files, where the file name serves as the key and its content as the value.

Additionally, :class:`EnvWizard` supports type hinting and automatically applies the ``@dataclass`` decorator to your subclasses.

.. hint::

   These docs are inspired by and adapted from Pydantic's `Settings Management`_ documentation.

Key Features
------------
- **Auto Mapping**: Seamlessly maps environment variables to dataclass fields, using field names or aliases.
- **Dotenv Support**: Load environment variables from ``.env`` files or custom dotenv paths.
- **Secret Files**: Handle secret files where filenames act as keys and file contents as values.
- **Custom Configuration**: Configure variable prefixing, logging, and error handling.
- **Type Parsing**: Supports basic types (int, float, bool) and collections (list, dict, etc.).

Installation
------------
Install via ``pip``:

.. code-block:: console

   $ pip install dataclass-wizard

For ``.env`` file support, install the ``python-dotenv`` dependency with the ``dotenv`` extra:

.. code-block:: console

   $ pip install dataclass-wizard[dotenv]

.. _Settings Management: https://docs.pydantic.dev/latest/concepts/pydantic_settings
.. _python-dotenv: https://saurabh-kumar.com/python-dotenv/

Quick Start
-----------
Define your environment variables and map them using EnvWizard:

.. code-block:: python

   import os
   from dataclass_wizard import EnvWizard

   # Set environment variables
   # or:
   #   export APP_NAME='...'
   os.environ.update({
       'APP_NAME': 'Env Wizard',
       'MAX_CONNECTIONS': '10',
       'DEBUG_MODE': 'true'
   })

   # Define the dataclass
   class AppConfig(EnvWizard):
       app_name: str
       max_connections: int
       debug_mode: bool

   # Instantiate and use
    config = AppConfig()
    print(config.app_name)    #> Env Wizard
    print(config.debug_mode)  #> True
    assert config.max_connections == 10

    # Override with keyword arguments
    config = AppConfig(app_name='Dataclass Wizard Rocks!', debug_mode='false')
    print(config.app_name)    #> Dataclass Wizard Rocks!
    assert config.debug_mode is False

Advanced Usage
--------------
**Handling Missing Variables**

If required variables are not set, `EnvWizard` raises a `MissingVars` exception. Provide defaults for optional fields:

.. code-block:: python

   class AppConfig(EnvWizard):
       app_name: str
       max_connections: int = 5
       debug_mode: bool = False

**Dotenv Support**

Load environment variables from a ``.env`` file by enabling ``Meta.env_file``:

.. code-block:: python

   class AppConfig(EnvWizard):
       class _(EnvWizard.Meta):
           env_file = True

       app_name: str
       max_connections: int
       debug_mode: bool

**Custom Field Mappings**

Map environment variables to differently named fields using ``json_field`` or ``Meta.field_to_env_var``:

.. code-block:: python

   class AppConfig(EnvWizard):
       class _(EnvWizard.Meta):
           field_to_env_var = {'max_conn': 'MAX_CONNECTIONS'}

       app_name: str
       max_conn: int

**Prefixes**

Use a static or dynamic prefix for environment variable keys:

.. code-block:: python

   class AppConfig(EnvWizard):
       class _(EnvWizard.Meta):
           env_prefix = 'APP_'

       name: str = json_field('NAME')
       debug: bool

   # Prefix is applied dynamically
   config = AppConfig(_env_prefix='CUSTOM_')

Configuration Options
---------------------
The :class:`Meta` class provides additional configuration:

- :attr:`env_file`: Path to a dotenv file. Defaults to `True` for `.env` in the current directory.
- :attr:`env_prefix`: A string prefix to prepend to all variable names.
- :attr:`field_to_env_var`: Map fields to custom variable names.
- :attr:`debug_enabled`: Enable debug logging.
- :attr:`extra`: Handle unexpected fields. Options: ``ALLOW``, ``DENY``, ``IGNORE``.

Error Handling
--------------
- **MissingVars**: Raised when required fields are missing.
- **ParseError**: Raised for invalid values (e.g., converting `abc` to `int`).
- **ExtraData**: Raised when extra fields are passed (default behavior).

Examples
--------
**Basic Example**

.. code-block:: python

   import os
   from dataclass_wizard import EnvWizard

   os.environ['API_KEY'] = '12345'

   class Config(EnvWizard):
       api_key: str

   config = Config()
   print(config.api_key)  # Output: 12345

**Dotenv with Paths**

.. code-block:: python

   from pathlib import Path
   from dataclass_wizard import EnvWizard

   class Config(EnvWizard):
       class _(EnvWizard.Meta):
           env_file = Path('/path/to/.env')

       db_host: str
       db_port: int

**Complete Example**

Here is a more complete example of using :class:`EnvWizard` to
load environment variables into a dataclass schema:

.. code:: python3

    from os import environ
    from datetime import datetime, time
    from typing import NamedTuple
    try:
        from typing import TypedDict
    except ImportError:
        from typing_extensions import TypedDict

    from dataclass_wizard import EnvWizard

    # ideally these variables will be set in the environment, like so:
    #   $ export MY_FLOAT=1.23

    environ.update(
        myStr='Hello',
        my_float='432.1',
        # lists/dicts can also be specified in JSON format
        MyTuple='[1, "2"]',
        Keys='{ "k1": "false", "k2": "true" }',
        # or in shorthand format...
        MY_PENCIL='sharpened=Y,  uses_left = 3',
        My_Emails='  first_user@abc.com ,  second-user@xyz.org',
        SOME_DT_VAL='1651077045',  # 2022-04-27T12:30:45
    )


    class Pair(NamedTuple):
        first: str
        second: int


    class Pencil(TypedDict):
        sharpened: bool
        uses_left: int


    class MyClass(EnvWizard):

        class _(EnvWizard.Meta):
            field_to_env_var = {
                'my_dt': 'SOME_DT_VAL',
            }

        my_str: str
        my_float: float
        my_tuple: Pair
        keys: dict[str, bool]
        my_pencil: Pencil
        my_emails: list[str]
        my_dt: datetime
        my_time: time = time.min

    c = MyClass()

    print('Class Fields:')
    print(c.dict())
    # {'my_str': 'Hello', 'my_float': 432.1, ...}

    print()

    print('JSON:')
    print(c.to_json(indent=2))
    # {
    #   "my_str": "Hello",
    #   "my_float": 432.1,
    # ...

    assert c.my_pencil['uses_left'] == 3
    assert c.my_dt.isoformat() == '2022-04-27T16:30:45+00:00'

This code highlights the ability to:

- Load variables from the environment or ``.env`` files.
- Map fields to specific environment variable names using :attr:`field_to_env_var`.
- Support complex types such as :class:`NamedTuple`, :class:`TypedDict`, and more.
