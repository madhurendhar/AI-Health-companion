"""Tests for NWDP historical comparison (uses real stats file when present)."""

import json
from pathlib import Path

from companion_core.flood_features import rainfall_windows
from companion_core.historical_monitor import compare, load_stats

STATS = Path("data/processed/rainfall/chennai_historical_stats.json")


def test_compare_low_vs_real_baseline():
    if not STATS.exists():
        return  # skip if stats not built
    stats = load_stats("Chennai")
    f = rainfall_windows([0.0] * 72)
    f.location = "Chennai"
    c = compare(f, stats)
    assert c.status == "LOW"
    assert c.data_source == "NWDP"


def test_compare_high_rain_vs_real_baseline():
    if not STATS.exists():
        return
    stats = load_stats("Chennai")
    # exceed historical p99 for 24h (~734mm from real NWDP ingest)
    heavy = [0.0] * 48 + [15.0] * 24
    f = rainfall_windows(heavy)
    f.location = "Chennai"
    c = compare(f, stats)
    assert c.status in ("WATCH", "HIGH")
    assert c.risk_score >= 0.4
    assert any(a.level != "normal" for a in c.anomalies)


def test_stats_file_is_real_nwdp():
    if not STATS.exists():
        return
    stats = json.loads(STATS.read_text())
    assert stats.get("data_kind") == "REAL NWDP HISTORICAL"
    assert stats.get("n_hours", 0) > 1000
