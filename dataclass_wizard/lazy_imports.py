"""
Lazy Import definitions. Generally, these imports will be available when the
"bonus features" are installed, i.e. as below:

  $ pip install dataclass-wizard[timeparse]

"""
from .utils.lazy_loader import LazyLoader


# pytimeparse: for parsing JSON string values as a `datetime.timedelta`
pytimeparse = LazyLoader(globals(), 'pytimeparse', 'timeparse')
