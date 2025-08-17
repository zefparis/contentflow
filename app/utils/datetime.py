from __future__ import annotations
from datetime import datetime, timezone, timedelta


def utcnow() -> datetime:
    """TZ-aware now in UTC (safe for Postgres timestamptz)."""
    return datetime.now(timezone.utc)


def iso_utc(dt: datetime | None = None) -> str:
    """ISO 8601 toujours en UTC."""
    return (dt or utcnow()).isoformat()
