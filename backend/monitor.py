"""Realtime NWDP monitor — logs live vs historical comparisons."""

from __future__ import annotations

import json
import time
from pathlib import Path

from companion_core.historical_monitor import compare, comparison_to_dict, load_stats
from companion_core.flood_features import rainfall_windows

LOG_DIR = Path("data/runtime/monitor")
MAX_ENTRIES = 500


def _log_path(location: str) -> Path:
    return LOG_DIR / f"{location.lower()}_monitor.jsonl"


def record(location: str, hours: list[float], ts: float, src: str) -> dict:
    stats = load_stats(location)
    if not stats:
        raise FileNotFoundError(f"No historical stats for {location}. Run build_historical_stats.py")
    f = rainfall_windows(hours)
    f.location = location
    comp = compare(f, stats)
    entry = {
        "recorded_s": time.time(),
        "nwdp_updated_s": ts,
        "source": src,
        "live": {w: getattr(f, w) for w in ("rain_1h", "rain_3h", "rain_6h", "rain_12h", "rain_24h", "rain_48h", "rain_72h", "intensity", "trend")},
        "comparison": comparison_to_dict(comp),
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with _log_path(location).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    _trim(location)
    return entry


def _trim(location: str):
    p = _log_path(location)
    if not p.exists():
        return
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    if len(lines) > MAX_ENTRIES:
        p.write_text("\n".join(lines[-MAX_ENTRIES:]) + "\n", encoding="utf-8")


def recent(location: str, n: int = 20) -> list[dict]:
    p = _log_path(location)
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(x) for x in lines[-n:]]


def trend(location: str, n: int = 10) -> dict:
    entries = recent(location, n)
    if len(entries) < 2:
        return {"available": False}
    scores = [e["comparison"]["risk_score"] for e in entries]
    statuses = [e["comparison"]["status"] for e in entries]
    return {
        "available": True,
        "n": len(entries),
        "risk_trend": round(scores[-1] - scores[0], 4),
        "latest_status": statuses[-1],
        "escalating": scores[-1] > scores[0] + 0.1,
        "latest_score": scores[-1],
    }
