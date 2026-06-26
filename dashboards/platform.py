"""Dashboards plateforme — API, ingestion, logs."""

import streamlit as st
import pandas as pd

from dashboards.components import (
    bar_chart,
    data_table,
    page_header,
    pie_chart,
    show_error,
)


def render_api_inventory(run_query) -> None:
    page_header("Inventaire API", "REST API Databricks (live)")
    st.info(
        "Configurez l'intégration API Databricks pour afficher "
        "clusters, warehouses et jobs en temps réel."
    )


def render_ingestion_health(run_query) -> None:
    page_header("Pipeline ingestion", "Suivi des runs d'ingestion FinOps")
    st.info(
        "Configurez `FINOPS_INGESTION_LOG_TABLE` (catalog.schema.table) "
        "pour alimenter cette section en production."
    )


def render_driver_logs(run_query) -> None:
    page_header("Logs driver", "Échantillon logs driver cluster")
    _render_driver_logs_prod()


def _render_driver_logs_prod() -> None:
    from prod_data import DRIVER_LOG_VOLUME, list_driver_log_files, read_driver_log

    if not DRIVER_LOG_VOLUME:
        st.info(
            "Configurez `FINOPS_DRIVER_LOG_VOLUME` (chemin Unity Volume) "
            "ou utilisez le cluster log delivery vers cloud storage."
        )
        return
    files = list_driver_log_files()
    if not files:
        st.warning(f"Aucun .log dans {DRIVER_LOG_VOLUME}")
        return
    selected = st.selectbox("Fichier log", files)
    content = read_driver_log(selected)
    _show_log_content(content)


def _show_log_content(content: str) -> None:
    errors = [line for line in content.splitlines() if "ERROR" in line or "OOM" in line or "WARN" in line]
    st.metric("Lignes WARN/ERROR", len(errors))
    st.code(content[:8000], language="log")
