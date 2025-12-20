Type Hooks
==========

.. note::
   If you want to customize serialization for **specific fields** (rather than
   a type everywhere it appears), see :doc:`serializer_hooks`.

Type hooks let you extend Dataclass Wizard to support **custom or unsupported
types**, by defining how a type is:

- **loaded** (parsed) from JSON/dicts into a Python object, and
- **dumped** (serialized) back into JSON-compatible data.

This is the recommended way to add support for types such as
``ipaddress.IPv4Address``, ``pathlib.Path``, custom IDs, and other domain types.

When to use type hooks
----------------------

Use type hooks when:

- a type is not supported out of the box and you want a clean, reusable solution
- you want consistent behavior for a type across many dataclasses
- you want to avoid sprinkling per-field logic throughout your models

If you only need special handling for a single field (or a small subset of
fields), prefer :doc:`serializer_hooks`.

Quick start: register a type
----------------------------

The simplest approach is to register a type and rely on sensible defaults:

- **load**: ``Type(value)``
- **dump**: ``str(value)``

Example: `ipaddress.IPv4Address`_

.. code-block:: python3

    from __future__ import annotations  # Remove if Python 3.10+

    from ipaddress import IPv4Address

    from dataclass_wizard import DataclassWizard


    class Foo(DataclassWizard):
        # DataclassWizard auto-applies @dataclass to subclasses
        c: IPv4Address | None = None


    Foo.register_type(IPv4Address)

    foo = Foo.from_dict({"c": "127.0.0.1"})
    assert foo.c == IPv4Address("127.0.0.1")
    assert foo.to_dict() == {"c": "127.0.0.1"}

If you omit the registration, you will get an error indicating the type is not
supported (and it should indicate whether the failure occurred during **load**
or **dump**).

No Inheritance Needed
--------------------

Type hooks also work without subclassing ``DataclassWizard`` or ``JSONWizard``.
This is useful when you prefer plain dataclasses and use the functional
API (``fromdict``/``asdict``).

.. code-block:: python3

    from __future__ import annotations  # Remove if Python 3.10+

    from dataclasses import dataclass
    from ipaddress import IPv4Address

    from dataclass_wizard import LoadMeta, asdict, fromdict, register_type


    @dataclass
    class Foo:
        b: bytes = b""
        s: str | None = None
        c: IPv4Address | None = None


    LoadMeta(v1=True).bind_to(Foo)

    # Register IPv4Address with default hooks (load=IPv4Address, dump=str)
    register_type(Foo, IPv4Address)

    data = {"b": "AAAA", "c": "127.0.0.1", "s": "foobar"}

    foo = fromdict(Foo, data)
    assert asdict(foo) == data
    assert asdict(fromdict(Foo, asdict(foo))) == data

Registering custom load and dump functions
------------------------------------------

You can override the defaults by providing custom functions. In general:

- The **load** function should return the target type (or object).
- The **dump** function must return a JSON-serializable value
  (``str``, ``int``, ``float``, ``bool``, ``None``, ``list``, ``dict``).

.. code-block:: python3

    from decimal import Decimal, ROUND_HALF_UP

    from dataclass_wizard import DataclassWizard


    def load_decimal(v):
        # Normalize all decimals to 2 decimal places on load
        return Decimal(v).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


    def dump_decimal(v: Decimal):
        # Serialize as string to preserve precision
        return str(v)


    class Invoice(DataclassWizard):
        total: Decimal


    # Override the built-in Decimal behavior
    Invoice.register_type(Decimal, load=load_decimal, dump=dump_decimal)

    invoice = Invoice.from_dict({'total': '1.235'})
    print(invoice)              # Invoice(total=Decimal('1.24'))
    print(invoice.to_dict())    # {'total': '1.24'}

V1 code generation hooks (advanced)
-----------------------------------

If you have v1 enabled, you may choose to provide **v1 codegen hooks**.
These hooks accept ``(TypeInfo, Extras)`` and return a **string expression**
(or ``TypeInfo``) used by the v1 compiler.

This is useful if you need to integrate directly with the v1 compilation
pipeline.

.. note::
   Most users should start with ``register_type()`` and only use codegen hooks
   when needed.

Example: ``IPv4Address`` with v1 codegen hooks

.. code-block:: python3

   from dataclasses import dataclass
   from ipaddress import IPv4Address

   from dataclass_wizard import JSONWizard
   from dataclass_wizard.v1.models import TypeInfo, Extras


   def load_to_ipv4_address(tp: TypeInfo, extras: Extras) -> str:
       # Wrap the value expression using the type's constructor
       return tp.wrap(tp.v(), extras)

   def dump_from_ipv4_address(tp: TypeInfo, extras: Extras) -> str:
       # Dump an IPv4Address by converting to string
       return f"str({tp.v()})"


   @dataclass
   class Foo(JSONWizard):
       class Meta(JSONWizard.Meta):
           v1 = True
           v1_type_to_load_hook = {IPv4Address: load_to_ipv4_address}
           v1_type_to_dump_hook = {IPv4Address: dump_from_ipv4_address}

       c: IPv4Address | None = None


   foo = Foo.from_dict({"c": "127.0.0.1"})
   assert foo.to_dict() == {"c": "127.0.0.1"}

Declaring hooks via Meta
------------------------

If you prefer a declarative style, you can set hooks in ``Meta``. This is
especially useful for v1.

.. code-block:: python3

    from ipaddress import IPv4Address

    from dataclass_wizard import DataclassWizard


    # DataclassWizard sets `v1=True` and auto-applies @dataclass to subclasses
    class Foo(DataclassWizard):
        c: IPv4Address | None = None


    Foo.register_type(IPv4Address)

If you want to avoid method calls entirely, you can also register via ``Meta``.
(Exact configuration options may vary depending on the engine you use.)

.. code-block:: python3

    from __future__ import annotations  # Remove if Python 3.10+

    from dataclasses import dataclass
    from ipaddress import IPv4Address

    from dataclass_wizard import JSONWizard


    @dataclass
    class Foo(JSONWizard):
        class Meta(JSONWizard.Meta):
            v1 = True
            # Equivalent of Foo.register_type(IPv4Address)
            # Defaults: load=IPv4Address, dump=str
            v1_type_to_load_hook = {IPv4Address: IPv4Address}
            v1_type_to_dump_hook = {IPv4Address: str}

        c: IPv4Address | None = None

    assert Foo.from_dict({'c': '1.2.3.4'}).c == IPv4Address('1.2.3.4')  # True

Enum example: load by name, dump by value
-----------------------------------------

The default behavior for enums is typically to load/dump using ``value``.
If you want to load by enum **name** instead, type hooks make it easy.

.. code-block:: python3

    from enum import Enum

    from dataclass_wizard import DataclassWizard


    class MyEnum(Enum):
        NAME_1 = 'one'
        NAME_2 = 'two'


    def load_enum_by_name(v):
        # Input example: 'NAME 1' -> MyEnum.NAME_1
        return MyEnum[v.replace(' ', '_')]


    def dump_enum_by_name(e: MyEnum):
        return e.name.replace('_', ' ')


    class MyClass(DataclassWizard):
        my_str: str
        my_enum: MyEnum


    MyClass.register_type(MyEnum, load=load_enum_by_name, dump=dump_enum_by_name)

    data = {'my_str': 'my string', 'my_enum': 'NAME 1'}

    c = MyClass.from_dict(data)
    assert c.my_enum is MyEnum.NAME_1
    assert c.to_dict() == data

Runtime vs v1 codegen hooks
---------------------------

Dataclass Wizard supports two styles of hooks:

Runtime hooks
   Regular Python callables used at runtime.

   - load hook: ``fn(value) -> object``
   - dump hook: ``fn(object) -> json_value``

V1 codegen hooks
   Functions used by the v1 compiler.

   - hook: ``fn(TypeInfo, Extras) -> str | TypeInfo``

If you provide a codegen hook, it must return a valid Python expression as a
string, referencing any required types/functions that are in scope for the
generated code.

Errors and troubleshooting
--------------------------

Unsupported type errors
   If a type is unsupported, Dataclass Wizard will raise a parse/serialization
   error. The error should indicate:

   - the field name
   - whether the error occurred during **load** or **dump**
   - the unsupported type
   - a resolution hint (register a type hook)

If your dump hook returns a non-JSON value
   Ensure your dump hook returns JSON-compatible primitives (or nested
   structures composed of primitives).

If you see name errors in v1 generated code
   Your codegen hook must reference names that are in scope for the generated
   function. Prefer builtins (like ``str``) or ensure the type/function is
   available to the compiler (via locals injection, if applicable).

See also
--------

- :doc:`serializer_hooks` (field-level customization)
- :doc:`../overview` (supported types and general usage)

.. _`ipaddress.IPv4Address`: https://docs.python.org/3/library/ipaddress.html#ipaddress.IPv4Address
