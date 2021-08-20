Overview
========

Dataclass Wizard is a library that provides a set of simple, yet elegant
*wizarding* tools for interacting with the Python ``dataclasses`` module.

Requirements
~~~~~~~~~~~~

The dataclass-wizard library officially supports **Python 3.6+**

There are no core requirements outside of the Python standard library. That being
said, this library *does*  require a few conditional dependencies:

* `typing-extensions` - this is a lightweight and highly useful library that backports
  the most recently added features to the ``typing`` module. For more info,
  check out the :doc:`python_compatibility` section.
* `dataclasses` - a backport of the ``dataclasses`` module for Python 3.6
* `backports-datetime-fromisoformat` - a backport of `fromisoformat()`_ for Python 3.6

Benefits
~~~~~~~~

- Minimal setup required. In most cases, all you need is a dataclass that sub-classes
  from ``JSONWizard``.
- Speed. It is up to 5 times faster than libraries such as `dataclasses-json`_
  that use ``marshmellow``, and about 30 x faster than libraries such as `jsons`_
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
- Support for recently introduced type Generics such as ``Literal``.


.. _here: https://pypi.org/project/typing-extensions/
.. _fromisoformat(): https://docs.python.org/3/library/datetime.html#datetime.date.fromisoformat
.. _defaultdict: https://docs.python.org/3/library/collections.html#collections.defaultdict
.. _jsons: https://pypi.org/project/jsons/
.. _dataclasses-json: https://pypi.org/project/dataclasses-json/

Supported Types
~~~~~~~~~~~~~~~

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

* Sets
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
    - ``time``
    - ``date``

* Recently introduced Generic types (available in Python 3.6+ via the ``typing-extensions``
  module)
    - ``Annotated``
    - ``Literal``
