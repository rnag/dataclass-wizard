import os
import sys


# Package name
PACKAGE_NAME = 'dataclass_wizard'

# Library Log Level
LOG_LEVEL = os.getenv('WIZARD_LOG_LEVEL', 'ERROR').upper()

# Current system Python version
_PY_VERSION = sys.version_info[:2]

# Check if currently running Python 3.10 or higher
PY310_OR_ABOVE = _PY_VERSION >= (3, 10)

# Check if currently running Python 3.11 or higher
PY311_OR_ABOVE = _PY_VERSION >= (3, 11)

# Check if currently running Python 3.12 or higher
PY312_OR_ABOVE = _PY_VERSION >= (3, 12)

# Check if currently running Python 3.13 or higher
PY313_OR_ABOVE = _PY_VERSION >= (3, 13)

# Check if currently running Python 3.14 or higher
PY314_OR_ABOVE = _PY_VERSION >= (3, 14)

# The name of the dictionary object that contains `load` hooks for each
# object type. Also used to check if a class is a :class:`BaseLoadHook`
_LOAD_HOOKS = '__LOAD_HOOKS__'

# The name of the dictionary object that contains `dump` hooks for each
# object type. Also used to check if a class is a :class:`BaseDumpHook`
_DUMP_HOOKS = '__DUMP_HOOKS__'

# Attribute name that will be defined for single-arg alias functions and
# methods; mainly for internal use.
SINGLE_ARG_ALIAS = '__SINGLE_ARG_ALIAS__'

# Attribute name that will be defined for identity functions and methods;
# mainly for internal use.
IDENTITY = '__IDENTITY__'

# The dictionary key that identifies the tag field for a class. This is only
# set when the `tag` field or the `auto_assign_tags` flag is enabled in the
# `Meta` config for a dataclass.
#
# Note that this key can also be customized in the `Meta` config for a class,
# via the :attr:`tag_key` field.
TAG = '__tag__'


# INTERNAL USE ONLY: The dictionary key that the library
# sets/uses to identify a "catch all" field, which captures
# JSON key/values that don't map to any known dataclass fields.
CATCH_ALL = '<-|CatchAll|->'
