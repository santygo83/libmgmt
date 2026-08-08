"""Small time utilities."""
from datetime import UTC, datetime


def utcnow() -> datetime:
    """Timezone-naive UTC now (stored naive for DB portability)."""
    return datetime.now(UTC).replace(tzinfo=None)
