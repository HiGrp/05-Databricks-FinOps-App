"""Vendor-side license tool (KEEP PRIVATE — do not ship with the app)."""

from __future__ import annotations

import argparse
import base64
import json
import sys
from datetime import date, timedelta
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_ROOT))

from app_config import trial_days  # noqa: E402

_PRIVATE_KEY_PATH = _HERE / "license_private_key.txt"
_PUBLIC_KEY_PATH = _ROOT / "license_public_key.txt"
_LICENSING_PY = _ROOT / "licensing.py"

APP_ID = "finops-optimizer"


def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _sync_embedded_public_key(pub_b64: str) -> None:
    if not _LICENSING_PY.is_file():
        return
    text = _LICENSING_PY.read_text(encoding="utf-8")
    marker = "_EMBEDDED_PUBLIC_KEY_B64 = "
    if marker not in text:
        return
    lines = text.splitlines()
    out = []
    for line in lines:
        if line.startswith(marker):
            out.append(f'{marker}"{pub_b64.strip()}"')
        else:
            out.append(line)
    _LICENSING_PY.write_text("\n".join(out) + "\n", encoding="utf-8")


def cmd_keygen(_args) -> None:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    priv = Ed25519PrivateKey.generate()
    priv_raw = priv.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_raw = priv.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    pub_b64 = base64.b64encode(pub_raw).decode()
    _PRIVATE_KEY_PATH.write_text(base64.b64encode(priv_raw).decode() + "\n", encoding="utf-8")
    _PUBLIC_KEY_PATH.write_text(pub_b64 + "\n", encoding="utf-8")
    _sync_embedded_public_key(pub_b64)
    print(f"Private key (SECRET) -> {_PRIVATE_KEY_PATH}")
    print(f"Public key  (ship)   -> {_PUBLIC_KEY_PATH}")
    print("Embedded public key updated in licensing.py")


def _load_private_key():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    txt = _PRIVATE_KEY_PATH.read_text(encoding="utf-8").strip()
    return Ed25519PrivateKey.from_private_bytes(base64.b64decode(txt))


def cmd_issue(args) -> None:
    if not args.workspace_id or not str(args.workspace_id).strip():
        raise SystemExit("--workspace-id is required for all license keys.")

    if args.trial and not args.until and not args.months and args.days == 365:
        args.days = trial_days()

    if args.until:
        exp = date.fromisoformat(args.until)
    elif args.months:
        exp = date.today() + timedelta(days=30 * args.months)
    else:
        exp = date.today() + timedelta(days=args.days)

    plan = "trial" if args.trial else args.plan

    payload = {
        "app": APP_ID,
        "customer": args.customer,
        "plan": plan,
        "workspace_id": str(args.workspace_id).strip(),
        "iat": date.today().isoformat(),
        "exp": exp.isoformat(),
    }
    payload_raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

    priv = _load_private_key()
    signature = priv.sign(payload_raw)
    token = f"{_b64u(payload_raw)}.{_b64u(signature)}"

    print("License payload:")
    print(json.dumps(payload, indent=2))
    print("\nLicense key (send to customer):\n")
    print(token)


def main() -> None:
    default_trial = trial_days()
    parser = argparse.ArgumentParser(description="FinOps Optimizer license tool")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("keygen", help="Generate a new signing key pair")

    p_issue = sub.add_parser("issue", help="Issue a signed license key")
    p_issue.add_argument("--customer", required=True, help="Customer / org name")
    p_issue.add_argument(
        "--workspace-id", required=True,
        help="Databricks workspace ID (shown in the app when no key is installed)",
    )
    p_issue.add_argument("--plan", default="yearly", help="monthly | yearly | custom | trial")
    p_issue.add_argument(
        "--trial", action="store_true",
        help=f"Trial key (plan=trial, default {default_trial} days from config.toml)",
    )
    p_issue.add_argument(
        "--days", type=int, default=365,
        help=f"Validity in days (trial default: {default_trial} from config.toml)",
    )
    p_issue.add_argument("--months", type=int, help="Validity in months (30d each)")
    p_issue.add_argument("--until", help="Explicit expiry date YYYY-MM-DD")

    args = parser.parse_args()
    if args.command == "keygen":
        cmd_keygen(args)
    elif args.command == "issue":
        cmd_issue(args)


if __name__ == "__main__":
    main()
