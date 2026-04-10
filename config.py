"""
Configuration module for ElixirMind.

Provides:
- sensible defaults
- environment variable overrides
- config file loading
- lightweight validation
- backwards-compatible dict access for existing modules
"""

from __future__ import annotations

import json
import os
from copy import deepcopy
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass(slots=True)
class AppConfig:
    """Typed application configuration with safe defaults."""

    emulator_type: str = "memu"
    memu_path: str = r"C:\Program Files\Microvirt\MEmu\MEmu.exe"
    bluestacks_path: str = r"C:\Program Files\BlueStacks\HD-Player.exe"
    instance_id: int = 0
    debug: bool = False
    log_level: str = "INFO"
    poll_interval_seconds: float = 0.25
    config_path: str = "config.json"

    def to_dict(self) -> Dict[str, Any]:
        """Return a mutable dictionary for compatibility with legacy modules."""
        return asdict(self)


DEFAULT_CONFIG = AppConfig()
SUPPORTED_EMULATORS = {"memu", "bluestacks", "ldplayer"}


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_file_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        return {}

    with config_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(f"Configuration file must contain a JSON object: {config_path}")

    return data


def _load_environment_overrides() -> Dict[str, Any]:
    overrides: Dict[str, Any] = {}

    env_map = {
        "ELIXIRMIND_EMULATOR_TYPE": ("emulator_type", str),
        "ELIXIRMIND_MEMU_PATH": ("memu_path", str),
        "ELIXIRMIND_BLUESTACKS_PATH": ("bluestacks_path", str),
        "ELIXIRMIND_INSTANCE_ID": ("instance_id", int),
        "ELIXIRMIND_DEBUG": ("debug", _parse_bool),
        "ELIXIRMIND_LOG_LEVEL": ("log_level", str),
        "ELIXIRMIND_POLL_INTERVAL_SECONDS": ("poll_interval_seconds", float),
    }

    for env_name, (config_key, caster) in env_map.items():
        raw_value = os.getenv(env_name)
        if raw_value is None:
            continue
        overrides[config_key] = caster(raw_value)

    return overrides


def _validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    validated = deepcopy(config)

    emulator_type = str(validated.get("emulator_type", DEFAULT_CONFIG.emulator_type)).lower()
    if emulator_type not in SUPPORTED_EMULATORS:
        raise ValueError(
            f"Unsupported emulator_type '{emulator_type}'. "
            f"Supported values: {sorted(SUPPORTED_EMULATORS)}"
        )
    validated["emulator_type"] = emulator_type

    instance_id = int(validated.get("instance_id", DEFAULT_CONFIG.instance_id))
    if instance_id < 0:
        raise ValueError("instance_id must be >= 0")
    validated["instance_id"] = instance_id

    poll_interval = float(
        validated.get("poll_interval_seconds", DEFAULT_CONFIG.poll_interval_seconds)
    )
    if poll_interval <= 0:
        raise ValueError("poll_interval_seconds must be > 0")
    validated["poll_interval_seconds"] = poll_interval

    validated["debug"] = bool(validated.get("debug", DEFAULT_CONFIG.debug))
    validated["log_level"] = str(validated.get("log_level", DEFAULT_CONFIG.log_level)).upper()

    return validated


def build_config(config_path: str = "config.json") -> AppConfig:
    """Build a typed configuration object from defaults, file, and env vars."""
    path = Path(config_path)
    merged = DEFAULT_CONFIG.to_dict()
    merged["config_path"] = str(path)

    merged.update(_load_file_config(path))
    merged.update(_load_environment_overrides())

    validated = _validate_config(merged)
    validated["config_path"] = str(path)

    return AppConfig(**validated)


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """
    Load configuration and return a dictionary.

    Kept as a dict-returning API for backwards compatibility with the rest of
    the codebase.
    """
    return build_config(config_path).to_dict()
