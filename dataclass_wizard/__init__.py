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
    >>> from dataclass_wizard import JSONWizard, property_wizard
    >>>
    >>>
    >>> @dataclass
    >>> class MyClass(JSONWizard, metaclass=property_wizard):
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

:copyright: (c) 2021-2026 by Ritvik Nag.
:license: Apache 2.0, see LICENSE for more details.
"""

__all__ = [
    # TODO DEDUP
    # Base exports
    'LoadMixin',
    'DumpMixin',
    # Models
    'Alias',
    'AliasPath',
    'Env',
    # Abstract Pattern
    'Pattern',
    'AwarePattern',
    'UTCPattern',
    # "Naive" Date/Time Patterns
    'DatePattern',
    'DateTimePattern',
    'TimePattern',
    # Timezone "Aware" Date/Time Patterns
    'AwareDateTimePattern',
    'AwareTimePattern',
    # UTC Date/Time Patterns
    'UTCDateTimePattern',
    'UTCTimePattern',
    # Env Wizard
    'EnvWizard',
    'env_config',
    # Base exports
    'DataclassWizard',
    'JSONWizard',
    'register_type',
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
    'skip_if_field',
    # 'Container',
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
    # Logging
    'LOG',
]

import logging

from .bases_meta import LoadMeta, DumpMeta, EnvMeta, register_type
from .dumpers import DumpMixin, setup_default_dumper
from .loader_selection import asdict, fromlist, fromdict
from .loaders import LoadMixin, setup_default_loader
from ._env import EnvWizard, env_config
from ._log import LOG
from ._mixins import JSONListWizard, JSONFileWizard, TOMLWizard, YAMLWizard
from ._properties import property_wizard
from ._serial_json import DataclassWizard, JSONWizard
from .models import (Alias, AliasPath, CatchAll, Container, Env,
                     SkipIf, SkipIfNone,
                     skip_if_field,
                     AwarePattern, AwareTimePattern,AwareDateTimePattern,
                     UTCPattern, UTCTimePattern, UTCDateTimePattern,
                     Pattern, DatePattern, TimePattern, DateTimePattern,
                     EQ, NE, LT, LE, GT, GE, IS, IS_NOT, IS_TRUTHY, IS_FALSY
                     )


# Set up logging to ``/dev/null`` like a library is supposed to.
# http://docs.python.org/3.3/howto/logging.html#configuring-logging-for-a-library
LOG.addHandler(logging.NullHandler())

# Setup the default type hooks to use when converting `str` (json) or a Python
# `dict` object to a `dataclass` instance.
setup_default_loader()

# Setup the default type hooks to use when converting `dataclass` instances to
# a JSON `string` or a Python `dict` object.
setup_default_dumper()
