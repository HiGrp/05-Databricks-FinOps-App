"""Databricks connection - Setup UI (session) or automatic on Databricks App."""

from __future__ import annotations

import os
import time
from typing import Any

from app_config import DEMO, LIVE, running_in_databricks

_SESSION_KEY = "dbx_connection"


def _blank() -> dict[str, Any]:
    return {
        "host": "",
        "warehouse_id": "",
        "auth": "token",
        "token": "",
        "client_id": "",
        "client_secret": "",
        "connected": False,
        "auto": False,
        "principal": "",
    }


def init_connection() -> None:
    import streamlit as st

    if _SESSION_KEY not in st.session_state:
        st.session_state[_SESSION_KEY] = _blank()

    cfg = st.session_state[_SESSION_KEY]
    if running_in_databricks() and not cfg.get("connected"):
        st.session_state[_SESSION_KEY] = {
            "host": os.environ.get("DATABRICKS_HOST", "").strip(),
            "warehouse_id": os.environ.get("DATABRICKS_WAREHOUSE_ID", "").strip(),
            "auth": "auto",
            "token": "",
            "client_id": os.environ.get("DATABRICKS_CLIENT_ID", "").strip(),
            "client_secret": "",
            "connected": True,
            "auto": True,
            "principal": os.environ.get("DATABRICKS_CLIENT_ID", "").strip(),
        }
        st.session_state.data_source = LIVE


def get_config() -> dict[str, Any]:
    import streamlit as st

    init_connection()
    return st.session_state[_SESSION_KEY]


def is_connected() -> bool:
    return bool(get_config().get("connected")) or running_in_databricks()


def _wait_sql(w, statement_id: str, resp) -> tuple[bool, str]:
    while resp.status.state.value in ("PENDING", "RUNNING"):
        time.sleep(0.4)
        resp = w.statement_execution.get_statement(statement_id=statement_id)
    if resp.status.state.value == "FAILED":
        msg = resp.status.error.message if resp.status.error else "SQL failed"
        return False, msg
    return True, ""


def save_connection(
    host: str,
    warehouse_id: str,
    *,
    auth: str,
    token: str = "",
    client_id: str = "",
    client_secret: str = "",
) -> tuple[bool, str]:
    import streamlit as st
    from databricks.sdk import WorkspaceClient

    host = host.strip().rstrip("/")
    warehouse_id = warehouse_id.strip()
    if not host.startswith("http"):
        return False, "Workspace URL must start with https://"
    if not warehouse_id:
        return False, "SQL warehouse ID is required."

    try:
        if auth == "sp":
            cid, secret = client_id.strip(), client_secret.strip()
            if not cid or not secret:
                return False, "Client ID and secret are required."
            w = WorkspaceClient(host=host, client_id=cid, client_secret=secret)
            principal = cid
            stored = {"auth": "sp", "token": "", "client_id": cid, "client_secret": secret}
        else:
            tok = token.strip()
            if not tok:
                return False, "Access token is required."
            w = WorkspaceClient(host=host, token=tok)
            me = w.current_user.me()
            principal = me.user_name or me.display_name or "connected-user"
            stored = {"auth": "token", "token": tok, "client_id": "", "client_secret": ""}

        resp = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement="SELECT 1",
            wait_timeout="30s",
        )
        ok, err = _wait_sql(w, resp.statement_id, resp)
        if not ok:
            return False, err

        st.session_state[_SESSION_KEY] = {
            "host": host,
            "warehouse_id": warehouse_id,
            "connected": True,
            "auto": False,
            "principal": principal,
            **stored,
        }
        st.session_state.data_source = LIVE
        return True, f"Connected as `{principal}`."
    except Exception as exc:
        return False, str(exc)


def disconnect() -> None:
    import streamlit as st

    st.session_state[_SESSION_KEY] = _blank()
    st.session_state.data_source = LIVE


def get_workspace_client():
    from databricks.sdk import WorkspaceClient

    if running_in_databricks():
        return WorkspaceClient()

    cfg = get_config()
    if not cfg.get("connected"):
        raise RuntimeError("Not connected - open Setup and connect your workspace.")

    host = cfg["host"]
    if cfg["auth"] == "sp":
        return WorkspaceClient(
            host=host,
            client_id=cfg["client_id"],
            client_secret=cfg["client_secret"],
        )
    return WorkspaceClient(host=host, token=cfg["token"])


def get_warehouse_id() -> str | None:
    wh = get_config().get("warehouse_id", "").strip()
    if wh:
        return wh
    if running_in_databricks():
        env_wh = os.environ.get("DATABRICKS_WAREHOUSE_ID", "").strip()
        if env_wh:
            return env_wh
    return None


def grant_principal() -> str:
    cfg = get_config()
    p = (cfg.get("principal") or "").strip()
    if p:
        return p
    env_id = os.environ.get("DATABRICKS_CLIENT_ID", "").strip()
    return env_id or "<your-user-or-service-principal>"
