"""Historical NWDP statistics + live anomaly comparison for early warning."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from companion_core.flood_features import FEATURE_NAMES, rainfall_windows
from companion_core.types import FloodFeatures

WINDOWS = ["rain_1h", "rain_3h", "rain_6h", "rain_12h", "rain_24h", "rain_48h", "rain_72h"]
PERCENTILES = [50, 90, 95, 99]
WEIGHTS = {
    "rain_1h": 0.15,
    "rain_3h": 0.10,
    "rain_6h": 0.10,
    "rain_12h": 0.10,
    "rain_24h": 0.25,
    "rain_48h": 0.15,
    "rain_72h": 0.15,
}


@dataclass
class AnomalyDetail:
    window: str
    current_mm: float
    p90: float
    p95: float
    p99: float
    ratio_p90: float
    level: str  # normal, elevated, high, extreme


@dataclass
class HistoricalComparison:
    location: str
    risk_score: float
    status: str  # LOW, WATCH, HIGH
    anomalies: list[AnomalyDetail] = field(default_factory=list)
    reason: str = ""
    method: str = "nwdp_historical_percentile"
    data_source: str = "NWDP"


def stats_path(location: str) -> Path:
    return Path(f"data/processed/rainfall/{location.lower()}_historical_stats.json")


def load_stats(location: str) -> dict | None:
    p = stats_path(location)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _level_for(val: float, p90: float, p95: float, p99: float) -> str:
    if val >= p99:
        return "extreme"
    if val >= p95:
        return "high"
    if val >= p90:
        return "elevated"
    return "normal"


def _score_from_level(level: str) -> float:
    return {"normal": 0.1, "elevated": 0.45, "high": 0.72, "extreme": 0.92}.get(level, 0.1)


def compare(features: FloodFeatures, stats: dict) -> HistoricalComparison:
    loc = features.location or stats.get("location", "")
    anomalies: list[AnomalyDetail] = []
    weighted = 0.0
    wsum = 0.0
    flags: list[str] = []

    for w in WINDOWS:
        cur = float(getattr(features, w, 0.0))
        p90 = float(stats.get(f"{w}_p90", 0))
        p95 = float(stats.get(f"{w}_p95", 0))
        p99 = float(stats.get(f"{w}_p99", 0))
        if p90 <= 0:
            continue
        level = _level_for(cur, p90, p95, p99)
        ratio = cur / p90 if p90 else 0.0
        anomalies.append(
            AnomalyDetail(w, cur, p90, p95, p99, round(ratio, 3), level)
        )
        wt = WEIGHTS.get(w, 0.1)
        weighted += _score_from_level(level) * wt
        wsum += wt
        if level != "normal":
            flags.append(f"{w}={cur:.1f}mm ({level}, p90={p90:.1f})")

    score = weighted / wsum if wsum else 0.0
    levels = [a.level for a in anomalies]
    if "extreme" in levels:
        score = max(score, 0.85)
    elif sum(1 for l in levels if l == "high") >= 2:
        score = max(score, 0.72)
    elif "high" in levels:
        score = max(score, 0.55)
    elif "elevated" in levels:
        score = max(score, 0.42)
    # intensity boost if 1h rainfall accelerating
    if features.intensity > stats.get("rain_1h_p95", 1e9):
        score = min(1.0, score + 0.08)
        flags.append(f"intensity={features.intensity:.1f}mm/h")

    if score >= 0.70:
        status = "HIGH"
    elif score >= 0.40:
        status = "WATCH"
    else:
        status = "LOW"

    reason = "; ".join(flags) if flags else f"within historical norms (24h={features.rain_24h:.1f}mm)"
    return HistoricalComparison(
        location=loc,
        risk_score=round(score, 4),
        status=status,
        anomalies=anomalies,
        reason=reason,
        data_source=stats.get("source", "NWDP"),
    )


def comparison_to_dict(c: HistoricalComparison) -> dict:
    return {
        "location": c.location,
        "risk_score": c.risk_score,
        "status": c.status,
        "method": c.method,
        "data_source": c.data_source,
        "reason": c.reason,
        "anomalies": [
            {
                "window": a.window,
                "current_mm": a.current_mm,
                "historical_p90": a.p90,
                "historical_p95": a.p95,
                "historical_p99": a.p99,
                "ratio_vs_p90": a.ratio_p90,
                "level": a.level,
            }
            for a in c.anomalies
        ],
    }
