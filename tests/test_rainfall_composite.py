"""Tests for composite rainfall routing (no live API)."""

import os

os.environ["RAINFALL_PROVIDER"] = "nwdp"
os.environ["COMPANION_DEMO_MODE"] = "false"

from backend.rainfall import CompositeRainfallProvider, DemoRainfallProvider


def test_kanyakumari_routes_open_meteo(monkeypatch):
    calls = []

    def fake_meteo(self, location):
        calls.append(location)
        return [0.0] * 72, 1.0, "open_meteo_fallback", {"data_status": "LIVE"}

    monkeypatch.setattr(
        "backend.rainfall.OpenMeteoProvider.hourly_mm",
        fake_meteo,
    )
    p = CompositeRainfallProvider()
    hours, _, src, meta = p.hourly_mm("Kanyakumari")
    assert calls == ["Kanyakumari"]
    assert src == "open_meteo_fallback"
    assert len(hours) == 72


def test_demo_provider_labelled():
    hours, _, src, meta = DemoRainfallProvider("high").hourly_mm("Chennai")
    assert "DEMO" in src
    assert meta["data_status"] == "DEMO"
    assert sum(hours) > 0
