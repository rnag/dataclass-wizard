=======
History
=======

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
