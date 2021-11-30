Overview
========

Requirements
~~~~~~~~~~~~

The ``dataclass-wizard`` library officially supports **Python 3.6+**

There are no core requirements outside of the Python standard library. That being
said, this library *does* utilize a few conditional dependencies:

* `typing-extensions` - this is a lightweight and highly useful library that backports
  the most recently added features to the ``typing`` module. For more info,
  check out the :doc:`python_compatibility` section.
* `dataclasses` - a backport of the ``dataclasses`` module for Python 3.6
* `backports-datetime-fromisoformat` - a backport of `fromisoformat()`_ for Python 3.6

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
.. _`wiz-cli`: https://dataclass-wizard.readthedocs.io/en/latest/wiz_cli.html
.. _dataclasses-json: https://pypi.org/project/dataclasses-json/

Supported Types
~~~~~~~~~~~~~~~

.. tip::
   See the below section on `Special Cases`_ for additional info
   on the JSON load/dump process for special Python types.

* Strings
    - ``str``
    - ``bytes``
    - ``bytearray``

* Numerics
    - ``int``
    - ``float``
    - ``Decimal``

* Booleans (``bool``)

* Sequences (and their equivalents in the ``typing`` module)
    - ``list``
    - ``deque``
    - ``tuple``
    - ``NamedTuple``

* Sets (and their equivalents in the ``typing`` module)
    - ``set``
    - ``frozenset``

* Mappings (and their equivalents in the ``typing`` module)
    - ``dict``
    - ``defaultdict``
    - ``TypedDict``
    - ``OrderedDict``

* ``Enum`` subclasses

* ``UUID``

* *date* and *time* objects
    - ``datetime``
    - ``date``
    - ``time``
    - ``timedelta``

* Special `typing primitives`_ from the ``typing`` module
    - ``Any``
    - ``Union`` - Also supports `using dataclasses`_.
    - ``Optional``

* Recently introduced Generic types (available in Python 3.6+ via the ``typing-extensions``
  module)
    - ``Annotated``
    - ``Literal``


.. _typing primitives: https://docs.python.org/3/library/typing.html#special-typing-primitives

Special Cases
-------------

.. note::
   With most annotated Python types, it is clear and unambiguous how they are to
   be loaded from JSON, or dumped when they are serialized back to JSON.

   However, here a few special cases that are worth going over.

* ``bool`` - JSON values that appear as strings or integers will be de-serialized
  to a ``bool`` using a case-insensitive search that matches against the following
  "truthy" values:
      *TRUE, T, YES, Y, 1*

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

.. _using dataclasses: https://dataclass-wizard.readthedocs.io/en/latest/common_use_cases/dataclasses_in_union_types.html
.. _pytimeparse: https://pypi.org/project/pytimeparse/
