import os
import sys


# Library Log Level
LOG_LEVEL = os.getenv('WIZARD_LOG_LEVEL', 'ERROR').upper()

# Check if currently running Python 3.6
PY36 = sys.version_info[:2] == (3, 6)

# Check if currently running Python 3.8
PY38 = sys.version_info[:2] == (3, 8)

# Check if currently running Python 3.8 or higher
PY38_OR_ABOVE = sys.version_info[:2] >= (3, 8)

# Check if currently running Python 3.10 or higher
PY310_OR_ABOVE = sys.version_info[:2] >= (3, 10)

# The dictionary key that identifies the default loader / dumper
_DEFAULT = '__DEFAULT__'

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
