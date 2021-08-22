=======
History
=======

0.8.1 (2021-08-22)
------------------
**Bugfixes**

* Fix an import issue with the ``wiz`` CLI tool.

0.8.0 (2021-08-22)
------------------
**Features and Improvements**

* Add new ``wiz`` companion CLI utility
* Add a CLI sub-command ``gs`` to generate the dataclass schema for a JSON
  file or string input.

**Bugfixes**

* The key transform functions now correctly work when the JSON keys contain
  spaces. For example, a field named "the number 42" should now be correctly
  parsed as ``the_number_42`` when the key transformer is :func:`to_snake_case`.

0.7.0 (2021-08-19)
------------------

* Support the ``deque`` type in the JSON load and dump process,
  as well as its equivalent in the ``typing`` module.
* Add ``__slots__`` where possible to classes, to help reduce the overall memory
  footprint.
* Slightly changed the order of constructor arguments to most ``Parser`` implementations.
* Rename the ``type_check`` utils module to ``typing_compat``, as I think this name
  makes it clearer as to its purpose.
* Rename a few internal functions, such as ``BaseJSONWizardMeta._safe_as_enum``
  -> ``BaseJSONWizardMeta._as_enum_safe``
* Add benchmark tests against a few other libraries

0.6.0 (2021-08-16)
------------------

* Support ``set`` and ``frozenset`` types in the JSON load and dump process,
  as well as their equivalents in the ``typing`` module.
* Support custom JSON key mappings for dataclass fields.
* Add new exported helper functions:
    - ``json_field``: This can be thought of as an alias to ``dataclasses.field(...)``,
      but one which also represents a mapping of one or more JSON key names to a
      dataclass field.
    - ``json_key``: Represents a mapping of one or more JSON key names for a
      dataclass field.
* Add an optional attribute ``json_key_to_field`` to ``JSONSerializable.Meta``
* Rename ``ListParser`` to ``IterableParser``, since this parser will also be
  used for Set types.
* Update the ``__call__`` method of the default ``Parser`` to raise a ``ParseError``,
  so we can provide a more helpful error message when an unknown or unsupported type
  annotation is encountered.

0.5.1 (2021-08-13)
------------------
**Bugfixes**

* The ``property_wizard`` metaclass should now correctly handle cases when field
  properties are annotated as a standard mutable type (``list``, ``dict``,
  or ``set``).
* The ``property_wizard`` metaclass should now also honor the ``default_factory``
  argument to a dataclass *field* object as expected.
* Resolved an issue where in some cases the JSON load/dump process failed when
  Python 3.8+ users imported ``TypedDict`` from ``typing`` instead of the
  ``typing_extensions`` module. Now it should correctly work regardless of which
  version of ``TypedDict`` is used. This is especially important because of
  `an issue with TypedDict`_ that is present in Python 3.8.

.. _an issue with TypedDict: https://bugs.python.org/issue38834

0.5.0 (2021-08-12)
------------------
**Features and Improvements**

* ``JSONSerializable`` now supports dataclass fields with an `Annotated`_ type.
* The ``property_wizard`` metaclass has been (similarly) updated to support
  `Annotated` field properties; such types can be resolved by
  making a call to ``typing.get_type_hints`` with the argument ``include_extras=True``.
* Support for adding global JSON load/dump settings, e.g. when ``JSONSerializable.Meta`` is defined
  as an outer class.
* Add proper source attributions, and apply the LICENSE and any NOTICE (if applicable) from
  the sources.
* Update comments in code to clarify or elaborate where
  needed.
* Update Sphinx docs/

**Bugfixes**

* When ``JSONSerializable.Meta`` is defined as an inner class - which is the most common
  scenario - it should now be correctly applied per-class, rather than mutating
  the load/dump process for other dataclasses that don't define their own inner ``Meta`` class.
* When logging a message if a JSON key is missing from a dataclass schema, the dataclass
  name is now also included in the message.

.. _Annotated: https://docs.python.org/3.9/library/typing.html#typing.Annotated

0.4.1 (2021-08-09)
------------------

* Update README docs with usage of newly supported features

0.4.0 (2021-08-09)
------------------
**Features and Improvements**

* Add support for serializing the following Python types:
    - ``defaultdict`` (via the ``typing.DefaultDict`` annotation)
    - ``UUID``'s
    - The special variadic form of ``Tuple``.
      For example, ``Tuple[str, ...]``.
    - A special case where optional type arguments are passed to ``Tuple``.
      For example, ``Tuple[str, Optional[int], Union[bool, str, None]]``
* Add new ``LetterCase.LISP`` Enum member, which references the ``to_lisp_case`` helper function
* All the ``Enum``-subclass attributes in ``JSONSerializable.Meta``
  now additionally support strings as values; they will be parsed using the Enum
  ``name`` field by default, and should format helpful messages on
  any lookup errors.
* Remove the ``LoadMixin.load_with_object`` method, as that was already
  deprecated and slated to be removed.

**Bugfixes**

* Update the ``get_class_name`` helper function to handle the edge case
  when classes are defined within a function.
* Update a few ``load_to...`` methods as a ``staticmethod``

0.3.0 (2021-08-05)
------------------
* Some minor code refactoring
* Require ``typing-extensions`` library up till Python 3.9 now
  (it's main use for Python 3.8 and 3.9 is the updated ``get_origin`` and ``get_args`` helper functions)
* The default ``__str__`` method is now optional, and can be skipped via the flag ``str=False``
* Add some more test cases


0.2.4 (2021-08-04)
------------------
* Update README docs

  * Move the section on *Advanced Usage* to the main docs
  * Cleanup usage and docs in the *Field Properties* section

0.2.3 (2021-08-03)
------------------
* Add better keywords for the package

0.2.2 (2021-08-03)
------------------
* Explicitly add a dependency on ``typing-extensions`` for Python 3.6 and 3.7

0.2.1 (2021-08-03)
------------------
* Fix a bug for Python 3.6 where the build failed when using
  the `PyForwardRef` annotation.

0.2.0 (2021-08-03)
------------------

* Rename type variable ``EXPLICIT_NULL`` to ``ExplicitNull``
* Rename module ``type_defs.py`` to ``type_def.py``
* Rename module ``base_meta.py`` to ``bases_meta.py``
* ``JSONSerializable.Meta``: rename attribute ``date_time_with_dump`` to ``marshal_date_time_as``, as I believe
  this name is overall more clearer.
* Refactor the ``property_wizard`` helper function and update it to cover some edges cases.
* Add test cases to confirm intended functionality of ``property_wizard``.

0.1.0 (2021-08-02)
------------------

* First release on PyPI.
