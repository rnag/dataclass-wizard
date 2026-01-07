from logging import Logger

LOG: Logger

def enable_library_debug_logging(
    debug: bool | int,
    logger: Logger = LOG,
) -> int:
    ...
