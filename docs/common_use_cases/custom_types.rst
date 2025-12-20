Custom or Unsupported Types
===========================

If you need to serialize or deserialize a type that is not supported out of the
box (for example, `ipaddress.IPv4Address`_ or a domain-specific class),
Dataclass Wizard provides **type hooks** to define custom load and dump behavior.

Type hooks allow you to extend (de)serialization without modifying the type
itself, and work with or without inheritance.

See `Type Hooks`_ for details and examples.

.. _Type Hooks: https://dcw.ritviknag.com/en/latest/advanced_usage/type_hooks.html
.. _`ipaddress.IPv4Address`: https://docs.python.org/3/library/ipaddress.html#ipaddress.IPv4Address
