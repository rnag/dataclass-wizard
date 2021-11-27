.. highlight:: shell

================
Py Compatibility
================

Python 3.6+
-----------

Just a quick note that even though this library supports Python 3.6+,
some of the new features introduced in the latest Python
versions might not be available from the ``typing`` module, depending on
the Python version installed.

To work around that, there's a great library called ``typing-extensions`` (you can
find it on PyPI `here`_) that backports all the new
``typing`` features introduced so that earlier Python versions can also
benefit from them. Note that the ``dataclass-wizard`` package already requires
this dependency for **Python version 3.9 or earlier**, so there's no need
to install this library separately.

With the ``typing-extensions`` module, you can take advantage of the
following new types from the ``typing`` module for Python 3.6+. Most of them are currently
supported by the ``JSONSerializable`` class, however the ones that are *not*
are marked with an asterisk (``*``) below.

Introduced in *Python 3.9*:
    * `Annotated`_ (added by `PEP 593`_)

Introduced in *Python 3.8*:
    * `Literal`_
    * `TypedDict`_
    * `Final`_ ``*``

Introduced in *Python 3.7*:
    * `OrderedDict`_


``*`` - Currently not supported by ``JSONSerializable`` at this time, though this
may change in a future release.

.. _here: https://pypi.org/project/typing-extensions/
.. _Annotated: https://docs.python.org/3.9/library/typing.html#typing.Annotated
.. _PEP 593: https://www.python.org/dev/peps/pep-0593/
.. _Final: https://docs.python.org/3.8/library/typing.html#typing.Final
.. _Literal: https://docs.python.org/3.8/library/typing.html#typing.Literal
.. _OrderedDict: https://docs.python.org/3.7/library/typing.html#typing.OrderedDict
.. _TypedDict: https://docs.python.org/3.8/library/typing.html#typing.TypedDict

Importing the New Types
~~~~~~~~~~~~~~~~~~~~~~~

You can import the new types (for example, the ones mentioned above) using the below
syntax:

.. code-block:: python3

    from typing_extensions import Literal, TypedDict, Annotated


Python 3.7+
-----------

The Dataclass Wizard library supports the parsing of *future annotations* (also
known as forward-declared annotations) which are enabled via a
``from __future__ import annotations`` import added at the top of a module; this
declaration allows `PEP 585`_ and `PEP 604`_- style annotations to be used in
Python 3.7 and higher. The one main benefit, is that static type checkers and
IDEs such as PyCharm appear to have solid support for using new-style
annotations in this way.

The following Python code illustrates the paradigm of future annotations in
Python 3.7+ code; notice that a ``__future__`` import is added at the top, for
compatibility with versions earlier than 3.10. In the annotations, we also prefer
to use parameterized standard collections, and the new pipe ``|`` syntax to
represent ``Union`` and ``Optional`` types.

.. code:: python3

    from __future__ import annotations

    import datetime
    from dataclasses import dataclass
    from decimal import Decimal

    from dataclass_wizard import JSONWizard


    @dataclass
    class A(JSONWizard):
        field_1: str | int | bool
        field_2: int | tuple[str | int] | bool
        field_3: Decimal | datetime.date | str
        field_4: str | int | None
        field_6: dict[str | int, list[B | C | D | None]]


    @dataclass
    class B:
        ...


    @dataclass
    class C:
        ...


    @dataclass
    class D:
        ...

The Latest and Greatest
-----------------------

If you already have Python 3.10 or higher, you can leverage the new support for parameterized
standard collections that was added as part of `PEP 585`_, as well as the ability to write
Union types as ``X | Y`` which is introduced in `PEP 604`_, and avoid these imports from
the ``typing`` module altogether:

.. code:: python3

    from collections import defaultdict
    from dataclasses import dataclass

    from dataclass_wizard import JSONWizard


    @dataclass
    class MyClass(JSONWizard):
        my_list: list[str]
        my_dict: defaultdict[str, list[int]]
        my_tuple: tuple[int | str, ...]


    if __name__ == '__main__':
        data = {'my_list': ['testing'], 'my_dict': {'key': [1, 2, '3']}, 'my_tuple': (1, '2')}

        c = MyClass.from_dict(data)

        print(repr(c))
        # prints:
        #   MyClass(my_list=['testing'], my_dict=defaultdict(<class 'list'>, {'key': [1, 2, 3]}), my_tuple=(1, '2'))


.. _PEP 585: https://www.python.org/dev/peps/pep-0585/
.. _PEP 604: https://www.python.org/dev/peps/pep-0604/
