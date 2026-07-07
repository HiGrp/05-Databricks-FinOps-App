"""License enforcement — offline Ed25519, bound to Databricks workspace_id.

Distribution model:
- No auto-trial file (resettable). Every key is vendor-signed.
- Trial keys: ``license_tool issue --trial --workspace-id <id>`` (durée : ``config.toml`` → ``trial_days``)
- Paid keys: same tool with longer validity.
- Keys are bound to one workspace; copying the package elsewhere fails validation.
- Works fully offline (no license server, no outbound Internet).
"""

from __future__ import annotations

import base64
import json
import os
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

from dashboards.app_metadata import APP_ID, APP_SUPPORT_EMAIL

# Fallback public key (overridden by license_public_key.txt if present).
_EMBEDDED_PUBLIC_KEY_B64 = "qzYI4Ex6nVdMRDlNI8TTavrTjDqiKBEdytLg30dq+ww="

_ROOT = Path(__file__).resolve().parent


# --------------------------------------------------------------------------- #
# base64url helpers
# --------------------------------------------------------------------------- #

def _b64u_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64u_decode(txt: str) -> bytes:
    pad = "=" * (-len(txt) % 4)
    return base64.urlsafe_b64decode(txt + pad)


# --------------------------------------------------------------------------- #
# Workspace identity (read locally — stays inside customer network)
# --------------------------------------------------------------------------- #

@lru_cache(maxsize=1)
def get_current_workspace_id() -> str | None:
    """Return this Databricks workspace ID, or None if unavailable."""
    from app_config import is_dev_mode

    if is_dev_mode():
        return "dev-local"

    try:
        from databricks.sdk import WorkspaceClient

        wid = WorkspaceClient().get_workspace_id()
        if wid is not None:
            return str(wid)
    except Exception:
        pass

    for env_key in ("DATABRICKS_WORKSPACE_ID", "WORKSPACE_ID"):
        raw = os.environ.get(env_key, "").strip()
        if raw:
            return raw
    return None


def format_workspace_id_for_display() -> str:
    wid = get_current_workspace_id()
    return wid if wid else "— (could not detect — run as Databricks App)"


# --------------------------------------------------------------------------- #
# Storage
# --------------------------------------------------------------------------- #

def _state_dir() -> Path:
    d = Path.home() / f".{APP_ID}"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return d


def _license_file() -> Path:
    return _state_dir() / "license.key"


def _load_public_key_b64() -> str:
    key_path = _ROOT / "license_public_key.txt"
    try:
        txt = key_path.read_text(encoding="utf-8").strip()
        if txt:
            return txt
    except Exception:
        pass
    return _EMBEDDED_PUBLIC_KEY_B64


# --------------------------------------------------------------------------- #
# License verification
# --------------------------------------------------------------------------- #

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


def _workspace_matches(payload: dict) -> tuple[bool, str | None]:
    """Check workspace_id binding. Returns (ok, error_message)."""
    bound = payload.get("workspace_id")
    if not bound:
        return False, "This license key is missing a workspace_id (legacy format not accepted)."

    current = get_current_workspace_id()
    if not current:
        return False, "Could not detect this workspace's ID — cannot validate the license key."

    if str(bound) != str(current):
        return False, (
            f"License is for workspace {bound}, but this app runs in workspace {current}."
        )
    return True, None


def _validate_payload(payload: dict) -> tuple[bool, str]:
    """Full validation: dates + workspace binding."""
    exp = _parse_date(payload.get("exp", ""))
    if exp and exp < date.today():
        return False, f"This license expired on {exp.isoformat()}."

    ok, err = _workspace_matches(payload)
    if not ok:
        return False, err or "Workspace mismatch."
    return True, ""


def _installed_license() -> dict | None:
    """Read + cryptographically verify the stored license."""
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


def save_license(token: str) -> tuple[bool, str]:
    """Validate then persist a license key. Returns (ok, message)."""
    payload = verify_license_token(token)
    if not payload:
        return False, "Invalid license key (bad signature or wrong product)."

    ok, msg = _validate_payload(payload)
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


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def get_access_status() -> dict:
    """Compute current access state (licensed or blocked — no local auto-trial)."""
    lic = _installed_license()
    if lic:
        ok, msg = _validate_payload(lic)
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

    return {
        "state": "expired",
        "allowed": False,
        "days_left": 0,
        "message": "No valid license key. Request a trial or paid key for this workspace.",
        "payload": None,
    }


def _render_workspace_id_block(container) -> None:
    wid = format_workspace_id_for_display()
    container.markdown(
        f"**Workspace ID** (include this when requesting a key):\n\n`{wid}`"
    )
    container.caption(
        f"Contact [{APP_SUPPORT_EMAIL}](mailto:{APP_SUPPORT_EMAIL}) "
        "with your workspace ID to get a trial or paid license key."
    )


def render_status_sidebar() -> None:
    """License badge + key entry in the sidebar."""
    import streamlit as st

    status = get_access_status()
    icon = {"licensed": "✅", "trial": "⏳", "expired": "⛔"}.get(status["state"], "•")
    st.sidebar.caption(f"{icon} {status['message']}")

    if status["state"] in ("licensed", "trial") and status.get("days_left") is not None:
        if status["days_left"] <= 3:
            st.sidebar.warning(f"⏳ {status['days_left']} day(s) left on this key.")

    if status["allowed"]:
        return

    with st.sidebar.expander("🔑 Enter license key"):
        _render_workspace_id_block(st.sidebar)
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


def render_license_gate() -> None:
    """Block the app when no valid key is installed (st.stop)."""
    import streamlit as st

    status = get_access_status()
    if status["allowed"]:
        if status["state"] == "trial" and status.get("days_left") is not None and status["days_left"] <= 3:
            st.warning(f"⏳ Trial: {status['days_left']} day(s) left. "
                       "Enter a paid license key in the sidebar to keep access.")
        return

    from dashboards.app_metadata import APP_ICON, APP_NAME

    st.markdown(f"## {APP_ICON} {APP_NAME}")
    st.error(status["message"])
    _render_workspace_id_block(st)
    st.markdown("Paste your license key below to unlock the application.")
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
