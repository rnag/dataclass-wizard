from datetime import timedelta, timezone

from .constants import PY311_OR_ABOVE


# UTC Time Zone
if PY311_OR_ABOVE:
    # https://docs.python.org/3/library/datetime.html#datetime.UTC
    # noinspection PyUnresolvedReferences
    from datetime import UTC
else:
    UTC = timezone.utc  # type: ignore

# UTC time zone (no offset)
ZERO = timedelta(0)
