=======
History
=======

0.14.0 (2021-09-25)
-------------------
**Features and Improvements**

* Add the ability to handle de-serialization and serialization of dataclasses
  within ``Union`` types. A new attribute ``tag`` in the inner ``Meta`` class
  determines the tag name to map to a dataclass, when the dataclass is part
  of any ``Union`` types.

* The dump (serialization) process has been reworked to function more like the
  load process. That is, it will properly use the :class:`Meta` config for a
  dataclass, as well as any custom load hooks for nested dataclasses. Performance
  or functionality should not otherwise be affected.

0.13.1 (2021-09-24)
-------------------

**Bugfixes**

* Ensure that :func:`setup_dump_config_for_cls_if_needed` is called for nested
  dataclasses, so that custom key mappings for example can be properly applied.

0.13.0 (2021-09-08)
-------------------
**Features and Improvements**

* Add new error class :class:`MissingData`, which is raised when a dataclass field
  annotated as a *data class* type has a ``null`` JSON value in the load process.

* Update the :func:`as_int` helper function so that ``float`` values as well as ones encoded
  as strings are correctly converted to annotated ``int`` types, i.e. using the
  ``int(round(float))`` syntax.

* Add :class:`Encoder` and :class:`Decoder` model classes, and properly implement them
  in the :class:`JSONWizard` helper methods.

* Decorate the :class:`JSONWizard` helper methods :meth:`from_list`, :meth:`from_dict`,
  and :meth:`to_dict` with the ``_alias`` decorator.

**Bugfixes**

* ``property_wizard``: Remove the internal usage of :func:`get_type_hints_with_extras`
  for resolving class annotations. This is because ``typing.get_type_hints`` will raise
  an error if a class has forward references in any type annotations. Since the usage
  is as a metaclass, forward refs can *never* be resolved. So we will instead access
  the class ``__annotations`` directly, and for now will ignore any forward references
  which are declared.

* Ensure :func:`fromlist` is actually exported at the top level (looks like that
  was not the case)

0.12.0 (2021-09-06)
-------------------

* Change the order of arguments for :func:`fromdict` and :func:`fromlist`
  functions, since it's more intuitive to pass the name of the data class
  as the first argument.

* Add :func:`fromlist`, :func:`fromdict`, and :func:`asdict` to the public API,
  and ensure that we export these helper functions.

* Add new helper functions :func:`LoadMeta` and :func:`DumpMeta` to specify
  the meta config for a dataclass, which can be used with the new functions
  like ``fromdict`` above.

* *Custom key mappings*: support a use case where we want to specify a new
  mapping via the ``__remapping__`` key in the ``metadata`` argument to
  :func:`dataclasses.field`.

0.11.0 (2021-09-04)
-------------------

* Add the ability to handle unknown or extraneous JSON keys in the *load* (de-serialization)
  process. A new attribute ``raise_on_unknown_json_key`` to the ``Meta`` class
  determines if we should raise an error in such cases.

* Move attribute definition for the ``JSONWizard.Meta`` class into a new
  :class:`BaseMeta` definition, so that the model can be re-used in
  `loaders` and `dumpers` module for example.

* Ensure all errors raised by this library extend from a new base error class,
  :class:`JSONWizardError`.

* Add new error classes

  * :class:`MissingFields` - raised when JSON object is missing a required
    dataclass field.
  * :class:`UnknownJSONKey` - raised when an unknown or extraneous JSON key is
    encountered in the JSON load process.

* Split up the load (de-serialization) process for *named tuples* into two
  helper load hooks. The new hook :meth:`load_to_named_tuple_untyped` is used
  for the ``collections.namedtuple`` variant.

* Minor performance improvements so the JSON load process is slightly faster.


0.10.2 (2021-08-29)
-------------------

* Rename some internal functions, such as the ``default_func`` decorator (renamed
  to ``_alias``). I felt that this name was overall more clearer.
* Similarly rename ``PassThroughParser`` to ``SingleArgParser``, as that's a bit
  more clear which types it handles.
* ``wiz`` CLI: comment out the *--verbose* and *--quiet* flags, as those were
  unused anyway.
* Update docs/

0.10.0 (2021-08-28)
-------------------

* Minor performance improvements so the JSON load process is slightly faster.
* ``wiz gs``: The result now includes the :class:`JSONWizard` import and the
  expected usage by default.
* Update type annotations slightly for the ``LoadMixin.load_to...`` methods.
* Add support for sub-classes of common Python types, such as subclasses of
  ``str`` and ``int``, as part of the JSON load process.
* Remove ``ForwardRefParser`` - we don't need it anyway as it's a simple
  resolution, and the usage of a ``Parser`` object incurs a bit of an
  unnecessary overhead.

0.9.0 (2021-08-23)
------------------
**Features and Improvements**

* Minor performance improvements so the JSON load process is slightly faster.
* Replace ``CaseInsensitiveDict`` with a custom ``DictWithLowerStore`` implementation.
* ``wiz`` CLI: Add a ``--version`` option to check the installed version.
* Remove :func:`get_class_name` usage wherever possible.

**Bugfixes**

* Fixes for the JSON to dataclass generation tool
    - Ensure that nested lists with dictionaries are correctly merged, and add a test
      case to confirm intended behavior.
    - Change to only singularize model names if nested within a list.

0.8.2 (2021-08-22)
------------------
**Bugfixes**

* ``wiz gs``: Empty lists should appear as ``List`` instead of ``Dict``

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
