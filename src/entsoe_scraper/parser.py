"""Generic ENTSO-E XML -> rows parser.

Nothing is hardcoded per document type. Every ENTSO-E document is a tree of
header -> TimeSeries -> Period -> Point. Each <Point> becomes one row containing:
  - its own fields (Point.position, Point.quantity, ...)
  - every scalar value of its ancestors, flattened to dotted column names
    (e.g. TimeSeries.MktPSRType.psrType, TimeSeries.Period.resolution)
  - timestamp_utc computed from the period start, resolution and position.
New fields in the response simply become new columns.
"""

import re
from collections.abc import Iterator
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element

from defusedxml.ElementTree import fromstring

ACK_ROOT = "Acknowledgement_MarketDocument"
DURATION = re.compile(r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?)?$")

Row = dict[str, str]


class NoDataError(Exception):
    """The API answered with an Acknowledgement document (e.g. no data for the period)."""


class UnexpectedStructureError(Exception):
    """The response is valid XML but not in the expected TimeSeries/Period/Point layout."""


def parse(xml: bytes) -> list[Row]:
    root = fromstring(xml)
    for element in root.iter():
        element.tag = element.tag.rsplit("}", 1)[-1]

    if root.tag == ACK_ROOT:
        raise NoDataError(root.findtext("Reason/text", default="unknown reason"))

    rows = list(_walk(root, {}, ""))
    if not rows:
        raise UnexpectedStructureError(f"No <Point> elements found in <{root.tag}>")
    return rows


def _walk(element: Element, context: Row, prefix: str) -> Iterator[Row]:
    context = dict(context)
    points, branches = [], []
    for child in element:
        if child.tag == "Point":
            points.append(child)
        elif child.find(".//Point") is not None:
            branches.append(child)
        else:
            _flatten(child, context, prefix)

    if points:
        yield from _period_rows(points, context, prefix)
    for branch in branches:
        yield from _walk(branch, context, f"{prefix}{branch.tag}.")


def _flatten(element: Element, out: Row, prefix: str) -> None:
    key = f"{prefix}{element.tag}"
    if len(element) == 0:
        out[key] = (element.text or "").strip()
    for child in element:
        _flatten(child, out, f"{key}.")


def _period_rows(points: list[Element], context: Row, prefix: str) -> Iterator[Row]:
    by_position: dict[int, Row] = {}
    for point in points:
        fields: Row = {}
        _flatten(point, fields, prefix)
        by_position[int(fields[f"{prefix}Point.position"])] = fields

    start = _parse_time(context.get(f"{prefix}timeInterval.start"))
    end = _parse_time(context.get(f"{prefix}timeInterval.end"))
    step = _parse_duration(context.get(f"{prefix}resolution", ""))
    if not (start and end and step):
        for fields in by_position.values():
            yield {"timestamp_utc": "", **context, **fields}
        return

    fill = any(k.endswith("curveType") and v == "A03" for k, v in context.items())
    last: Row | None = None
    for position in range(1, int((end - start) / step) + 1):
        fields = by_position.get(position)
        if fields is None and fill and last is not None:
            fields = {**last, f"{prefix}Point.position": str(position)}
        if fields is None:
            continue
        last = fields
        timestamp = start + (position - 1) * step
        yield {"timestamp_utc": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"), **context, **fields}


def _parse_time(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _parse_duration(value: str) -> timedelta | None:
    """ISO 8601 durations used by ENTSO-E (PT15M, PT60M, P1D, ...); None for months/years."""
    match = DURATION.match(value)
    if not match or not any(match.groups()):
        return None
    days, hours, minutes = (int(g or 0) for g in match.groups())
    return timedelta(days=days, hours=hours, minutes=minutes)
