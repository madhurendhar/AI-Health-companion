"""Open-Meteo fallback integration (network required)."""

import os

os.environ["COMPANION_API_TOKEN"] = "change-me-local-token"
os.environ["COMPANION_DEMO_MODE"] = "false"
os.environ["RAINFALL_PROVIDER"] = "open_meteo"

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.rainfall import OpenMeteoProvider

client = TestClient(app)


@pytest.mark.integration
def test_open_meteo_provider():
    hours, ts, src, meta = OpenMeteoProvider().hourly_mm("Chennai")
    assert "open_meteo" in src
    assert len(hours) >= 24
    assert meta["data_status"] == "LIVE"


@pytest.mark.integration
def test_flood_status_open_meteo_mode():
    r = client.get("/flood/status?location=Kanyakumari&demo=false")
    assert r.status_code == 200
    body = r.json()
    assert body["demo_mode"] is False
    assert body["status"] in ("LOW", "WATCH", "HIGH")
