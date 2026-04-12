"""Tests for the pipeline worker webhook app."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from pipelines.worker.app import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestWebhookEndpoint:
    def test_webhook_triggers_export_pmtiles(self, client):
        """A POST to /webhooks/nocodb with table=Country triggers the export flow."""
        with patch("pipelines.worker.app.export_pmtiles_flow") as mock_flow:
            mock_flow.return_value = None
            response = client.post(
                "/webhooks/nocodb",
                json={"type": "records.after.update", "data": {"table_name": "Country"}},
            )
        assert response.status_code == 202
        assert response.json()["status"] == "accepted"
        mock_flow.assert_called_once()

    def test_webhook_triggers_on_distribution_zone(self, client):
        with patch("pipelines.worker.app.export_pmtiles_flow") as mock_flow:
            mock_flow.return_value = None
            response = client.post(
                "/webhooks/nocodb",
                json={"type": "records.after.update", "data": {"table_name": "DistributionZone"}},
            )
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
