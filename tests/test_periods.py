from datetime import date

from entsoe_scraper.config import Window
from entsoe_scraper.periods import chunks, to_api_period, window_days


def test_window_tomorrow():
    assert window_days(Window(1, 1), date(2026, 1, 1)) == (date(2026, 1, 2), date(2026, 1, 2))


def test_window_yesterday():
    assert window_days(Window(-1, 1), date(2026, 1, 1)) == (date(2025, 12, 31), date(2025, 12, 31))


def test_api_period_winter_and_summer():
    assert to_api_period(date(2026, 1, 1), date(2026, 1, 1)) == ("202512312300", "202601012300")
    assert to_api_period(date(2026, 7, 1), date(2026, 7, 1)) == ("202606302200", "202607012200")


def test_api_period_dst_switch_day_has_23_hours():
    assert to_api_period(date(2026, 3, 29), date(2026, 3, 29)) == ("202603282300", "202603292200")


def test_chunks():
    assert chunks(date(2026, 1, 1), date(2026, 1, 3), 1) == [
        (date(2026, 1, 1), date(2026, 1, 1)),
        (date(2026, 1, 2), date(2026, 1, 2)),
        (date(2026, 1, 3), date(2026, 1, 3)),
    ]
    assert chunks(date(2026, 1, 1), date(2026, 1, 3), 365) == [(date(2026, 1, 1), date(2026, 1, 3))]
