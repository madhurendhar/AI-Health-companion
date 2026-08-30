"""Live NWDP integration (network required)."""

import os

os.environ["COMPANION_DEMO_MODE"] = "false"
os.environ["RAINFALL_PROVIDER"] = "nwdp"

import pytest

from backend.rainfall import CompositeRainfallProvider


@pytest.mark.integration
def test_nwdp_chennai_live():
    p = CompositeRainfallProvider()
    hours, ts, src, meta = p.hourly_mm("Chennai")
    assert src in ("NWDP", "open_meteo_fallback")
    assert len(hours) >= 1
    assert ts > 0


@pytest.mark.integration
def test_api_flood_nwdp_mode():
    from fastapi.testclient import TestClient
    from backend.app import app

    client = TestClient(app)
    r = client.get("/flood/status?location=Chennai&demo=false")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("LOW", "WATCH", "HIGH")
    assert body["demo_mode"] is False
