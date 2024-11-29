`Env` Magic
===========

The *Environment Wizard* (or ``EnvWizard``) is a tool for effortlessly mapping environment variables to Python dataclass fields.
It offers built-in type validation, optional ``.env`` file support, and the ability to handle secret files, where the file name
serves as the key and its content as the value.

.. hint::

   These docs are inspired by and adapted from Pydantic's `Settings Management`_ documentation.

Key Features
------------
- **Auto Mapping**: Seamlessly maps environment variables to dataclass fields, using field names or aliases.
- **Dotenv Support**: Load environment variables from `.env` files or custom dotenv paths.
- **Secret Files**: Handle secret files where filenames act as keys and file contents as values.
- **Custom Configuration**: Configure variable prefixing, logging, and error handling.
- **Type Parsing**: Supports basic types (int, float, bool) and collections (list, dict, etc.).

Installation
------------
Install via `pip`:

.. code-block:: bash

   pip install dataclass-wizard

For `.env` file support, install the `python-dotenv` dependency with the `dotenv` extra:

.. code-block:: bash

   pip install dataclass-wizard[dotenv]

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
The `Meta` class provides additional configuration:

- `env_file`: Path to a dotenv file. Defaults to `True` for `.env` in the current directory.
- `env_prefix`: A string prefix to prepend to all variable names.
- `field_to_env_var`: Map fields to custom variable names.
- `debug_enabled`: Enable debug logging.
- `extra`: Handle unexpected fields. Options: `ALLOW`, `DENY`, `IGNORE`.

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
