EnvWizard v0 → v1 Migration
===========================

This guide covers migrating from v0 behavior to v1.

Who should migrate?
-------------------

Migrate if you want:

- explicit environment precedence
- nested dataclass support in env loading
- clearer aliasing rules

If your v0 config is flat and stable, there is no urgency.

Step 1: Opt into v1
-------------------

.. code-block:: python

   class Config(EnvWizard):
       class _(EnvWizard.Meta):
           v1 = True

       token: str

Step 2: Turn on v1 debug (temporary)
------------------------------------

.. code-block:: python

   class _(EnvWizard.Meta):
       v1_debug = True

Step 3: Verify precedence assumptions
-------------------------------------

v1 uses explicit precedence. Default:

::

   Secrets → Environment → Dotenv

If your v0 behavior relied on dotenv overriding env vars, set precedence
explicitly in v1.

.. code-block:: python

   from dataclass_wizard import EnvPrecedence

   class _(EnvWizard.Meta):
       v1_env_precedence = EnvPrecedence.DOTENV_ENV_SECRETS

Step 4: Migrate aliases
-----------------------

v0 aliasing:

- ``field_to_env_var``

v1 aliasing:

- load-only: ``v1_field_to_env_load``
- dump-only: ``v1_field_to_alias_dump``

Example:

.. code-block:: python

   class _(EnvWizard.Meta):
       v1_field_to_env_load = {"db_url": ["DATABASE_URL", "DB_URL"]}
       v1_field_to_alias_dump = {"db_url": "databaseUrl"}

Step 5: Nested dataclasses
--------------------------

If you previously flattened configs due to v0 limitations, you can now
model them directly.

.. code-block:: python

   class DB(EnvWizard):
       host: str
       port: int

   class Config(EnvWizard):
       db: DB

Step 6: Remove debug
--------------------

Once stable, disable debug to avoid log noise.

.. code-block:: python

   class _(EnvWizard.Meta):
       v1_debug = False
