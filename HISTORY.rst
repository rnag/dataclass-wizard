=======
History
=======

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
