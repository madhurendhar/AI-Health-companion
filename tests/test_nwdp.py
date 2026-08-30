"""NWDP client/parser tests using saved samples (no live API)."""

import json
from pathlib import Path

from backend.services.nwdp.client import NwdpClient
from backend.services.nwdp.config import RESOURCES
from backend.services.nwdp.parser import hourly_mm_series, parse_record, parse_timestamp

SAMPLE = Path("data/raw/nwdp_samples/chennai_1.json")


def test_parse_timestamp():
    dt = parse_timestamp("09-08-2021 17:45")
    assert dt is not None
    assert dt.year == 2021 and dt.month == 8 and dt.day == 9


def test_parse_chennai_rainfall_record():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    res = RESOURCES["Chennai"]["rainfall_historical"]
    rec = data["records"][0]
    parsed = parse_record(rec, res)
    assert parsed is not None
    assert parsed.rainfall_mm == 1.5
    assert parsed.station.startswith("Chennai")


def test_hourly_series_from_samples():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    res = RESOURCES["Chennai"]["rainfall_historical"]
    parsed = [p for r in data["records"] if (p := parse_record(r, res))]
    hours = hourly_mm_series(parsed, hours=24)
    assert len(hours) >= 1
    assert all(h >= 0 for h in hours)


def test_client_search_mock(monkeypatch):
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))

    def fake_search(self, res, **kw):
        return {"records": sample["records"], "total": len(sample["records"])}

    monkeypatch.setattr(NwdpClient, "search", fake_search)
    client = NwdpClient()
    res = RESOURCES["Chennai"]["rainfall_historical"]
    out = client.search(res, limit=5)
    assert len(out["records"]) == 5
