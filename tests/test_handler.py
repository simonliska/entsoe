import json
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

from entsoe_scraper import client, handler

FIXTURES = Path(__file__).parent / "fixtures"
BUCKET = "test-bucket"
DATASET = {
    "params": {"documentType": "A71", "processType": "A01"},
    "area_params": ["in_Domain"],
    "areas": ["10YSK-SEPS-----K"],
    "window": {"start_offset_days": 1, "days": 1},
}


@pytest.fixture
def aws(monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-central-1")
    monkeypatch.setenv("BUCKET_NAME", BUCKET)
    monkeypatch.setenv("CONFIG_PARAM_PREFIX", "/entsoe-scraper/datasets")
    monkeypatch.setenv("TOKEN_PARAM_NAME", "/entsoe-scraper/api-token")
    with mock_aws():
        ssm = boto3.client("ssm")
        ssm.put_parameter(
            Name="/entsoe-scraper/datasets/forecast", Type="String", Value=json.dumps(DATASET)
        )
        ssm.put_parameter(Name="/entsoe-scraper/api-token", Type="SecureString", Value="test-token")
        boto3.client("s3").create_bucket(
            Bucket=BUCKET, CreateBucketConfiguration={"LocationConstraint": "eu-central-1"}
        )
        yield


def test_backfill_writes_csv_to_s3(aws, monkeypatch):
    calls = []

    def fake_fetch(params, token):
        calls.append((params, token))
        return (FIXTURES / "a71_forecast_sk.xml").read_bytes()

    monkeypatch.setattr(client, "fetch", fake_fetch)

    result = handler.lambda_handler(
        {"dataset": "forecast", "start": "2026-01-01", "end": "2026-01-01"}, None
    )

    params, token = calls[0]
    assert token == "test-token"
    assert params["in_Domain"] == "10YSK-SEPS-----K"
    assert (params["periodStart"], params["periodEnd"]) == ("202512312300", "202601012300")

    key = result["files"][0]["key"]
    assert key.startswith("forecast/area=10YSK-SEPS-----K/date=2026-01-01/")
    body = boto3.client("s3").get_object(Bucket=BUCKET, Key=key)["Body"].read().decode()
    assert len(body.splitlines()) == 25


def test_no_data_writes_nothing(aws, monkeypatch):
    monkeypatch.setattr(
        client, "fetch", lambda params, token: (FIXTURES / "ack_no_data.xml").read_bytes()
    )

    result = handler.lambda_handler({"dataset": "forecast"}, None)

    assert result["files"] == []
