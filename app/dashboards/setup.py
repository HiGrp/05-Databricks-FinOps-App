"""Setup — connect (app) + permissions (Databricks)."""

from __future__ import annotations

import streamlit as st

from app_config import running_in_databricks
from connection import disconnect, get_config, grant_principal, is_connected, save_connection
from dashboards.catalog_config import get_catalog
from dashboards.components import page_header

SYSTEM_SCHEMAS = ("billing", "access", "compute", "lakeflow", "query")


def _grants_sql(catalog: str, principal: str) -> str:
    lines = [f"GRANT USE CATALOG ON CATALOG {catalog} TO `{principal}`;"]
    lines += [f"GRANT USE SCHEMA, SELECT ON SCHEMA {catalog}.{s} TO `{principal}`;" for s in SYSTEM_SCHEMAS]
    return "\n".join(lines)


def _render_connect_step() -> None:
    st.markdown("### 1. Connect — in this app")
    st.markdown(
        "**What you need from Databricks** (gather these first):\n"
        "- Your **workspace URL**\n"
        "- A **SQL warehouse ID** (warehouse must be running)\n"
        "- Either your **personal access token** *or* a **service principal** (see below)"
    )

    st.markdown(
        "**Access token** *(pick this if you are alone / testing)*\n"
        "- This is **your** Databricks login, like a temporary password\n"
        "- Databricks → **Settings** → **Developer** → **Access tokens** → **Generate new token**\n"
        "- Copy it (starts with `dapi…`) — you won't see it again\n\n"
        "**Service principal** *(pick this for production / shared install)*\n"
        "- A **robot account**, not a person — for apps running 24/7 for a team\n"
        "- Databricks → **Admin console** → **Identity and access** → **Service principals**\n"
        "- Create one → **Secrets** tab → generate **OAuth secret** → copy **Client ID** + **Secret**"
    )

    cfg = get_config()

    if running_in_databricks():
        st.success("Running as a Databricks App — connection is automatic.")
        st.caption(f"Warehouse `{cfg.get('warehouse_id') or '—'}` · identity `{grant_principal()}`")
    elif cfg.get("connected"):
        st.success(f"Connected to `{cfg.get('host')}` as `{grant_principal()}`")
        if st.button("Disconnect", key="dbx_disconnect"):
            disconnect()
            st.rerun()
    else:
        auth = st.radio(
            "How should the app authenticate?",
            ["Access token (my user)", "Service principal (robot account)"],
            horizontal=True,
            key="setup_auth",
            help="Token = you. Service principal = production app identity.",
        )
        use_sp = auth.startswith("Service")
        with st.form("dbx_connect", clear_on_submit=False):
            host = st.text_input(
                "Workspace URL",
                placeholder="https://adb-1234567890123456.7.azuredatabricks.net",
                help="Databricks → Settings → Developer → Databricks workspace URL",
            )
            warehouse = st.text_input(
                "SQL warehouse ID",
                placeholder="a1b2c3d4e5f6g7h8",
                help="SQL → SQL Warehouses → your warehouse → copy the ID from the Overview page",
            )
            token = client_id = client_secret = ""
            if use_sp:
                client_id = st.text_input("Client ID")
                client_secret = st.text_input("Client secret", type="password")
            else:
                token = st.text_input(
                    "Access token",
                    type="password",
                    help="Settings → Developer → Access tokens",
                )

            if st.form_submit_button("Connect", type="primary", use_container_width=True):
                ok, msg = save_connection(
                    host,
                    warehouse,
                    auth="sp" if use_sp else "token",
                    token=token,
                    client_id=client_id,
                    client_secret=client_secret,
                )
                if ok:
                    st.rerun()
                else:
                    st.error(msg)


def _render_permissions_step() -> None:
    st.markdown("### 2. Permissions — in Databricks")
    principal = grant_principal()
    connected = is_connected()

    st.markdown(
        "**Do this once** in your Databricks workspace:\n"
        "1. Open Databricks in your browser\n"
        "2. Go to **SQL** → **SQL Editor**\n"
        "3. Select the **same SQL warehouse** as in step 1 (dropdown top-left)\n"
        "4. You must run this as a **metastore admin** (or ask yours to run it for you)\n"
        "5. Copy the script below → paste in SQL Editor → click **Run**\n"
        "6. Come back here → click **↻ Refresh** on any page"
    )

    if connected:
        st.markdown(
            f"The script below grants read access to **`{principal}`** "
            f"(the identity you connected with) on catalog **`{get_catalog()}`**."
        )
    else:
        st.info("Connect in step 1 first — the script will show your exact user or service principal.")

    st.code(_grants_sql(get_catalog(), principal), language="sql")

    if connected and not principal.startswith("<"):
        st.caption(
            "Token auth → principal is your email. "
            "Service principal → principal is the Client ID."
        )


def render_setup(_run_query=None) -> None:
    page_header("Setup")
    with st.container(border=True):
        _render_connect_step()
    with st.container(border=True):
        _render_permissions_step()
