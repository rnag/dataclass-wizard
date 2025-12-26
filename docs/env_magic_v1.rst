Env Magic (v1)
==============

The *Environment Wizard* (``EnvWizard``) is a dataclass mixin for loading
**typed configuration** from:

- environment variables
- ``.env`` files
- secret directories

It performs string-to-type coercion, validates input, and in v1 supports
**nested dataclasses**.

.. important::

   EnvWizard v1 is **opt-in**. If you do not enable it, v0 behavior applies.

.. hint::

   This page documents v1 concepts: explicit precedence, v1 aliasing, and
   nested dataclass support.

Why v1?
-------

In v0, environment lookup relied on implicit heuristics and cascading fallbacks.
That made behavior harder to reason about and customize safely.

v1 introduces:

- explicit environment precedence
- clearer aliasing rules (load vs dump)
- first-class nested dataclass support

Installation
------------

Install the base package:

.. code-block:: console

   pip install dataclass-wizard

Optional extras:

.. code-block:: console

   pip install dataclass-wizard[dotenv]
   pip install dataclass-wizard[tz]

Opting into v1
--------------

Enable v1 via the inner ``Meta`` class:

.. code-block:: python

   from dataclass_wizard.v1 import EnvWizard

   class Config(EnvWizard):
       class _(EnvWizard.Meta):
           v1 = True

       token: str

Or using ``EnvMeta``:

.. code-block:: python

    from dataclass_wizard import EnvMeta
    from dataclass_wizard.v1 import EnvWizard

    class Config(EnvWizard):
        token: str

    EnvMeta(v1=True).bind_to(Config)

Quick Start
-----------

.. code-block:: python

   import os
   from dataclass_wizard.v1 import EnvWizard

   os.environ.update({
       "APP_NAME": "Env Wizard",
       "MAX_CONNECTIONS": "10",
       "DEBUG": "true",
   })

   class AppConfig(EnvWizard):
       app_name: str
       max_connections: int
       debug: bool

   cfg = AppConfig()

   assert cfg.app_name == "Env Wizard"
   assert cfg.max_connections == 10
   assert cfg.debug is True

Environment Precedence
----------------------

v1 resolves values from multiple sources using an explicit precedence order.

Default precedence:

::

   Secrets → Environment → Dotenv

Later sources override earlier sources.

Customize precedence:

.. code-block:: python

    from dataclass_wizard.v1 import EnvWizard
    from dataclass_wizard.v1.enums import EnvPrecedence

    class Config(EnvWizard):
        class _(EnvWizard.Meta):
            v1 = True
            v1_env_precedence = EnvPrecedence.SECRETS_DOTENV_ENV

        token: str

Dotenv Support
--------------

Enable ``.env`` loading via ``Meta.env_file``:

.. code-block:: python

   class Config(EnvWizard):
       class _(EnvWizard.Meta):
           v1 = True
           env_file = True

       api_key: str

Custom paths are supported:

.. code-block:: python

   from pathlib import Path

   class Config(EnvWizard):
       class _(EnvWizard.Meta):
           v1 = True
           env_file = Path(".env.prod")

       db_host: str

If multiple files are provided, later files take precedence.

Secrets Directories
-------------------

Secrets directories treat **filenames as keys** and **file contents as values**.

.. code-block:: python

   class Config(EnvWizard):
       class _(EnvWizard.Meta):
           v1 = True
           secrets_dir = "/run/secrets"

       db_password: str

Field Aliases (v1)
------------------

Load-only aliases (recommended):

.. code-block:: python

   class Config(EnvWizard):
       class _(EnvWizard.Meta):
           v1 = True
           v1_field_to_env_load = {
               "db_url": ["DATABASE_URL", "DB_URL"],
           }

       db_url: str

Dump-only aliases:

.. code-block:: python

   class _(EnvWizard.Meta):
       v1_field_to_alias_dump = {
           "db_url": "databaseUrl",
       }

.. hint::

   Loading and dumping are intentionally separate concerns in v1.

Prefixes
--------

Static prefix:

.. code-block:: python

   class Config(EnvWizard):
       class _(EnvWizard.Meta):
           v1 = True
           env_prefix = "APP_"

       name: str

Dynamic override at runtime:

.. code-block:: python

   Config(_env_prefix="CUSTOM_")

Nested Dataclasses (v1)
-----------------------

v1 supports nested dataclasses out of the box.

.. code-block:: python

   class DB(EnvWizard):
       host: str
       port: int

   class Config(EnvWizard):
       class _(EnvWizard.Meta):
           v1 = True

       db: DB

Environment variables:

::

   DB_HOST=localhost
   DB_PORT=5432

Error Handling
--------------

Common errors include:

- ``MissingVars``: required value not found
- ``ParseError``: type conversion failed
- ``UnknownKeyError``: unknown key (if enabled)

Enable debug output:

.. code-block:: python

   class _(EnvWizard.Meta):
       v1_debug = True
