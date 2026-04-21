"""
Lightweight FastAPI service that receives NocoDB webhooks and triggers
Prefect pipeline flows.

Runs inside the Docker network — not exposed to the internet.

Webhooks need to be set up on NocoDB: 
https://nocodb.com/docs/product-docs/automation/webhook/create-webhook
"""

import logging
import os
import threading
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from pipelines.export.export_country_images import export_country_images
from pipelines.export.export_team_images import export_team_images
from pipelines.export.export_pmtiles import export_pmtiles_flow
from pipelines.tasks.build_search_index import build_search_index

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="VCM WaterWatch Pipeline Worker")

# Tables whose changes should trigger a PMTiles rebuild
PMTILES_TRIGGER_TABLES = {"Country", "DistributionZone"}

# Tables whose changes should trigger a country/team images mirror
COUNTRY_IMAGES_TRIGGER_TABLES = {"Country"}
TEAM_IMAGES_TRIGGER_TABLES = {"Team"}

# Tables whose changes should trigger a search index rebuild
SEARCH_INDEX_TRIGGER_TABLES = {"DistributionZone", "Municipality"}

# Debounce delay — how long to wait after the last webhook before running the flow.
# Override via WEBHOOK_DEBOUNCE_SECONDS env var. Default 60s.
DEBOUNCE_SECONDS = float(os.environ.get("WEBHOOK_DEBOUNCE_SECONDS", "60"))

# Lock and timer for PMTiles debounce
_debounce_lock = threading.Lock()
_debounce_timer: threading.Timer | None = None

# Lock and timer for search index debounce
_search_debounce_lock = threading.Lock()
_search_debounce_timer: threading.Timer | None = None

# Country images flow runs without debounce (webhook fires rarely and users
# want to see the new image immediately). A lock still exists for test-suite
# compatibility but is no longer used to schedule timers.
_country_images_debounce_lock = threading.Lock()
_country_images_debounce_timer: threading.Timer | None = None

# Serialize all Prefect flow runs so only one ephemeral server exists at a time
_flow_run_lock = threading.Lock()


def _run_flow():
    """Run the export flow. Called by the debounce timer."""
    with _flow_run_lock:
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


def _run_search_index_flow():
    """Run the search index flow. Called by the debounce timer."""
    with _flow_run_lock:
        try:
            build_search_index()
        except Exception:
            logger.exception("Search index flow failed")


def _schedule_search_index():
    """Schedule (or reschedule) the search index flow after DEBOUNCE_SECONDS."""
    global _search_debounce_timer
    with _search_debounce_lock:
        if _search_debounce_timer is not None:
            _search_debounce_timer.cancel()
        _search_debounce_timer = threading.Timer(DEBOUNCE_SECONDS, _run_search_index_flow)
        _search_debounce_timer.daemon = True
        _search_debounce_timer.start()


def _run_country_images_flow():
    """Run the country images mirror flow in a background thread."""
    logger.info("Country images flow: acquiring flow-run lock")
    with _flow_run_lock:
        logger.info("Country images flow: starting export")
        try:
            export_country_images()
            logger.info("Country images flow: completed successfully")
        except Exception:
            logger.exception("Country images flow failed")


def _schedule_country_images():
    """Trigger the country images flow immediately in a background thread.

    No debounce: webhook frequency for Country edits is low and users expect
    the mirror to update promptly after an image change.
    """
    logger.info("Country images: dispatching flow run (no debounce)")
    t = threading.Thread(target=_run_country_images_flow, name="country-images-flow", daemon=True)
    t.start()


def _run_team_images_flow():
    """Run the team images mirror flow in a background thread."""
    logger.info("Team images flow: acquiring flow-run lock")
    with _flow_run_lock:
        logger.info("Team images flow: starting export")
        try:
            export_team_images()
            logger.info("Team images flow: completed successfully")
        except Exception:
            logger.exception("Team images flow failed")


def _schedule_team_images():
    """Trigger the team images flow immediately in a background thread.

    No debounce: webhook frequency for Team edits is low and users expect
    the mirror to update promptly after an image change.
    """
    logger.info("Team images: dispatching flow run (no debounce)")
    t = threading.Thread(target=_run_team_images_flow, name="team-images-flow", daemon=True)
    t.start()


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

    scheduled = []

    if table_name in PMTILES_TRIGGER_TABLES:
        logger.info(
            f"Webhook received for table {table_name}, scheduling PMTiles export"
        )
        _schedule_export()
        scheduled.append("export_pmtiles")

    if table_name in SEARCH_INDEX_TRIGGER_TABLES:
        logger.info(
            f"Webhook received for table {table_name}, scheduling search index rebuild"
        )
        _schedule_search_index()
        scheduled.append("build_search_index")

    if table_name in COUNTRY_IMAGES_TRIGGER_TABLES:
        logger.info(
            f"Webhook received for table {table_name}, scheduling country images mirror"
        )
        _schedule_country_images()
        scheduled.append("export_country_images")

    if table_name in TEAM_IMAGES_TRIGGER_TABLES:
        logger.info(
            f"Webhook received for table {table_name}, scheduling team images mirror"
        )
        _schedule_team_images()
        scheduled.append("export_team_images")

    if scheduled:
        return JSONResponse(
            status_code=202,
            content={"status": "accepted", "pipelines": scheduled},
        )

    logger.info(f"Webhook received for table {table_name}, ignoring")
    return {"status": "ignored"}
