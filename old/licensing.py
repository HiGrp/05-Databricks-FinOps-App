"""License enforcement — offline Ed25519 + automatic local trial.

- First launch: auto trial for ``trial_days`` (config.toml), no key required.
- After trial: vendor-signed key required (not bound to workspace_id).
- Works fully offline.
"""

from __future__ import annotations

import base64
import json
import os
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path

from app_config import trial_days
from dashboards.app_metadata import APP_ID, APP_SUPPORT_EMAIL

_EMBEDDED_PUBLIC_KEY_B64 = "qzYI4Ex6nVdMRDlNI8TTavrTjDqiKBEdytLg30dq+ww="

_ROOT = Path(__file__).resolve().parent


def _b64u_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64u_decode(txt: str) -> bytes:
    pad = "=" * (-len(txt) % 4)
    return base64.urlsafe_b64decode(txt + pad)


def _state_dir() -> Path:
    d = Path.home() / f".{APP_ID}"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return d


def _license_file() -> Path:
    return _state_dir() / "license.key"


def _trial_file() -> Path:
    return _state_dir() / "trial.json"


def _load_public_key_b64() -> str:
    key_path = _ROOT / "license_public_key.txt"
    try:
        txt = key_path.read_text(encoding="utf-8").strip()
        if txt:
            return txt
    except Exception:
        pass
    return _EMBEDDED_PUBLIC_KEY_B64


def verify_license_token(token: str) -> dict | None:
    """Return payload if signature is valid and product matches; else None."""
    token = (token or "").strip().replace("\n", "")
    if token.count(".") != 1:
        return None
    payload_b64, sig_b64 = token.split(".")
    try:
        payload_raw = _b64u_decode(payload_b64)
        signature = _b64u_decode(sig_b64)
    except Exception:
        return None

    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        pub = Ed25519PublicKey.from_public_bytes(base64.b64decode(_load_public_key_b64()))
        pub.verify(signature, payload_raw)
    except Exception:
        return None

    try:
        payload = json.loads(payload_raw.decode("utf-8"))
    except Exception:
        return None

    if payload.get("app") != APP_ID:
        return None
    return payload


def _parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _validate_license_payload(payload: dict) -> tuple[bool, str]:
    exp = _parse_date(payload.get("exp", ""))
    if exp and exp < date.today():
        return False, f"This license expired on {exp.isoformat()}."
    return True, ""


def _installed_license() -> dict | None:
    candidates = [os.environ.get("APP_LICENSE_TOKEN", "")]
    for p in (_ROOT / "license.key", _license_file()):
        try:
            candidates.append(p.read_text(encoding="utf-8"))
        except Exception:
            continue

    for token in candidates:
        payload = verify_license_token(token)
        if payload:
            return payload
    return None


def _read_trial_start() -> date | None:
    try:
        data = json.loads(_trial_file().read_text(encoding="utf-8"))
        return _parse_date(data.get("started", ""))
    except Exception:
        return None


def _ensure_trial_started() -> date:
    started = _read_trial_start()
    if started is not None:
        return started
    started = date.today()
    try:
        _trial_file().write_text(
            json.dumps({"started": started.isoformat()}),
            encoding="utf-8",
        )
    except Exception:
        pass
    return started


def _auto_trial_status() -> dict | None:
    """Local auto trial — starts on first use, no vendor key."""
    days = trial_days()
    started = _ensure_trial_started()
    exp = started + timedelta(days=days)
    days_left = (exp - date.today()).days
    if days_left < 0:
        return {
            "state": "expired",
            "allowed": False,
            "days_left": 0,
            "message": f"Auto trial ended on {exp.isoformat()}. Enter a license key to continue.",
            "payload": None,
        }
    return {
        "state": "trial",
        "allowed": True,
        "days_left": days_left,
        "message": f"Auto trial · {days_left} day(s) left · expires {exp.isoformat()}",
        "payload": None,
    }


def save_license(token: str) -> tuple[bool, str]:
    """Validate then persist a license key. Returns (ok, message)."""
    payload = verify_license_token(token)
    if not payload:
        return False, "Invalid license key (bad signature or wrong product)."

    ok, msg = _validate_license_payload(payload)
    if not ok:
        return False, msg

    try:
        _license_file().write_text(token.strip(), encoding="utf-8")
    except Exception as exc:
        return False, f"Could not save license: {exc}"

    plan = payload.get("plan", "custom")
    customer = payload.get("customer", "customer")
    exp = payload.get("exp", "?")
    return True, f"License activated ({plan}) for {customer} until {exp}."


def get_access_status() -> dict:
    """Licensed key > auto trial > blocked."""
    lic = _installed_license()
    if lic:
        ok, msg = _validate_license_payload(lic)
        if ok:
            exp = _parse_date(lic.get("exp", ""))
            days_left = (exp - date.today()).days if exp else None
            plan = lic.get("plan", "licensed")
            label = "Trial" if plan == "trial" else "Licensed"
            return {
                "state": "trial" if plan == "trial" else "licensed",
                "allowed": True,
                "days_left": days_left,
                "message": f"{label} · {lic.get('customer', 'customer')}"
                           + (f" · expires {lic.get('exp')}" if exp else ""),
                "payload": lic,
            }
        return {
            "state": "expired",
            "allowed": False,
            "days_left": 0,
            "message": msg or "License is no longer valid.",
            "payload": lic,
        }

    return _auto_trial_status() or {
        "state": "expired",
        "allowed": False,
        "days_left": 0,
        "message": "Trial expired. Contact the vendor for a license key.",
        "payload": None,
    }


def render_status_sidebar() -> None:
    """License badge + key entry in the sidebar."""
    import streamlit as st

    status = get_access_status()
    icon = {"licensed": "✅", "trial": "⏳", "expired": "⛔"}.get(status["state"], "•")
    st.sidebar.caption(f"{icon} {status['message']}")

    if status["state"] in ("licensed", "trial") and status.get("days_left") is not None:
        if status["days_left"] <= 3:
            st.sidebar.warning(f"⏳ {status['days_left']} day(s) left.")

    if status["allowed"] and status["state"] != "expired":
        with st.sidebar.expander("🔑 Enter license key"):
            with st.form("license_form_sidebar", clear_on_submit=False):
                token = st.text_area("License key", height=110, placeholder="eyJ...  .  ...")
                submitted = st.form_submit_button("Activate", type="primary")
            if submitted:
                ok, msg = save_license(token)
                if ok:
                    st.success(msg)
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(msg)
        return

    with st.sidebar.expander("🔑 Enter license key"):
        st.caption(f"Contact [{APP_SUPPORT_EMAIL}](mailto:{APP_SUPPORT_EMAIL}) for a key.")
        with st.form("license_form_sidebar_blocked", clear_on_submit=False):
            token = st.text_area("License key", height=110, placeholder="eyJ...  .  ...")
            submitted = st.form_submit_button("Activate", type="primary")
        if submitted:
            ok, msg = save_license(token)
            if ok:
                st.success(msg)
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(msg)


def render_license_gate() -> None:
    """Block the app when trial expired and no valid key (st.stop)."""
    import streamlit as st

    status = get_access_status()
    if status["allowed"]:
        if status["state"] == "trial" and status.get("days_left") is not None and status["days_left"] <= 3:
            st.warning(f"⏳ Trial: {status['days_left']} day(s) left. "
                       "Enter a license key in the sidebar to keep access.")
        return

    from dashboards.app_metadata import APP_ICON, APP_NAME

    st.markdown(f"## {APP_ICON} {APP_NAME}")
    st.error(status["message"])
    st.markdown(
        f"Contact [{APP_SUPPORT_EMAIL}](mailto:{APP_SUPPORT_EMAIL}) "
        "to get a license key, then paste it below."
    )
    with st.form("license_form", clear_on_submit=False):
        token = st.text_area("License key", height=140, placeholder="eyJ...  .  ...")
        submitted = st.form_submit_button("Activate license", type="primary")
    if submitted:
        ok, msg = save_license(token)
        if ok:
            st.success(msg)
            st.cache_data.clear()
            st.rerun()
        else:
            st.error(msg)
    st.stop()
