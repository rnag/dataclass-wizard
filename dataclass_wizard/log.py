from __future__ import annotations
from logging import getLogger, Logger, StreamHandler, DEBUG

from .constants import LOG_LEVEL, PACKAGE_NAME


LOG = getLogger(PACKAGE_NAME)
LOG.setLevel(LOG_LEVEL)


def enable_library_debug_logging(
    debug: bool | int,
    logger: Logger = LOG,
) -> int:
    """
    Enable debug logging for a library logger without touching global logging.

    - Attaches a StreamHandler if none exists
    - Sets logger + handler level
    - Disables propagation to avoid duplicate logs

    Returns the resolved logging level.
    """
    lvl = DEBUG if isinstance(debug, bool) else debug

    logger.setLevel(lvl)

    if not any(isinstance(h, StreamHandler) for h in logger.handlers):
        h = StreamHandler()
        h.setLevel(lvl)
        logger.addHandler(h)
    else:
        # ensure existing stream handlers honor the new level
        for h in logger.handlers:
            if isinstance(h, StreamHandler):
                h.setLevel(lvl)

    logger.propagate = False
    return lvl
