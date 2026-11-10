"""Turn local calendar days into ENTSO-E request periods (UTC)."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from entsoe_scraper.config import Window

LOCAL_TZ = ZoneInfo("Europe/Bratislava")
API_FORMAT = "%Y%m%d%H%M"


def window_days(window: Window, today: date) -> tuple[date, date]:
    """Return the first and last local day (inclusive) covered by the window."""
    first = today + timedelta(days=window.start_offset_days)
    return first, first + timedelta(days=window.days - 1)


def chunks(first: date, last: date, max_days: int) -> list[tuple[date, date]]:
    """Split an inclusive day range into chunks of at most ``max_days`` days."""
    result = []
    start = first
    while start <= last:
        end = min(start + timedelta(days=max_days - 1), last)
        result.append((start, end))
        start = end + timedelta(days=1)
    return result


def to_api_period(first: date, last: date) -> tuple[str, str]:
    """Local days [first, last] -> (periodStart, periodEnd) in UTC, DST-safe."""

    def utc(day: date) -> str:
        local_midnight = datetime.combine(day, time.min, tzinfo=LOCAL_TZ)
        return local_midnight.astimezone(ZoneInfo("UTC")).strftime(API_FORMAT)

    return utc(first), utc(last + timedelta(days=1))
