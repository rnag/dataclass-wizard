Overview
========

Requirements
~~~~~~~~~~~~

The ``dataclass-wizard`` library officially supports **Python 3.9+**

There are no core requirements outside of the Python standard library. That being
said, this library *does* utilize a few conditional dependencies:

* `typing-extensions` - this is a lightweight and highly useful library that backports
  the most recently added features to the ``typing`` module. For more info,
  check out the :doc:`python_compatibility` section.

Advantages
~~~~~~~~~~

- Minimal setup required. In most cases, all you need is a dataclass that sub-classes
  from ``JSONWizard``.
- Speed. It is up to 25 times faster than libraries such as `dataclasses-json`_
  that use ``marshmallow``, and about 60 x faster than libraries such as `jsons`_
  which don't seem to handle dataclasses as well as you'd expect.
- Adds the ability to use field properties (with default values) in dataclasses.
- Automatic key transform to/from JSON (ex. *camel* to *snake*).
  :doc:`Custom key mappings <common_use_cases/custom_key_mappings>` also supported.
- Automatic type conversion when loading from JSON or a ``dict`` object.
  For instance, strings are converted to boolean if a type annotation is ``List[bool]``.
- Built-in support for standard Python collections, as well as most Generics from the
  ``typing`` module. Other commonly used types such as Enums, `defaultdict`_, and *date*
  and *time* objects such as :class:`datetime` are also natively supported.
- Latest Python features such as
  `parameterized standard collections <python_compatibility.html#the-latest-and-greatest>`__
  can be used.
- Ability to construct *ad-hoc* dataclass schemas using JSON input (either as a
  file or string) using the included `wiz-cli`_ utility.


.. _here: https://pypi.org/project/typing-extensions/
.. _fromisoformat(): https://docs.python.org/3/library/datetime.html#datetime.date.fromisoformat
.. _defaultdict: https://docs.python.org/3/library/collections.html#collections.defaultdict
.. _jsons: https://pypi.org/project/jsons/
.. _`wiz-cli`: https://dcw.ritviknag.com/en/latest/wiz_cli.html
.. _dataclasses-json: https://pypi.org/project/dataclasses-json/

Supported Types
~~~~~~~~~~~~~~~

.. tip::
   See the section on `Special Cases`_ for additional information on how Dataclass Wizard handles JSON
   load/dump for special Python types.

Dataclass Wizard supports a wide range of Python types, making it easier to work with complex data structures.
This includes built-in types, collections, and more advanced type annotations.
The following types are supported:

- **Basic Types**:

  - ``str``
  - ``int``
  - ``float``
  - ``bool``
  - ``None`` (`docs <https://docs.python.org/3/library/constants.html#None>`_)

- **Binary Types**:

  - ``bytes`` (`docs <https://docs.python.org/3/library/stdtypes.html#bytes>`_)
  - ``bytearray`` (`docs <https://docs.python.org/3/library/stdtypes.html#bytearray>`_)

- **Decimal Type**:

  - ``Decimal`` (`docs <https://docs.python.org/3/library/decimal.html#decimal.Decimal>`_)

- **Pathlib**:

  - ``Path`` (`docs <https://docs.python.org/3/library/pathlib.html>`_)

- **Typed Collections**:
  Typed collections are supported for structured data, including:

  - ``TypedDict`` (`docs <https://docs.python.org/3/library/typing.html#typing.TypedDict>`_)
  - ``NamedTuple`` (`docs <https://docs.python.org/3/library/typing.html#typing.NamedTuple>`_)
  - ``namedtuple`` (`docs <https://docs.python.org/3/library/collections.html#collections.namedtuple>`_)

- **ABC Containers** (`docs <https://docs.python.org/3/library/typing.html#aliases-to-container-abcs-in-collections-abc>`_):

  - ``Sequence`` (`docs <https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence>`_) -- instantiated as ``tuple``
  - ``MutableSequence`` (`docs <https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableSequence>`_) -- mapped to ``list``
  - ``Collection`` (`docs <https://docs.python.org/3/library/collections.abc.html#collections.abc.Collection>`_) -- instantiated as ``list``

- **Type Annotations and Qualifiers**:

  - ``Required``, ``NotRequired``, ``ReadOnly`` (`docs <https://docs.python.org/3/library/typing.html#typing.Required>`_)
  - ``Annotated`` (`docs <https://docs.python.org/3/library/typing.html#typing.Annotated>`_)
  - ``Literal`` (`docs <https://docs.python.org/3/library/typing.html#typing.Literal>`_)
  - ``LiteralString`` (`docs <https://docs.python.org/3/library/typing.html#typing.LiteralString>`_)
  - ``Union`` (`docs <https://docs.python.org/3/library/typing.html#typing.Union>`_) -- Also supports `using dataclasses`_.
  - ``Optional`` (`docs <https://docs.python.org/3/library/typing.html#typing.Optional>`_)
  - ``Any`` (`docs <https://docs.python.org/3/library/typing.html#typing.Any>`_)

- **Enum Types**:

  - ``Enum`` (`docs <https://docs.python.org/3/library/enum.html#enum.Enum>`_)
  - ``StrEnum`` (`docs <https://docs.python.org/3/library/enum.html#enum.StrEnum>`_)
  - ``IntEnum`` (`docs <https://docs.python.org/3/library/enum.html#enum.IntEnum>`_)

- **Sets**:

  - ``set`` (`docs <https://docs.python.org/3/library/stdtypes.html#set>`_)
  - ``frozenset`` (`docs <https://docs.python.org/3/library/stdtypes.html#frozenset>`_)

- **Mappings**:

  - ``dict`` (`docs <https://docs.python.org/3/library/stdtypes.html#dict>`_)
  - ``defaultdict`` (`docs <https://docs.python.org/3/library/collections.html#collections.defaultdict>`_)
  - ``OrderedDict`` (`docs <https://docs.python.org/3/library/collections.html#collections.OrderedDict>`_)

- **Sequences**:

  - ``list`` (`docs <https://docs.python.org/3/library/stdtypes.html#list>`_)
  - ``deque`` (`docs <https://docs.python.org/3/library/collections.html#collections.deque>`_)
  - ``tuple`` (`docs <https://docs.python.org/3/library/stdtypes.html#tuple>`_)

- **UUID**:

  - ``UUID`` (`docs <https://docs.python.org/3/library/uuid.html#uuid.UUID>`_)

- **Date and Time**:

  - ``datetime`` (`docs <https://docs.python.org/3/library/datetime.html#datetime.datetime>`_)
  - ``date`` (`docs <https://docs.python.org/3/library/datetime.html#datetime.date>`_)
  - ``time`` (`docs <https://docs.python.org/3/library/datetime.html#datetime.time>`_)
  - ``timedelta`` (`docs <https://docs.python.org/3/library/datetime.html#datetime.timedelta>`_)

- **Nested Dataclasses**: Nested dataclasses are supported, allowing you to serialize and deserialize
  nested data structures.

Starting with **v0.34.0**, recursive and self-referential dataclasses are supported out of the box
when the ``v1`` option is enabled in the ``Meta`` setting (i.e., ``v1 = True``). This removes the
need for custom settings like ``recursive_classes`` and expands type support beyond what is
available in ``v0.x``.

For more advanced functionality and additional types, enabling ``v1`` is recommended. It forms
the basis for more complex cases and will evolve into the standard model for Dataclass Wizard.

For more info, see the `Field Guide to V1 Opt-in <https://github.com/rnag/dataclass-wizard/wiki/Field-Guide-to-V1-Opt%E2%80%90in>`_.

Special Cases
-------------

.. note::
   With most annotated Python types, it is clear and unambiguous how they are to
   be loaded from JSON, or dumped when they are serialized back to JSON.

   However, here a few special cases that are worth going over.

* ``str`` - Effortlessly converts inputs to strings. If already a string,
  it remains unchanged. Non-strings are converted to their string
  representation, and ``None`` becomes an empty string.

      *Examples*: ``123`` → ``'123'``, ``None`` → ``''``

* ``bool`` - JSON values that appear as strings or integers will be de-serialized
  to a ``bool`` using a case-insensitive search that matches against the following
  "truthy" values:
      *TRUE, T, YES, Y, ON, 1*

* ``int`` - Converts valid inputs to integers:

  - String representations of integers (e.g., ``"123"``).
  - Floats or float strings with or without fractional parts (e.g., ``123.4`` or ``"123.4"``), rounded to the nearest integer.
  - Empty strings or ``None`` return the default value of ``0``.

  .. warning::
     Starting in v1.0, floats or float strings with fractional parts (e.g., ``123.4`` or
     ``"123.4"``) will raise an error instead of being rounded.

* ``Enum`` - JSON values (ideally strings) are de-serialized to ``Enum``
  subclasses via the ``value`` attribute, and are serialized back to JSON
  using the same ``value`` attribute.

* ``UUID`` types are de-serialized from JSON strings using the constructor
  method -- i.e. ``UUID(string)``, and by default are serialized back to JSON
  using the ``hex`` attribute -- i.e. :attr:`my_uuid.hex`.

* ``Decimal`` types are de-serialized using the ``Decimal(str(o))`` syntax --
  or via an annotated subclass of *Decimal* -- and are serialized via the
  builtin :func:`str` function.

* ``NamedTuple`` sub-types are de-serialized from a ``list``, ``tuple``, or any
  iterable type into the annotated sub-type. They are serialized back as the
  the annotated ``NamedTuple`` sub-type; this is mainly because *named tuples*
  are essentially just tuples, so they are inherently JSON serializable
  to begin with.

* For ``date``, ``time``, and ``datetime`` types, string values are de-serialized
  using the builtin :meth:`fromisoformat` method; for ``datetime`` and ``time`` types,
  a suffix of "Z" appearing in the string is first replaced with "+00:00",
  which represents UTC time. JSON values for ``datetime`` and ``date`` annotated
  types appearing as numbers will be de-serialized using the
  builtin :meth:`fromtimestamp` method.

  All these types are serialized back to JSON using the builtin :meth:`isoformat` method.
  For ``datetime`` and ``time`` types, there is one noteworthy addition: the
  suffix "+00:00" is replaced with "Z", which is a common abbreviation for UTC time.

* For ``timedelta`` types, the values to de-serialize can either be strings or numbers,
  so we check the type explicitly. If the value is a string, we first ensure it's in
  a numeric form like '1.23', and if so convert it to a *float* value in seconds;
  otherwise, we convert values like '01:45' or '3hr12m56s' via the `pytimeparse`_
  module, which is also available as an extra via ``pip install dataclass-wizard[timedelta]``.
  Lastly, any numeric values are assumed to be in seconds and are used as is.

  All :class:`timedelta` values are serialized back to JSON using the builtin :meth:`str` method,
  so for example ``timedelta(seconds=3)`` will be serialized as "0:00:03".

* ``set``, ``frozenset``, and ``deque`` types will be de-serialized using their
  annotated base types, and serialized as ``list``'s.

* Commonly used ``dict`` sub-types (such as ``defaultdict``) will be de-serialized
  from JSON objects using the annotated base type, and serialized back as
  plain ``dict`` objects.

.. _using dataclasses: https://dcw.ritviknag.com/en/latest/common_use_cases/dataclasses_in_union_types.html
.. _pytimeparse: https://pypi.org/project/pytimeparse/
