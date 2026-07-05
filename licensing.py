"""License + free-trial enforcement.

Model (à la Dataiku): the app runs free for N days, then locks until a valid
license key is entered. Keys are signed offline by the vendor (Ed25519); the app
only carries the *public* key, so keys cannot be forged from the shipped code.

Design goals:
- Works fully offline (no license server).
- Safe to obfuscate/distribute: no private key in the app.
- Best-effort trial tracking in the user profile directory.

A license key is a compact token: ``base64url(payload_json).base64url(signature)``
Payload example::

    {"app": "finops-optimizer", "customer": "ACME", "plan": "yearly",
     "iat": "2026-01-01", "exp": "2027-01-01"}
"""

from __future__ import annotations

import base64
import json
from datetime import date, datetime
from pathlib import Path

from dashboards.app_metadata import APP_ID

# Fallback public key (overridden by license_public_key.txt if present).
_EMBEDDED_PUBLIC_KEY_B64 = "qzYI4Ex6nVdMRDlNI8TTavrTjDqiKBEdytLg30dq+ww="

# Secret used only to detect trial-file tampering (integrity, not secrecy).
# Obfuscation hides it in distributed builds. Not security-critical.
_TRIAL_HMAC_SECRET = b"finops-optimizer::trial-integrity::v1"

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
# Storage locations
# --------------------------------------------------------------------------- #

def _state_dir() -> Path:
    d = Path.home() / f".{APP_ID}"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return d


def _trial_file() -> Path:
    return _state_dir() / "trial.json"


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
    """Return the payload dict if the token is authentic and well-formed, else None.

    Does NOT check expiry here — callers decide how to treat expired keys.
    """
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
        pub.verify(signature, payload_raw)  # raises on bad signature
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


def _installed_license() -> dict | None:
    """Read + verify the stored license (state dir, project root, or env)."""
    import os

    candidates = [
        os.environ.get("APP_LICENSE_TOKEN", ""),
    ]
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
    exp = _parse_date(payload.get("exp", ""))
    if exp and exp < date.today():
        return False, f"This license expired on {exp.isoformat()}."
    try:
        _license_file().write_text(token.strip(), encoding="utf-8")
    except Exception as exc:
        return False, f"Could not save license: {exc}"
    return True, f"License activated for {payload.get('customer', 'customer')} until {payload.get('exp', '?')}."


# --------------------------------------------------------------------------- #
# Trial tracking
# --------------------------------------------------------------------------- #

def _sign_trial(first_run_iso: str) -> str:
    import hashlib
    import hmac

    return hmac.new(_TRIAL_HMAC_SECRET, first_run_iso.encode("utf-8"), hashlib.sha256).hexdigest()


def _trial_first_run() -> datetime:
    """Return the trial start; create/repair the trial file on first run."""
    path = _trial_file()
    now = datetime.now()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        first = data.get("first_run", "")
        if data.get("sig") == _sign_trial(first):
            parsed = datetime.fromisoformat(first)
            return parsed
    except Exception:
        pass

    # First run (or tampered/missing) -> (re)start the trial now.
    iso = now.isoformat(timespec="seconds")
    try:
        path.write_text(json.dumps({"first_run": iso, "sig": _sign_trial(iso)}), encoding="utf-8")
    except Exception:
        pass
    return now


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def get_access_status() -> dict:
    """Compute current access state.

    Returns dict with keys: state ('licensed'|'trial'|'expired'),
    allowed (bool), days_left (int|None), message (str), payload (dict|None).
    """
    from app_config import trial_days

    lic = _installed_license()
    if lic:
        exp = _parse_date(lic.get("exp", ""))
        if exp is None or exp >= date.today():
            days_left = (exp - date.today()).days if exp else None
            return {
                "state": "licensed",
                "allowed": True,
                "days_left": days_left,
                "message": f"Licensed to {lic.get('customer', 'customer')}"
                           + (f" · expires {lic.get('exp')}" if exp else " · perpetual"),
                "payload": lic,
            }
        # licensed but expired -> fall through to trial/expired handling

    total = trial_days()
    start = _trial_first_run()
    used = (date.today() - start.date()).days
    days_left = total - used
    if days_left > 0:
        return {
            "state": "trial",
            "allowed": True,
            "days_left": days_left,
            "message": f"Free trial · {days_left} day(s) left of {total}",
            "payload": None,
        }
    return {
        "state": "expired",
        "allowed": False,
        "days_left": 0,
        "message": "Your free trial has ended. Enter a license key to continue.",
        "payload": None,
    }


def render_status_sidebar() -> None:
    """Small badge + license activation expander in the sidebar."""
    import streamlit as st

    status = get_access_status()
    icon = {"licensed": "✅", "trial": "⏳", "expired": "⛔"}.get(status["state"], "•")
    st.sidebar.caption(f"{icon} {status['message']}")

    if status["state"] == "licensed":
        return

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


def render_license_gate() -> None:
    """Allow the app through, or block it with a license-entry screen (st.stop)."""
    import streamlit as st

    status = get_access_status()
    if status["allowed"]:
        if status["state"] == "trial" and status["days_left"] is not None and status["days_left"] <= 3:
            st.warning(f"⏳ Free trial: {status['days_left']} day(s) left. "
                       "Enter a license key in the sidebar to keep access.")
        return

    from dashboards.app_metadata import APP_ICON, APP_NAME

    st.markdown(f"## {APP_ICON} {APP_NAME}")
    st.error(status["message"])
    st.markdown(
        "Paste your license key below to unlock the application. "
        "Need a key? Contact your vendor."
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
