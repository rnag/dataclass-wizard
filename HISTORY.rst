=======
History
=======

0.26.0 (2024-11-05)
-------------------

* This will be the latest (minor) release with support for Python 3.6, 3.7, and 3.8 --
  all of which have reached *end-of-life*!

**Features and Improvements**

* Add compatability and support for **Python 3.13**. Thanks to :user:`benjjs` in :pr:`129`!

**Bugfixes**

* Fix: :meth:`LiteralParser.__contains__` method compares value of item with `Literal`_ arguments.
  Contributed by :user:`mikeweltevrede` in :pr:`111`.

.. _Literal: https://docs.python.org/3/library/typing.html#typing.Literal

0.25.0 (2024-11-03)
-------------------

**Features and Improvements**

* Add support for `pathlib.Path`_. Thanks to :user:`assafge` in :pr:`79`.

.. _pathlib.Path: https://docs.python.org/3/library/pathlib.html#basic-use

0.24.1 (2024-11-03)
-------------------

* Resolve ``mypy`` typing issues. Thanks to :user:`AdiNar` in :pr:`64`.

0.24.0 (2024-11-03)
-------------------

**Features and Improvements**

* :pr:`125`: add support for ``typing.Required``, ``NotRequired``

**Bugfixes**

* Fixed by :pr:`125`: Annotating ``TypedDict`` field with one of ``Required`` or ``NotRequired`` wrappers introduced in Python 3.11, no longer raises a ``TypeError``
  -- credits to :user:`claui`.

0.23.0 (2024-09-18)
-------------------

* :pr:`94`: Allows the ability to define keys in JSON/dataclass
  that do not undergo transformation -- credits to :user:`cquick01`.

  * ``LetterCase.NONE`` - Performs no conversion on strings.

    * ex: `MY_FIELD_NAME` -> `MY_FIELD_NAME`

0.22.3 (2024-01-29)
-------------------

**Features and Improvements**

* Add full support for Python 3.11 and 3.12 (Credits to :user:`alexanderilyin` on :pr:`101`)
* Project-specific development changes
    * Update CI to run tests on PY 3.11 and 3.12
    * Update ``wheel`` version
    * Update ``setup.py`` to add a ``dev`` extra which installs dev-related dependencies
    * Move test dependencies into ``requirements-test.txt``
    * Add ``sphinx_issues`` dependency to easily add link in docs to an user/issue/PR on GitHub
    * Update ``project_urls`` on PyPI to add extra links, such as "Changelog" and "Issue Tracker"


**Bugfixes**

* Fix: Loading a Variadic Tuple fails for length 0 (Credits to :user:`intentionally-left-nil` on :pr:`105`)
* Stop-gap fix for time-string patterns that contain ``-`` or ``+``,
  as Python 3.11+ can interpret this as timezone data.

0.22.2 (2022-10-11)
-------------------

**Features and Improvements**

* Minor performance improvement when dumping custom sub-types
  or unhandled types, such that we cache the dump hook
  for the type so that subsequent lookups are faster overall.

0.22.1 (2022-05-11)
-------------------

**Features and Improvements**

* Update :class:`MissingFields` to provide a more user-friendly error message,
  in cases where a missing dataclass field is not snake-cased, but could - with
  the right *key transform* - map to a key in the JSON object. For example, a JSON key of ``myField`` and a field
  named ``MyField``.

**Bugfixes**

* Fixed a bug in the load (or de-serialization) process with ``from_dict``, where a :class:`MissingFields` was raised
  in cases where a dataclass field is not snake-cased, but is otherwise identical to a key in the JSON object.
  For example, a JSON key and field |both named viewMode|_. The JSON data in such cases should now be correctly
  de-serialized to a dataclass instance as expected.

.. _both named viewMode: https://github.com/rnag/dataclass-wizard/issues/54
.. |both named viewMode| replace:: both named ``viewMode``

0.22.0 (2022-02-02)
-------------------

**Features and Improvements**

* Ensure that the :attr:`debug_enabled` flag now applies recursively to all
  nested dataclasses, which is more helpful for debugging purposes.

* Add new attribute :attr:`json_object` -- which contains the original JSON
  object -- to :class:`ParseError` objects, and include it in the object representation.

**Bugfixes**

* Fixed an issue with the :attr:`debug_enabled` flag enabled, where some load
  hooks were not properly decorated when *debug* mode was enabled; errors were not
  properly formatted in these cases. To elaborate, this only affected load hooks
  decorated with a ``@_single_arg_alias``. In particular, this affected the
  load hooks for a few annotated types, such as ``float`` and ``enum``.

0.21.0 (2022-01-23)
-------------------

**Features and Improvements**

* Adds few extra Wizard Mixin classes that might prove incredibly convenient to use.

    - :class:`JSONListWizard` - Extends :class:`JSONWizard` to return *Container* -- instead of *list* -- objects where possible.
    - :class:`JSONFileWizard` - Makes it easier to convert dataclass instances from/to JSON files on a local drive.
    - :class:`YAMLWizard` - Provides support to convert dataclass instances to/from YAML, using the default PyYAML parser.

* Add a new :class:`Container` model class, a *list* sub-type which acts as a convenience wrapper around a collection of dataclass instances.

* The ``dataclass-wizard`` library now supports parsing of YAML data. It adds the `PyYAML`_ as an optional dependency, which is loaded when it's used for the initial time. This extra dependency can be installed via::

      $ pip install dataclass-wizard[yaml]

.. _PyYAML: https://pypi.org/project/PyYAML/

0.20.3 (2021-11-30)
-------------------

* Update the parsing logic in :func:`as_timedelta` for :class:`timedelta` annotated types
  so we now explicitly check the types. If the value is numeric, or if it's a string in a numeric value
  like "1.2", we can parse it directly and so avoid calling the :mod:`pytimeparse` module.

0.20.1 - 0.20.2 (2021-11-27)
----------------------------

* Update and refactor docs, doc layout, and the readme.
* Move benchmark tests to the ``benchmarks/`` directory.

0.20.0 (2021-11-23)
-------------------

* Support custom patterns for dates and times, which are parsed (de-serialized) using :meth:`datetime.strptime`.
  This allows two approaches to be used, which have complete support in Python 3.7+ currently:

    - Using the ``DatePattern``, ``TimePattern``, and ``DateTimePattern`` type annotations,
      representing patterned `date`, `time`, and `datetime` objects respectively.

    - Use ``Annotated`` to annotate the field as ``list[time]`` for example, and pass
      in :func:`Pattern` as an extra.

0.19.0 (2021-11-17)
-------------------

**Features and Improvements**

* Add the option to customize the name of the *tag* key that will be used to
  (de)serialize fields that contain dataclasses within ``Union`` types. A new
  attribute :attr:`tag_key` in the ``Meta`` config determines the key in the
  JSON object that will be used for this purpose, which defaults to ``__tag__`` if not specified.

* Add the ability to *auto-generate* tags for a class - using the name of
  the class - if a value for :attr:`tag` is not specified in the ``Meta`` config
  for a dataclass that appears within a ``Union`` declaration. A new flag
  :attr:`auto_assign_tags` in the ``Meta`` config can be enabled to allow
  auto-assigning the class name as a tag.

0.18.0 (2021-11-14)
-------------------

**Breaking Changes**

* The :func:`LoadMeta` and :func:`DumpMeta` helper functions no longer accept
  a class type as the first argument; the correct usage now is to invoke the
  :meth:`bind_to` method on the ``Meta`` config returned. That is, given a
  dataclass :class:`A`, replace the following syntax::

      LoadMeta(A, **kwargs)

  with a more explicit binding::

      LoadMeta(**kwargs).bind_to(A)

* The :func:`asdict` helper function no longer accepts a ``Meta`` config
  as an argument. This is to encourage the usage of :func:`LoadMeta` and
  :func:`DumpMeta`, as mentioned above. The main impetus for this change is
  performance, since the ``Meta`` config for a class only needs to be set up
  once using this approach.

* Updated the project status from *Beta* to *Production/Stable*, to signify
  that any further breaking changes will result in bumping the major version.

**Features and Improvements**

* Add the :meth:`bind_to` method to the base Meta class,
  :class:`BaseJSONWizardMeta`.

* Meta config specified for a main dataclass (i.e. the class passed in to
  ``from_dict`` and ``to_dict``) now applies recursively to any nested
  dataclasses by default. The Meta config from the main class will be
  merged with the Meta config for each nested class. Note that this behavior
  can be disabled however, with the :attr:`recursive` parameter passed in
  to the ``Meta`` config.

* Rename :class:`BaseMeta` to :class:`AbstractMeta`, as the name should be
  overall more clearer, since it's actually an abstract class.

0.17.1 (2021-11-04)
-------------------

* ``property_wizard``: Update the metaclass to support `new-style annotations`_,
  also via a ``__future__`` import declared at a the top of a module; this allows
  `PEP 585`_ and `PEP 604`_ style annotations to be used in Python 3.7 and higher.

0.17.0 (2021-10-28)
-------------------

* Support `new-style annotations`_ in Python 3.7+, via a ``__future__`` import
  declared at a the top of a module; this allows `PEP 585`_ and `PEP 604`_ style
  annotations to be used in Python 3.7 and higher.

* ``wiz`` CLI: Add the *-x / --experimental* flag, which instead uses
  new-style annotations in the generated Python code.

* Update the docs and readme with examples and usage of *future
  annotations* in Python 3.7+.

.. _new-style annotations: https://dataclass-wizard.readthedocs.io/en/latest/python_compatibility.html#python-3-7
.. _PEP 585: https://www.python.org/dev/peps/pep-0585/
.. _PEP 604: https://www.python.org/dev/peps/pep-0604/

0.16.2 (2021-10-26)
-------------------

* Minor code refactor and cleanup to support ``ForwardRef`` in Python 3.6 a little better.

0.16.1 (2021-10-21)
-------------------

* Add full support for Python 3.10

0.16.0 (2021-10-20)
-------------------

* Add support for serializing ``datetime.timedelta``

  * Requires an extra for de-serialization,
    can be installed via ``pip install dataclass-wizard[timedelta]``.

0.15.2 (2021-10-03)
-------------------

**Features and Improvements**

* Add new internal helper function :func:`eval_forward_ref_if_needed`

**Bugfixes**

* Support forward references in type arguments to ``Union``, as well as when
  iterating over the list of :func:`dataclasses.fields` for each data class.


0.15.1 (2021-09-30)
-------------------

* Add a new method :meth:`list_to_json` to the :class:`JSONWizard` Mixin class, which can be
  used to convert a list of dataclass instances to a JSON string representation.

* Minor code refactoring to introduce small typing-related changes.

* Update docs.

0.15.0 (2021-09-30)
-------------------

* Add the ability to skip fields with default values in the serialization
  process. A new attribute ``skip_defaults`` in the inner ``Meta`` class
  determines whether to skip / omit fields with default values, based on the
  ``default`` or ``default_factory`` argument to :func:`dataclasses.field`.

* Add the ability to omit fields in the serialization process.

  * A new argument ``dump`` added to the :func:`json_key` and :func:`json_field`
    helper functions determines whether to exclude the field in the JSON or
    dictionary result.
  * The :func:`asdict` helper function has similarly been updated to accept a
    ``exclude`` argument, containing a list of one or more dataclass field
    names to exclude from the serialization process.

0.14.2 (2021-09-28)
-------------------

**Bugfixes**

* Dataclass fields that are excluded from the constructor method - i.e. ones
  defined like ``field(init=False...)`` - should now be similarly handled in the
  de-serialization process.

0.14.1 (2021-09-26)
-------------------

**Bugfixes**

* The :attr:`Meta.tag` field should be updated to a ``ClassVar`` to help
  reduce the memory footprint.

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
