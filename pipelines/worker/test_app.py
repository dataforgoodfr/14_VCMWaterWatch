"""Tests for the pipeline worker webhook app."""

import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from pipelines.worker.app import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_app_state():
    """Cancel pending debounce timers and wait for any running flow to finish."""
    import pipelines.worker.app as app_module

    def _cancel_timers():
        with app_module._debounce_lock:
            if app_module._debounce_timer is not None:
                app_module._debounce_timer.cancel()
                app_module._debounce_timer = None
        with app_module._search_debounce_lock:
            if app_module._search_debounce_timer is not None:
                app_module._search_debounce_timer.cancel()
                app_module._search_debounce_timer = None
        with app_module._country_images_debounce_lock:
            if app_module._country_images_debounce_timer is not None:
                app_module._country_images_debounce_timer.cancel()
                app_module._country_images_debounce_timer = None

    _cancel_timers()
    # Wait for any in-flight flow run to finish before starting the next test
    acquired = app_module._flow_run_lock.acquire(timeout=10.0)
    if acquired:
        app_module._flow_run_lock.release()
    yield
    _cancel_timers()


@pytest.fixture(autouse=True)
def zero_debounce():
    """Default to zero debounce so existing tests don't need to wait."""
    import pipelines.worker.app as app_module
    original = app_module.DEBOUNCE_SECONDS
    app_module.DEBOUNCE_SECONDS = 0
    yield
    app_module.DEBOUNCE_SECONDS = original


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestWebhookEndpoint:
    def test_webhook_triggers_export_pmtiles(self, client):
        """A POST to /webhooks/nocodb with table=Country triggers the export flow."""
        with patch("pipelines.worker.app.export_pmtiles_flow") as mock_flow, \
                patch("pipelines.worker.app.export_country_images"):
            mock_flow.return_value = None
            response = client.post(
                "/webhooks/nocodb",
                json={"type": "records.after.update", "data": {"table_name": "Country"}},
            )
            time.sleep(0.05)
        assert response.status_code == 202
        assert response.json()["status"] == "accepted"
        mock_flow.assert_called_once()

    def test_webhook_triggers_country_images_on_country(self, client):
        """A POST with table=Country also triggers the country images flow."""
        with patch("pipelines.worker.app.export_pmtiles_flow"), \
                patch("pipelines.worker.app.export_country_images") as mock_images:
            mock_images.return_value = None
            response = client.post(
                "/webhooks/nocodb",
                json={"type": "records.after.update", "data": {"table_name": "Country"}},
            )
            time.sleep(0.05)
        assert response.status_code == 202
        pipelines = response.json()["pipelines"]
        assert "export_country_images" in pipelines
        mock_images.assert_called_once()

    def test_webhook_triggers_team_images_on_team(self, client):
        """A POST with table=Team triggers the team images flow."""
        with patch("pipelines.worker.app.export_team_images") as mock_images:
            mock_images.return_value = None
            response = client.post(
                "/webhooks/nocodb",
                json={"type": "records.after.update", "data": {"table_name": "Team"}},
            )
            time.sleep(0.05)
        assert response.status_code == 202
        pipelines = response.json()["pipelines"]
        assert "export_team_images" in pipelines
        mock_images.assert_called_once()

    def test_webhook_triggers_on_distribution_zone(self, client):
        with patch("pipelines.worker.app.export_pmtiles_flow") as mock_flow, \
                patch("pipelines.worker.app.build_search_index"):
            mock_flow.return_value = None
            response = client.post(
                "/webhooks/nocodb",
                json={"type": "records.after.update", "data": {"table_name": "DistributionZone"}},
            )
            time.sleep(0.05)
        assert response.status_code == 202
        mock_flow.assert_called_once()

    def test_webhook_ignores_irrelevant_table(self, client):
        with patch("pipelines.worker.app.export_pmtiles_flow") as mock_flow:
            response = client.post(
                "/webhooks/nocodb",
                json={"type": "records.after.update", "data": {"table_name": "Actor"}},
            )
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"
        mock_flow.assert_not_called()

    def test_webhook_handles_malformed_payload(self, client):
        response = client.post(
            "/webhooks/nocodb",
            json={"unexpected": "format"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"


class TestWebhookDebounce:
    """Tests for debounce behavior. Uses short debounce windows to keep tests fast."""

    def test_rapid_webhooks_coalesce_into_single_run(self, client, monkeypatch):
        """Multiple webhooks within the debounce window trigger only one flow run."""
        from pipelines.worker import app as app_module
        app_module.DEBOUNCE_SECONDS = 0.3

        with patch("pipelines.worker.app.export_pmtiles_flow") as mock_flow, \
                patch("pipelines.worker.app.export_country_images"):
            mock_flow.return_value = None
            for _ in range(5):
                client.post(
                    "/webhooks/nocodb",
                    json={"type": "records.after.update", "data": {"table_name": "Country"}},
                )
            # Wait for debounce to fire
            time.sleep(0.6)
        mock_flow.assert_called_once()

    def test_webhook_after_debounce_window_triggers_again(self, client, monkeypatch):
        """A webhook arriving after the debounce fires triggers a new run."""
        from pipelines.worker import app as app_module
        app_module.DEBOUNCE_SECONDS = 0.2

        with patch("pipelines.worker.app.export_pmtiles_flow") as mock_flow, \
                patch("pipelines.worker.app.export_country_images"):
            mock_flow.return_value = None
            client.post(
                "/webhooks/nocodb",
                json={"type": "records.after.update", "data": {"table_name": "Country"}},
            )
            time.sleep(0.4)  # first debounce fires
            client.post(
                "/webhooks/nocodb",
                json={"type": "records.after.update", "data": {"table_name": "Country"}},
            )
            time.sleep(0.4)  # second debounce fires
        assert mock_flow.call_count == 2
