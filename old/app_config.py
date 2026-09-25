"""Central configuration - read from ``config.toml`` with environment overrides.

In **distribution builds** (``.dist_build`` marker present), licensing is always
enforced and cannot be disabled via config.toml or APP_LICENSE_ENABLED.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_CONFIG_PATH = _ROOT / "config.toml"
_DIST_MARKER = _ROOT / ".dist_build"


def is_distribution_build() -> bool:
    """True when running from a compiled customer package."""
    return _DIST_MARKER.is_file()


def _load_toml() -> dict:
    try:
        import tomllib  # Python 3.11+
    except ModuleNotFoundError:  # pragma: no cover
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
    if is_distribution_build():
        return False
    cfg = _config().get("app", {})
    return _env_bool("APP_DEV_MODE", bool(cfg.get("dev_mode", False)))


def license_enabled() -> bool:
    """True -> enforce the license gate."""
    if is_distribution_build():
        return True
    cfg = _config().get("license", {})
    return _env_bool("APP_LICENSE_ENABLED", bool(cfg.get("enabled", True)))


def trial_days() -> int:
    """Auto-trial length (days) when no license key is installed."""
    raw = os.environ.get("APP_TRIAL_DAYS")
    if raw is not None:
        try:
            return max(1, int(raw.strip()))
        except ValueError:
            pass
    cfg = _config().get("license", {})
    try:
        return max(1, int(cfg.get("trial_days", 7)))
    except (TypeError, ValueError):
        return 7
