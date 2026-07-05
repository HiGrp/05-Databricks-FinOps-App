"""Vendor-side license tool (KEEP PRIVATE — do not ship with the app).

Generate a signing key pair, then issue signed license keys that the app unlocks
with its embedded public key.

Usage
-----
Generate a key pair (run once, keep the private key secret)::

    python tools/license_tool.py keygen

    # -> writes tools/license_private_key.txt (SECRET)
    #    writes license_public_key.txt          (ship this in the app)

Issue a license key::

    python tools/license_tool.py issue --customer "ACME Corp" --plan yearly --days 365
    python tools/license_tool.py issue --customer "ACME Corp" --plan monthly --months 1
    python tools/license_tool.py issue --customer "Trial+" --until 2027-01-31

The printed token is what the customer pastes into the app's license screen.
"""

from __future__ import annotations

import argparse
import base64
import json
from datetime import date, timedelta
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
_PRIVATE_KEY_PATH = _HERE / "license_private_key.txt"
_PUBLIC_KEY_PATH = _ROOT / "license_public_key.txt"

# Must match dashboards/app_metadata.py::APP_ID
APP_ID = "finops-optimizer"


def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


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
    _PRIVATE_KEY_PATH.write_text(base64.b64encode(priv_raw).decode() + "\n", encoding="utf-8")
    _PUBLIC_KEY_PATH.write_text(base64.b64encode(pub_raw).decode() + "\n", encoding="utf-8")
    print(f"Private key (SECRET) -> {_PRIVATE_KEY_PATH}")
    print(f"Public key  (ship)   -> {_PUBLIC_KEY_PATH}")
    print("\nKeep the private key safe. Anyone with it can issue valid licenses.")


def _load_private_key():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    txt = _PRIVATE_KEY_PATH.read_text(encoding="utf-8").strip()
    return Ed25519PrivateKey.from_private_bytes(base64.b64decode(txt))


def cmd_issue(args) -> None:
    if args.until:
        exp = date.fromisoformat(args.until)
    elif args.months:
        exp = date.today() + timedelta(days=30 * args.months)
    else:
        exp = date.today() + timedelta(days=args.days)

    payload = {
        "app": APP_ID,
        "customer": args.customer,
        "plan": args.plan,
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
    parser = argparse.ArgumentParser(description="FinOps Optimizer license tool")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("keygen", help="Generate a new signing key pair")

    p_issue = sub.add_parser("issue", help="Issue a signed license key")
    p_issue.add_argument("--customer", required=True, help="Customer / org name")
    p_issue.add_argument("--plan", default="custom", help="monthly | yearly | custom")
    p_issue.add_argument("--days", type=int, default=365, help="Validity in days (default 365)")
    p_issue.add_argument("--months", type=int, help="Validity in months (30d each)")
    p_issue.add_argument("--until", help="Explicit expiry date YYYY-MM-DD")

    args = parser.parse_args()
    if args.command == "keygen":
        cmd_keygen(args)
    elif args.command == "issue":
        cmd_issue(args)


if __name__ == "__main__":
    main()
