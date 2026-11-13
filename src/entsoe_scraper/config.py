"""Dataset configuration: validation and loading from SSM Parameter Store."""

import json
from dataclasses import dataclass
from typing import Any

ALLOWED_KEYS = {"schedule", "params", "area_params", "areas", "window", "max_period_days"}


class ConfigError(ValueError):
    """Raised when a dataset configuration is invalid."""


@dataclass(frozen=True)
class Window:
    start_offset_days: int
    days: int


@dataclass(frozen=True)
class DatasetConfig:
    name: str
    params: dict[str, str]
    area_params: tuple[str, ...]
    areas: tuple[str, ...]
    window: Window
    max_period_days: int = 365

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> DatasetConfig:
        unknown = set(data) - ALLOWED_KEYS
        if unknown:
            raise ConfigError(f"{name}: unknown keys {sorted(unknown)}")
        try:
            window = data["window"]
            config = cls(
                name=name,
                params={str(k): str(v) for k, v in data["params"].items()},
                area_params=tuple(data["area_params"]),
                areas=tuple(data["areas"]),
                window=Window(int(window["start_offset_days"]), int(window["days"])),
                max_period_days=int(data.get("max_period_days", 365)),
            )
        except (KeyError, TypeError, AttributeError, ValueError) as exc:
            raise ConfigError(f"{name}: invalid or missing field ({exc})") from exc

        if not config.area_params or not config.areas:
            raise ConfigError(f"{name}: area_params and areas must not be empty")
        if config.window.days < 1 or config.max_period_days < 1:
            raise ConfigError(f"{name}: window.days and max_period_days must be >= 1")
        return config


def load_dataset(ssm: Any, prefix: str, name: str) -> DatasetConfig:
    """Load a dataset config stored as JSON in SSM at ``{prefix}/{name}``."""
    value = ssm.get_parameter(Name=f"{prefix}/{name}")["Parameter"]["Value"]
    return DatasetConfig.from_dict(name, json.loads(value))
