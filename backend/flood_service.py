"""Flood risk orchestration — NWDP rainfall + baseline + optional ML tree."""

from __future__ import annotations

import json
import time
from pathlib import Path

from companion_core.compact_tree import CompactTree
from companion_core.config import FLOOD
from companion_core.flood_features import feature_vector
from companion_core.flood_risk import FloodStateMachine, heuristic_flood_score, make_flood_result, poll_interval_s
from companion_core.types import FloodStatus, NetworkState
from backend.rainfall import CachedRainfall, RainfallProvider, build_provider, features_for

BASELINE_PATH = Path("data/processed/rainfall/chennai_baseline.json")


def load_baseline(location: str) -> dict | None:
    p = Path(f"data/processed/rainfall/{location.lower()}_baseline.json")
    if not p.exists() and location == "Chennai" and BASELINE_PATH.exists():
        p = BASELINE_PATH
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def baseline_score(f, baseline: dict) -> tuple[float, str]:
    p90 = baseline.get("rain_24h_p90") or 30.0
    p95 = baseline.get("rain_24h_p95") or 60.0
    p99 = baseline.get("rain_24h_p99") or 100.0
    s24 = f.rain_24h
    if s24 >= p99:
        score = 0.85 + min(0.15, (s24 - p99) / max(p99, 1) * 0.15)
    elif s24 >= p95:
        score = 0.65 + (s24 - p95) / max(p99 - p95, 1) * 0.2
    elif s24 >= p90:
        score = 0.40 + (s24 - p90) / max(p95 - p90, 1) * 0.25
    else:
        score = min(0.35, s24 / max(p90, 1) * 0.35)
    score = max(0.0, min(1.0, score))
    return score, f"baseline rain24={s24:.1f} p90={p90:.1f} p95={p95:.1f} p99={p99:.1f}"


class FloodEngine:
    def __init__(self, provider: RainfallProvider | None = None, flood_tree: CompactTree | None = None, sklearn_model=None):
        self._provider = provider
        self._sm = FloodStateMachine()
        self._tree = flood_tree
        self._sklearn = sklearn_model
        self._last: dict[str, dict] = {}

    def provider(self, demo: bool = False, scenario: str = "normal") -> CachedRainfall:
        inner = self._provider or build_provider(demo=demo, scenario=scenario)
        return CachedRainfall(inner, ttl_s=60)

    def evaluate(self, location: str, demo: bool = False, scenario: str = "normal") -> dict:
        now = time.time()
        network = NetworkState.ONLINE
        meta: dict = {}
        try:
            hours, ts, src, meta = self.provider(demo, scenario).hourly_mm(location)
            demo_flag = src.startswith("DEMO")
        except Exception as exc:
            stale_hit = self._last.get(location)
            if stale_hit:
                hours, ts, src = stale_hit["hours"], stale_hit["ts"], stale_hit["src"]
                meta = {"data_status": "STALE_DATA", "stale": True, "error": str(exc)}
                demo_flag = src.startswith("DEMO")
                network = NetworkState.STALE_DATA
            else:
                raise

        f = features_for(hours, location)
        h_score, h_reason = heuristic_flood_score(f)
        bl = load_baseline(location)
        b_score, b_reason = (None, "")
        if bl:
            b_score, b_reason = baseline_score(f, bl)

        scores = [h_score]
        reasons = [h_reason]
        if b_score is not None:
            scores.append(b_score)
            reasons.append(b_reason)

        tree_score = None
        ml_used = False
        if self._sklearn:
            tree_score = self._sklearn.predict_score(feature_vector(f))
            ml_used = True
        elif self._tree:
            tree_score = self._tree.predict_score(feature_vector(f))
            ml_used = True
        if tree_score is not None:
            scores.append(tree_score)

        score = sum(scores) / len(scores)
        reason = "; ".join(reasons)
        st = self._sm.update(score, now)

        data_status = meta.get("data_status", "LIVE")
        if meta.get("stale"):
            network = NetworkState.STALE_DATA
        if data_status == "DEMO":
            network = NetworkState.ONLINE

        result = make_flood_result(
            f, score, st, now, ts, network, demo_flag,
            reason, ml_used,
        )
        self._last[location] = {"hours": hours, "ts": ts, "src": src}

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
            "demo_mode": result.demo_mode,
            "demo_banner": "DEMO MODE / SIMULATED DATA" if result.demo_mode else None,
            "reason": result.reason,
            "meaning": "LOCATION-SPECIFIC FLOOD EARLY-RISK PREDICTION. Not guaranteed flood detection.",
            "baseline_used": bl is not None,
            "ml_tree_used": ml_used,
            "ml_sklearn_used": self._sklearn is not None,
            "supervised_labels": "PENDING EXTERNAL DATA",
        }
