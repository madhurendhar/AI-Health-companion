"""Flood early warning — real NWDP live data vs historical baseline (no synthetic inference)."""

from __future__ import annotations

import json
import time
from pathlib import Path

from companion_core.config import FLOOD
from companion_core.flood_events import predict_from_hourly
from companion_core.flood_risk import FloodStateMachine, make_flood_result, poll_interval_s
from companion_core.historical_monitor import compare, comparison_to_dict, load_stats
from companion_core.types import NetworkState
from backend.monitor import record, trend
from backend.rainfall import CachedRainfall, RainfallProvider, build_provider, features_for

BASELINE_PATH = Path("data/processed/rainfall/chennai_baseline.json")


def load_baseline(location: str) -> dict | None:
    stats = load_stats(location)
    if stats:
        return stats
    p = Path(f"data/processed/rainfall/{location.lower()}_baseline.json")
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return None


class FloodEngine:
    def __init__(self, provider: RainfallProvider | None = None, **_ignored):
        self._provider = provider
        self._sm = FloodStateMachine()
        self._last: dict[str, dict] = {}

    def provider(self, demo: bool = False, scenario: str = "normal") -> CachedRainfall:
        inner = self._provider or build_provider(demo=demo, scenario=scenario)
        ttl = 30 if demo else int(__import__("os").getenv("NWDP_CACHE_TTL_S", "600"))
        return CachedRainfall(inner, ttl_s=ttl)

    def evaluate(self, location: str, demo: bool = False, scenario: str = "normal") -> dict:
        now = time.time()
        network = NetworkState.ONLINE
        meta: dict = {}
        try:
            hours, ts, src, meta = self.provider(demo, scenario).hourly_mm(location)
            demo_flag = src.startswith("DEMO") or "SIMULATED" in src
        except Exception as exc:
            stale_hit = self._last.get(location)
            if stale_hit:
                hours, ts, src = stale_hit["hours"], stale_hit["ts"], stale_hit["src"]
                meta = {"data_status": "STALE_DATA", "stale": True, "error": str(exc)}
                demo_flag = False
                network = NetworkState.STALE_DATA
            else:
                raise

        f = features_for(hours, location)
        stats = load_stats(location)

        if demo_flag or not stats:
            # Demo path only when explicitly requested or no historical stats yet
            from companion_core.flood_risk import heuristic_flood_score

            score, reason = heuristic_flood_score(f)
            st = self._sm.update(score, now)
            comp_dict = None
            monitor_entry = None
        else:
            comp = compare(f, stats)
            score = comp.risk_score
            reason = comp.reason
            st = self._sm.update(score, now)
            comp_dict = comparison_to_dict(comp)
            try:
                monitor_entry = record(location, hours, ts, src)
            except Exception:
                monitor_entry = None

        data_status = meta.get("data_status", "LIVE")
        if meta.get("stale"):
            network = NetworkState.STALE_DATA

        result = make_flood_result(
            f, score, st, now, ts, network, demo_flag, reason, used_tree=False
        )
        if not demo_flag and stats:
            result.model_name = "nwdp_historical_monitor_v1"
            result.model_version = "1.0.0"

        self._last[location] = {"hours": hours, "ts": ts, "src": src}
        tr = trend(location)

        event_risk = predict_from_hourly(hours, location) if not demo_flag else {
            "model_available": False,
            "risk": "UNKNOWN",
            "reason": "demo mode — event model uses real IFI labels only",
            "demo_mode": True,
        }

        return {
            "location": location,
            "risk": result.status.value,
            "risk_score": result.risk_score,
            "status": result.status.value,
            "rainfall": {
                "1h": f.rain_1h,
                "3h": f.rain_3h,
                "6h": f.rain_6h,
                "12h": f.rain_12h,
                "24h": f.rain_24h,
                "48h": f.rain_48h,
                "72h": f.rain_72h,
            },
            "windows": f.__dict__,
            "source": src,
            "updated_at": ts,
            "updated_s": ts,
            "data_status": data_status,
            "stale": result.stale or meta.get("stale", False),
            "network": result.network.value,
            "poll_interval_s": poll_interval_s(result.status),
            "model_name": result.model_name,
            "model_version": result.model_version,
            "demo_mode": demo_flag,
            "demo_banner": "DEMO MODE / SIMULATED DATA" if demo_flag else None,
            "reason": result.reason,
            "meaning": "NWDP live rainfall vs historical baseline early-warning. Not guaranteed flood detection.",
            "historical_comparison": comp_dict,
            "historical_stats_available": stats is not None,
            "monitor_trend": tr,
            "inference": "REAL NWDP + historical percentile" if not demo_flag else "DEMO/SIMULATED",
            "flood_event": event_risk,
        }
