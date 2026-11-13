"""Rows -> CSV, and where the CSV is stored."""

import csv
import io
from datetime import date, datetime

from entsoe_scraper.parser import Row


def to_csv(rows: list[Row]) -> bytes:
    """CSV with the union of all row keys as header (order of first appearance)."""
    header = list(dict.fromkeys(key for row in rows for key in row))
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def object_key(dataset: str, area: str, day: date, run_at: datetime) -> str:
    """Hive-style key, queryable later with Athena: dataset/area=../date=../<run>.csv"""
    return f"{dataset}/area={area}/date={day.isoformat()}/{run_at.strftime('%Y%m%dT%H%M%SZ')}.csv"
