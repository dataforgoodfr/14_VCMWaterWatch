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


def _run_in_background(flow_fn, **kwargs):
    """Run a Prefect flow in a background thread so the webhook returns immediately."""

    def target():
        try:
            flow_fn(**kwargs)
        except Exception:
            logger.exception("Background flow failed")

    thread = threading.Thread(target=target, daemon=True)
    thread.start()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/webhooks/nocodb")
def nocodb_webhook(payload: dict):
    """
    Handle NocoDB webhook payloads.

    When a relevant table is changed, triggers the PMTiles export flow
    in a background thread.
    """
    table_name = None
    if isinstance(payload.get("data"), dict):
        table_name = payload["data"].get("table_name")

    if table_name in PMTILES_TRIGGER_TABLES:
        logger.info(
            f"Webhook received for table {table_name}, triggering PMTiles export"
        )
        data_dir = Path(os.environ.get("PM_TILES_DIR", "data/export"))
        _run_in_background(export_pmtiles_flow, destination=data_dir)
        return JSONResponse(
            status_code=202,
            content={"status": "accepted", "pipeline": "export_pmtiles"},
        )

    logger.info(f"Webhook received for table {table_name}, ignoring")
    return {"status": "ignored"}
