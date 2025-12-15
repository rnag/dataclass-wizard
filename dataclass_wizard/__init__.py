"""
Dataclass Wizard
~~~~~~~~~~~~~~~~

Lightning-fast JSON wizardry for Python dataclasses — effortless
serialization right out of the box!

Sample Usage:

    >>> from dataclasses import dataclass, field
    >>> from datetime import datetime
    >>> from typing import Optional
    >>>
    >>> from dataclass_wizard import JSONSerializable, property_wizard
    >>>
    >>>
    >>> @dataclass
    >>> class MyClass(JSONSerializable, metaclass=property_wizard):
    >>>
    >>>     my_str: Optional[str]
    >>>     list_of_int: list[int] = field(default_factory=list)
    >>>     # You can also define this as `my_dt`, however only the annotation
    >>>     # will carry over in that case, since the value is re-declared by
    >>>     # the property below.
    >>>     _my_dt: datetime = datetime(2000, 1, 1)
    >>>
    >>>     @property
    >>>     def my_dt(self):
    >>>     # A sample `getter` which returns the datetime with year set as 2010
    >>>         if self._my_dt is not None:
    >>>             return self._my_dt.replace(year=2010)
    >>>         return self._my_dt
    >>>
    >>>     @my_dt.setter
    >>>     def my_dt(self, new_dt: datetime):
    >>>     # A sample `setter` which sets the inverse (roughly) of the `month` and `day`
    >>>         self._my_dt = new_dt.replace(month=13 - new_dt.month,
    >>>                                      day=30 - new_dt.day)
    >>>
    >>>
    >>> string = '''{"myStr": 42, "listOFInt": [1, "2", 3]}'''
    >>> c = MyClass.from_json(string)
    >>> print(repr(c))
    >>> # prints:
    >>> #   MyClass(
    >>> #       my_str='42',
    >>> #       list_of_int=[1, 2, 3],
    >>> #       my_dt=datetime.datetime(2010, 12, 29, 0, 0)
    >>> #   )
    >>> my_dict = {'My_Str': 'string', 'myDT': '2021-01-20T15:55:30Z'}
    >>> c = MyClass.from_dict(my_dict)
    >>> print(repr(c))
    >>> # prints:
    >>> #   MyClass(
    >>> #       my_str='string',
    >>> #       list_of_int=[],
    >>> #       my_dt=datetime.datetime(2010, 12, 10, 15, 55, 30,
    >>> #                               tzinfo=datetime.timezone.utc)
    >>> #   )
    >>> print(c.to_json())
    >>> # prints:
    >>> #   {"myStr": "string", "listOfInt": [], "myDt": "2010-12-10T15:55:30Z"}

For full documentation and more advanced usage, please see
<https://dcw.ritviknag.com>.

:copyright: (c) 2021-2025 by Ritvik Nag.
:license: Apache 2.0, see LICENSE for more details.
"""

__all__ = [
    # Base exports
    'DataclassWizard',
    'JSONSerializable',
    'JSONPyWizard',
    'JSONWizard',
    'LoadMixin',
    'DumpMixin',
    'property_wizard',
    # Wizard Mixins
    'EnvWizard',
    'JSONListWizard',
    'JSONFileWizard',
    'TOMLWizard',
    'YAMLWizard',
    # Helper serializer functions + meta config
    'fromlist',
    'fromdict',
    'asdict',
    'LoadMeta',
    'DumpMeta',
    'EnvMeta',
    # Models
    'env_field',
    'json_field',
    'json_key',
    'path_field',
    'skip_if_field',
    'KeyPath',
    'Container',
    'Pattern',
    'DatePattern',
    'TimePattern',
    'DateTimePattern',
    'CatchAll',
    'SkipIf',
    'SkipIfNone',
    'EQ',
    'NE',
    'LT',
    'LE',
    'GT',
    'GE',
    'IS',
    'IS_NOT',
    'IS_TRUTHY',
    'IS_FALSY',
]

import logging

from .bases_meta import LoadMeta, DumpMeta, EnvMeta
from .constants import PACKAGE_NAME
from .dumpers import DumpMixin, setup_default_dumper
from .loaders import LoadMixin, setup_default_loader
from .loader_selection import asdict, fromlist, fromdict
from .models import (env_field, json_field, json_key, path_field, skip_if_field,
                     KeyPath, Container,
                     Pattern, DatePattern, TimePattern, DateTimePattern,
                     CatchAll, SkipIf, SkipIfNone,
                     EQ, NE, LT, LE, GT, GE, IS, IS_NOT, IS_TRUTHY, IS_FALSY)
from .environ.wizard import EnvWizard
from .property_wizard import property_wizard
from .serial_json import DataclassWizard, JSONWizard, JSONPyWizard, JSONSerializable
from .wizard_mixins import JSONListWizard, JSONFileWizard, TOMLWizard, YAMLWizard


# Set up logging to ``/dev/null`` like a library is supposed to.
# http://docs.python.org/3.3/howto/logging.html#configuring-logging-for-a-library
logging.getLogger(PACKAGE_NAME).addHandler(logging.NullHandler())

# Setup the default type hooks to use when converting `str` (json) or a Python
# `dict` object to a `dataclass` instance.
setup_default_loader()

# Setup the default type hooks to use when converting `dataclass` instances to
# a JSON `string` or a Python `dict` object.
setup_default_dumper()
