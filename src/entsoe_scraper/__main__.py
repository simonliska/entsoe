"""Local run without AWS: reads config/datasets.yaml and ENTSOE_TOKEN, writes CSVs to ./out.

uv run python -m entsoe_scraper generation_forecast_day_ahead --start 2026-01-01 --end 2026-01-01
"""

import argparse
import json
import logging
import os
from datetime import date
from pathlib import Path

import yaml

from entsoe_scraper.config import DatasetConfig
from entsoe_scraper.handler import run


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m entsoe_scraper")
    parser.add_argument("dataset", help="dataset name from the config file")
    parser.add_argument("--config", type=Path, default=Path("config/datasets.yaml"))
    parser.add_argument("--start", type=date.fromisoformat, help="first day (YYYY-MM-DD)")
    parser.add_argument("--end", type=date.fromisoformat, help="last day, inclusive")
    parser.add_argument("--out", type=Path, default=Path("out"))
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    datasets = yaml.safe_load(args.config.read_text())
    config = DatasetConfig.from_dict(args.dataset, datasets[args.dataset])

    def write(key: str, body: bytes) -> None:
        path = args.out / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)

    summary = run(config, os.environ["ENTSOE_TOKEN"], write, start=args.start, end=args.end)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
