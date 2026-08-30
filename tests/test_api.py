import os

os.environ["COMPANION_API_TOKEN"] = "change-me-local-token"
os.environ["COMPANION_DEMO_MODE"] = "true"
os.environ["RAINFALL_PROVIDER"] = "demo"

from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)


def test_data_status():
    r = client.get("/data-status").json()
    assert "Chennai" in r["nwdp_locations"]
    assert r["inference_mode"].startswith("NWDP")


def test_flood_demo():
    client.post(
        "/demo/scenario",
        json={"flood_scenario": "high"},
        headers={"X-Api-Token": "change-me-local-token"},
    )
    f = client.get("/flood/status?location=Chennai&demo=true").json()
    assert f["demo_mode"] is True
    assert f["status"] in ("LOW", "WATCH", "HIGH")


def test_rainfall_demo():
    r = client.get("/rainfall?location=Chennai&demo=true").json()
    assert r["demo"] is True
    assert "windows" in r
