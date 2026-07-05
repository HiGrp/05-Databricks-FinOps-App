"""Central configuration — read from ``config.toml`` with environment overrides.

Priority (highest first):
    1. Environment variable (APP_DEV_MODE, APP_LICENSE_ENABLED, APP_TRIAL_DAYS)
    2. ``config.toml`` value
    3. Hard-coded default
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_CONFIG_PATH = _ROOT / "config.toml"


def _load_toml() -> dict:
    try:
        import tomllib  # Python 3.11+
    except ModuleNotFoundError:  # pragma: no cover - older runtimes
        try:
            import tomli as tomllib  # type: ignore
        except ModuleNotFoundError:
            return {}
    try:
        with open(_CONFIG_PATH, "rb") as fh:
            return tomllib.load(fh)
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


@lru_cache(maxsize=1)
def _config() -> dict:
    return _load_toml()


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def is_dev_mode() -> bool:
    """True -> serve local fake data instead of querying Databricks."""
    cfg = _config().get("app", {})
    return _env_bool("APP_DEV_MODE", bool(cfg.get("dev_mode", False)))


def license_enabled() -> bool:
    """True -> enforce the trial / license gate."""
    cfg = _config().get("license", {})
    return _env_bool("APP_LICENSE_ENABLED", bool(cfg.get("enabled", True)))


def trial_days() -> int:
    """Number of free trial days before the app locks."""
    raw = os.environ.get("APP_TRIAL_DAYS")
    if raw:
        try:
            return max(0, int(raw))
        except ValueError:
            pass
    cfg = _config().get("license", {})
    try:
        return max(0, int(cfg.get("trial_days", 7)))
    except (TypeError, ValueError):
        return 7
