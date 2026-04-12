"""
Lightweight FastAPI service that receives NocoDB webhooks and triggers
Prefect pipeline flows.

Runs inside the Docker network — not exposed to the internet.
"""

import logging
import os
import threading
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from pipelines.export.export_pmtiles import export_pmtiles_flow

logger = logging.getLogger(__name__)

app = FastAPI(title="VCM WaterWatch Pipeline Worker")

# Tables whose changes should trigger a PMTiles rebuild
PMTILES_TRIGGER_TABLES = {"Country", "DistributionZone"}

# Debounce delay — how long to wait after the last webhook before running the flow.
# Override via WEBHOOK_DEBOUNCE_SECONDS env var. Default 60s.
DEBOUNCE_SECONDS = float(os.environ.get("WEBHOOK_DEBOUNCE_SECONDS", "60"))

# Lock and timer for debounce
_debounce_lock = threading.Lock()
_debounce_timer: threading.Timer | None = None


def _run_flow():
    """Run the export flow. Called by the debounce timer."""
    try:
        data_dir = Path(os.environ.get("PM_TILES_DIR", "data/export"))
        export_pmtiles_flow(destination=data_dir)
    except Exception:
        logger.exception("Export flow failed")


def _schedule_export():
    """Schedule (or reschedule) the export flow after DEBOUNCE_SECONDS."""
    global _debounce_timer
    with _debounce_lock:
        if _debounce_timer is not None:
            _debounce_timer.cancel()
        _debounce_timer = threading.Timer(DEBOUNCE_SECONDS, _run_flow)
        _debounce_timer.daemon = True
        _debounce_timer.start()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/webhooks/nocodb")
def nocodb_webhook(payload: dict):
    """
    Handle NocoDB webhook payloads.

    When a relevant table is changed, schedules the PMTiles export flow
    with debounce — rapid successive webhooks coalesce into a single run.
    """
    table_name = None
    if isinstance(payload.get("data"), dict):
        table_name = payload["data"].get("table_name")

    if table_name in PMTILES_TRIGGER_TABLES:
        logger.info(
            f"Webhook received for table {table_name}, scheduling PMTiles export"
        )
        _schedule_export()
        return JSONResponse(
            status_code=202,
            content={"status": "accepted", "pipeline": "export_pmtiles"},
        )

    logger.info(f"Webhook received for table {table_name}, ignoring")
    return {"status": "ignored"}
