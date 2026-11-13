"""AWS Lambda entrypoint.

Event: {"dataset": "<name>"} for scheduled runs,
       {"dataset": "<name>", "start": "YYYY-MM-DD", "end": "YYYY-MM-DD"} for a backfill.
"""

import logging
import os
from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import Any

import boto3

from entsoe_scraper import client, periods
from entsoe_scraper.config import DatasetConfig, load_dataset
from entsoe_scraper.parser import NoDataError, parse
from entsoe_scraper.storage import object_key, to_csv

logger = logging.getLogger()
logger.setLevel(logging.INFO)

Writer = Callable[[str, bytes], None]


def run(
    config: DatasetConfig,
    token: str,
    write: Writer,
    start: date | None = None,
    end: date | None = None,
) -> dict[str, Any]:
    """Fetch -> parse -> store for every area and period chunk. Shared by Lambda and local runs."""
    if start is None or end is None:
        start, end = periods.window_days(config.window, datetime.now(periods.LOCAL_TZ).date())
    run_at = datetime.now(UTC)
    files = []

    for area in config.areas:
        for first, last in periods.chunks(start, end, config.max_period_days):
            period_start, period_end = periods.to_api_period(first, last)
            params = {
                **config.params,
                **dict.fromkeys(config.area_params, area),
                "periodStart": period_start,
                "periodEnd": period_end,
            }
            rows = []
            try:
                for document in client.documents(client.fetch(params, token)):
                    rows.extend(parse(document))
            except NoDataError as exc:
                logger.warning(
                    "No data", extra={"dataset": config.name, "area": area, "reason": str(exc)}
                )
                continue

            key = object_key(config.name, area, first, run_at)
            write(key, to_csv(rows))
            files.append({"key": key, "rows": len(rows)})
            logger.info("Stored", extra={"dataset": config.name, "key": key, "rows": len(rows)})

    return {
        "dataset": config.name,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "files": files,
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    ssm = boto3.client("ssm")
    s3 = boto3.client("s3")
    bucket = os.environ["BUCKET_NAME"]

    config = load_dataset(ssm, os.environ["CONFIG_PARAM_PREFIX"], event["dataset"])
    token = ssm.get_parameter(Name=os.environ["TOKEN_PARAM_NAME"], WithDecryption=True)
    start, end = event.get("start"), event.get("end")

    return run(
        config,
        token["Parameter"]["Value"],
        write=lambda key, body: s3.put_object(
            Bucket=bucket, Key=key, Body=body, ContentType="text/csv"
        ),
        start=date.fromisoformat(start) if start else None,
        end=date.fromisoformat(end) if end else None,
    )
