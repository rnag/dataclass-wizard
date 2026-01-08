import sys


# Package name
PACKAGE_NAME: str
# Library Log Level
LOG_LEVEL: str
# Current system Python version
_version_info = type(sys.version_info)
_PY_VERSION: _version_info = sys.version_info[:2]
# Check if currently running Python 3.x or higher
PY310_OR_ABOVE: bool
PY311_OR_ABOVE: bool
PY312_OR_ABOVE: bool
PY313_OR_ABOVE: bool
PY314_OR_ABOVE: bool
# The name of the dictionary object that contains `dump` or `load` hooks
_DUMP_HOOKS: str
_LOAD_HOOKS: str
# Attribute names (mostly internal)
SINGLE_ARG_ALIAS: str
IDENTITY: str
TAG: str
CATCH_ALL: str
