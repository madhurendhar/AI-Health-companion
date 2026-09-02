"""Environmental disaster risk — heat, pollution, rainfall (screening only)."""

from __future__ import annotations

from pathlib import Path
import json

from ai.companion.features import ENV_FEATURE_NAMES, heat_index_approx
from companion_core.compact_tree import CompactTree
from companion_core.flood_features import FloodFeatures

LABELS = ["LOW", "WATCH", "HIGH"]
_tree: CompactTree | None = None


def _load_tree() -> CompactTree | None:
    global _tree
    if _tree is not None:
        return _tree
    p = Path("ai/companion/models/env_disaster_tree.json")
    if p.exists():
        _tree = CompactTree.load(p)
    return _tree


def env_vector(
    ambient_temp: float,
    humidity: float,
    mq135_relative: float,
    flood: FloodFeatures | None = None,
) -> list[float]:
    f = flood or FloodFeatures()
    hi = heat_index_approx(ambient_temp, humidity)
    return [
        ambient_temp,
        humidity,
        hi,
        mq135_relative,
        f.rain_1h,
        f.rain_24h,
        f.rain_72h,
        f.intensity,
        f.trend,
    ]


def heuristic_env_score(ambient_temp: float, humidity: float, mq135_relative: float, flood: FloodFeatures | None) -> tuple[float, str]:
    f = flood or FloodFeatures()
    hi = heat_index_approx(ambient_temp, humidity)
    score = 0.0
    score += min(0.35, max(0, hi - 32) / 15)
    score += min(0.25, max(0, mq135_relative - 1.2) / 2)
    score += min(0.30, f.rain_24h / 120)
    score += min(0.10, f.intensity / 30)
    score = max(0.0, min(1.0, score))
    return score, f"heat={hi:.1f} mq={mq135_relative:.2f} rain24={f.rain_24h:.1f}"


def classify(score: float) -> str:
    if score >= 0.70:
        return "HIGH"
    if score >= 0.40:
        return "WATCH"
    return "LOW"


def predict(
    ambient_temp: float,
    humidity: float,
    mq135_relative: float,
    flood: FloodFeatures | None = None,
) -> dict:
    vec = env_vector(ambient_temp, humidity, mq135_relative, flood)
    h_score, reason = heuristic_env_score(ambient_temp, humidity, mq135_relative, flood)
    tree = _load_tree()
    t_score = tree.predict_score(vec) if tree else None
    if t_score is not None:
        score = 0.5 * h_score + 0.5 * t_score
    else:
        score = h_score
    status = classify(score)
    return {
        "status": status,
        "risk_score": round(score, 4),
        "heat_index": round(heat_index_approx(ambient_temp, humidity), 2),
        "reason": reason,
        "model_used": tree is not None,
        "meaning": "Environmental early-warning screening (heat/pollution/flood rainfall). Not guaranteed detection.",
    }
