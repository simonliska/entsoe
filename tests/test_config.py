from pathlib import Path

import pytest
import yaml

from entsoe_scraper.config import ConfigError, DatasetConfig

DATASETS_FILE = Path(__file__).parents[1] / "config" / "datasets.yaml"


def test_repository_datasets_are_valid():
    """Fails the PR if someone commits an invalid config/datasets.yaml."""
    datasets = yaml.safe_load(DATASETS_FILE.read_text())
    assert datasets
    for name, data in datasets.items():
        DatasetConfig.from_dict(name, data)


def test_unknown_key_is_rejected():
    with pytest.raises(ConfigError, match="unknown keys"):
        DatasetConfig.from_dict("x", {"param": {}})


def test_missing_field_is_rejected():
    with pytest.raises(ConfigError, match="invalid or missing"):
        DatasetConfig.from_dict("x", {"params": {"documentType": "A71"}})
