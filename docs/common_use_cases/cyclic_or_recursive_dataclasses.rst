Cyclic or "Recursive" Dataclasses
=================================

.. note::
    **Important:** The current functionality for cyclic or "recursive" dataclasses is being re-imagined.
    Please refer to the new docs for **V1 Opt-in** features, which introduces enhanced support for these use
    cases. For more details, see the `Field Guide to V1 Opt‐in`_ and the `Recursive Types and Dataclasses with Cyclic References in V1`_ documentation.

    This change is part of the ongoing improvements in version ``v0.34.0+``, and the old functionality will no longer be maintained in future releases.

.. _Field Guide to V1 Opt‐in: https://github.com/rnag/dataclass-wizard/wiki/Field-Guide-to-V1-Opt%E2%80%90in
.. _Recursive Types and Dataclasses with Cyclic References in V1: https://github.com/rnag/dataclass-wizard/wiki/V1:-Recursive-Types-and-Dataclasses-with-Cyclic-References

Prior to version ``v0.27.0``, dataclasses with cyclic references
or self-referential structures were not supported. This
limitation is shown in the following toy example:

.. code:: python3

    from dataclasses import dataclass

    from dataclass_wizard import JSONWizard


    @dataclass
    class A(JSONWizard):
        a: 'A | None' = None


    a = A.from_dict({'a': {'a': {'a': None}}})
    assert a == A(a=A(a=A(a=None)))

This has been a `longstanding issue`_.

New in ``v0.27.0``: The Dataclass Wizard now extends its support
to cyclic and self-referential dataclass models.

The example below demonstrates recursive dataclasses with cyclic
dependencies, following the pattern ``A -> B -> A -> B``.

With Class Inheritance
**********************

Here’s a basic example demonstrating the use of recursive dataclasses
with cyclic dependencies, using a class inheritance model and
the :class:`JSONWizard` mixin:

.. code:: python3

    from __future__ import annotations  # This can be removed in Python 3.10+

    from dataclasses import dataclass

    from dataclass_wizard import JSONWizard


    @dataclass
    class A(JSONWizard):
        class _(JSONWizard.Meta):
            # enable support for self-referential / recursive dataclasses
            recursive_classes = True

        b: 'B | None' = None


    @dataclass
    class B:
        a: A | None = None


    # confirm that `from_dict` with a recursive, self-referential
    # input `dict` works as expected.
    a = A.from_dict({'b': {'a': {'b': {'a': None}}}})
    assert a == A(b=B(a=A(b=B())))

Without Class Inheritance
*************************

Here is the same example as above, but with relying solely on ``dataclasses``, without
using any special class inheritance model:


.. code:: python3

    from __future__ import annotations  # This can be removed in Python 3.10+

    from dataclasses import dataclass

    from dataclass_wizard import fromdict, LoadMeta


    @dataclass
    class A:
        b: 'B | None' = None


    @dataclass
    class B:
        a: A | None = None


    # enable support for self-referential / recursive dataclasses
    LoadMeta(recursive_classes=True).bind_to(A)

    # confirm that `from_dict` with a recursive, self-referential
    # input `dict` works as expected.
    a = fromdict(A, {'b': {'a': {'b': {'a': None}}}})
    assert a == A(b=B(a=A(b=B())))

.. _longstanding issue: https://github.com/rnag/dataclass-wizard/issues/62
