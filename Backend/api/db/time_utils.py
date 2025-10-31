from datetime import datetime, timezone
from zoneinfo import ZoneInfo

TH_TZ = ZoneInfo("Asia/Bangkok")

def now_th() -> datetime:
    """Return timezone-aware datetime in Asia/Bangkok."""
    return datetime.now(tz=TH_TZ)


def to_th(dt: datetime | None) -> datetime | None:
    if not dt:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=TH_TZ)
    return dt.astimezone(TH_TZ)
