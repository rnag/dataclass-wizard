from logging import getLogger

from .constants import LOG_LEVEL, PACKAGE_NAME


LOG = getLogger(PACKAGE_NAME)
LOG.setLevel(LOG_LEVEL)
