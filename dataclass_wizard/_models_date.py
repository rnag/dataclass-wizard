from datetime import timedelta, timezone

from .constants import PY311_OR_ABOVE


# UTC Time Zone
if PY311_OR_ABOVE:
    # https://docs.python.org/3/library/datetime.html#datetime.UTC
    from datetime import UTC
else:
    UTC: timezone = timezone.utc

# UTC time zone (no offset)
ZERO: timedelta = timedelta(0)
