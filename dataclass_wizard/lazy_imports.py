"""
Lazy Import definitions. Generally, these imports will be available when any
"bonus features" are installed, i.e. as below:

  $ pip install dataclass-wizard[timedelta]
"""

from .utils.lazy_loader import LazyLoader


# csv: to add support for (de)serializing CSV data to dataclass instances
csv = LazyLoader(globals(), 'csv')

# pytimeparse: for parsing JSON string values as a `datetime.timedelta`
pytimeparse = LazyLoader(globals(), 'pytimeparse', 'timedelta')

# PyYAML: to add support for (de)serializing YAML data to dataclass instances
yaml = LazyLoader(globals(), 'yaml', 'yaml', local_name='PyYAML')
