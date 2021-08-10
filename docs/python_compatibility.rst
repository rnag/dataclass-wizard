.. highlight:: shell

================
Py Compatibility
================

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
    * `Annotated`_ (added by `PEP 593`_) ``*``

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
-----------------------

You can import the new types (for example, the ones mentioned above) using the below
syntax:

.. code-block:: python3

    from typing_extensions import Literal, TypedDict, Annotated

