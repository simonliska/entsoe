from pathlib import Path

import pytest

from entsoe_scraper.parser import NoDataError, UnexpectedStructureError, parse
from entsoe_scraper.storage import to_csv

FIXTURES = Path(__file__).parent / "fixtures"
QUANTITY = "TimeSeries.Period.Point.quantity"
POSITION = "TimeSeries.Period.Point.position"


def load(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_day_ahead_forecast_forward_fills_a03_gaps():
    rows = parse(load("a71_forecast_sk.xml"))

    assert len(rows) == 24
    assert [int(r[POSITION]) for r in rows] == list(range(1, 25))
    assert rows[1][QUANTITY] == rows[0][QUANTITY]
    assert rows[0]["timestamp_utc"] == "2025-12-31T23:00:00Z"
    assert rows[-1]["timestamp_utc"] == "2026-01-01T22:00:00Z"
    assert rows[0]["TimeSeries.inBiddingZone_Domain.mRID"] == "10YSK-SEPS-----K"


def test_actual_per_unit_flattens_nested_fields():
    rows = parse(load("a73_actual_per_unit_sk.xml"))

    assert len(rows) == 29 * 24
    assert rows[0]["TimeSeries.MktPSRType.PowerSystemResources.name"] == "Čierny Váh TG1"
    assert {r["TimeSeries.MktPSRType.psrType"] for r in rows} >= {"B10", "B14"}


def test_csv_header_is_union_of_all_fields():
    rows = parse(load("a73_actual_per_unit_sk.xml"))
    header = to_csv(rows).decode().splitlines()[0].split(",")

    assert "TimeSeries.outBiddingZone_Domain.mRID" in header
    assert "TimeSeries.inBiddingZone_Domain.mRID" in header
    assert header[0] == "timestamp_utc"


def test_unknown_structure_fails_loudly():
    xml = b"<GL_MarketDocument><TimeSeries><Period><Interval><pos>1</pos></Interval></Period>"
    xml += b"</TimeSeries></GL_MarketDocument>"
    with pytest.raises(UnexpectedStructureError):
        parse(xml)


def test_acknowledgement_raises_no_data():
    with pytest.raises(NoDataError, match="No matching data"):
        parse(load("ack_no_data.xml"))
