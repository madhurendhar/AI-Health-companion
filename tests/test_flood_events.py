"""Tests for real IFI flood event pipeline."""

from pathlib import Path

import pandas as pd
import pytest

from companion_core.flood_events import (
    event_inventory_summary,
    list_historical_events,
    predict_from_hourly,
    river_thresholds,
)
from companion_core.flood_features import rainfall_windows

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "data" / "processed" / "flood" / "chennai_flood_events.parquet"
DATASET = ROOT / "data" / "processed" / "flood" / "chennai_event_dataset.parquet"
RIVER = ROOT / "data" / "processed" / "flood" / "chennai_river_level.parquet"


@pytest.mark.skipif(not EVENTS.exists(), reason="run process_flood_events.py")
def test_ifi_events_loaded():
    df = pd.read_parquet(EVENTS)
    assert len(df) > 100
    assert (df["flood_event"] == 1).all()
    assert df["location"].iloc[0] == "Chennai"


@pytest.mark.skipif(not DATASET.exists(), reason="run build_event_dataset.py")
def test_event_dataset_has_positives():
    df = pd.read_parquet(DATASET)
    assert df["flood_event"].sum() > 0
    assert "flood_event_next_day" in df.columns


@pytest.mark.skipif(not RIVER.exists(), reason="run ingest_river_level.py")
def test_river_level_parquet():
    df = pd.read_parquet(RIVER)
    assert len(df) > 1000
    assert df["level_m"].notna().all()


def test_predict_event_risk_heavy_rain():
    hours = [15.0] * 72
    out = predict_from_hourly(hours)
    assert out["risk"] in ("LOW", "WATCH", "HIGH", "UNKNOWN")
    assert "reason" in out


def test_list_historical_events():
    events = list_historical_events(limit=5)
    if EVENTS.exists():
        assert len(events) > 0
        assert "date" in events[0]


def test_inventory_summary():
    s = event_inventory_summary()
    if EVENTS.exists():
        assert s is not None
        assert s["event_records"] >= 50


def test_rainfall_windows_for_event_features():
    f = rainfall_windows([5.0] * 48 + [20.0] * 24)
    assert f.rain_24h == 20 * 24
    assert f.rain_72h > 0
