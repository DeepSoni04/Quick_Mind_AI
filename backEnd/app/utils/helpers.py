import re
from datetime import datetime, timezone


def make_avatar(name: str = "") -> str:
    """Generate 2-character uppercase avatar from full name."""
    if not name:
        return "QM"
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    elif len(parts) == 1 and len(parts[0]) > 0:
        return parts[0][:2].upper()
    return "QM"


def utc_now() -> datetime:
    """Return current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def format_relative_time(dt: datetime) -> str:
    """Format datetime into relative humanized string (e.g., '2 min ago', 'Just now')."""
    if not dt:
        return "Just now"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    diff = (now - dt).total_seconds()
    if diff < 60:
        return "Just now"
    elif diff < 3600:
        mins = int(diff // 60)
        return f"{mins} min ago"
    elif diff < 86400:
        hours = int(diff // 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff < 172800:
        return "Yesterday"
    else:
        days = int(diff // 86400)
        return f"{days} days ago"
