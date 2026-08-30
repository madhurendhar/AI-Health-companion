"""Flood event inference — real IFI-trained model + NWDP river level."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

from companion_core.flood_features import FEATURE_NAMES, rainfall_windows
from companion_core.types import FloodFeatures

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "ai" / "flood" / "models" / "flood_event.joblib"
EVENTS_PATH = ROOT / "data" / "processed" / "flood" / "chennai_flood_events.parquet"
RIVER_PATH = ROOT / "data" / "processed" / "flood" / "chennai_river_level.parquet"
RIVER_REPORT = ROOT / "reports" / "river_level_quality.json"
EVENT_REPORT = ROOT / "reports" / "flood_events_inventory.json"

_model = None


def _load_model():
    global _model
    if _model is None and MODEL_PATH.exists():
        _model = joblib.load(MODEL_PATH)
    return _model


def river_thresholds() -> dict:
    if RIVER_REPORT.exists():
        return json.loads(RIVER_REPORT.read_text(encoding="utf-8")).get("level_m", {})
    if RIVER_PATH.exists():
        s = pd.read_parquet(RIVER_PATH)["level_m"]
        return {"p90": float(s.quantile(0.9)), "p95": float(s.quantile(0.95)), "p99": float(s.quantile(0.99))}
    return {}


def latest_river_level() -> dict | None:
    if not RIVER_PATH.exists():
        return None
    df = pd.read_parquet(RIVER_PATH)
    if df.empty:
        return None
    df = df.sort_values("timestamp")
    row = df.iloc[-1]
    thr = river_thresholds()
    level = float(row["level_m"])
    status = "NORMAL"
    if thr.get("p99") and level >= thr["p99"]:
        status = "CRITICAL"
    elif thr.get("p95") and level >= thr["p95"]:
        status = "HIGH"
    elif thr.get("p90") and level >= thr["p90"]:
        status = "ELEVATED"
    return {
        "level_m": level,
        "station": row.get("station"),
        "timestamp": str(row["timestamp"]),
        "status": status,
        "thresholds_m": thr,
        "source": "NWDP",
    }


def list_historical_events(location: str = "Chennai", limit: int = 50) -> list[dict]:
    if not EVENTS_PATH.exists():
        return []
    df = pd.read_parquet(EVENTS_PATH)
    df = df[df["location"] == location].sort_values("date", ascending=False).head(limit)
    return [
        {
            "date": str(r["date"].date()) if hasattr(r["date"], "date") else str(r["date"]),
            "source": r.get("source"),
            "severity": r.get("severity"),
        }
        for _, r in df.iterrows()
    ]


def event_inventory_summary() -> dict | None:
    if EVENT_REPORT.exists():
        return json.loads(EVENT_REPORT.read_text(encoding="utf-8"))
    return None


def _event_rain_profile() -> dict | None:
    """Median rainfall windows on documented IFI flood days (train overlap)."""
    p = ROOT / "data" / "processed" / "flood" / "chennai_event_dataset.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    pos = df[df["flood_event"] == 1]
    if pos.empty:
        return None
    return {
        "rain_24h_median": float(pos["rain_24h"].median()),
        "rain_72h_median": float(pos["rain_72h"].median()),
        "n_flood_days": int(len(pos)),
    }


def predict_event_risk(features: FloodFeatures) -> dict:
    """Probability of flood event next 24h from rainfall features + river context."""
    model = _load_model()
    vec = [[getattr(features, k) for k in FEATURE_NAMES]]
    river = latest_river_level()
    thr = river_thresholds()

    result = {
        "model_available": model is not None,
        "model_name": "flood_event_ifi_nwdp_v1",
        "label_source": "IFI-Impacts v3 (real Chennai flood events)",
        "target": "flood_event_next_day",
        "probability": None,
        "risk": "UNKNOWN",
        "reason": "",
        "river_level": river,
        "ifi_profile": _event_rain_profile(),
    }

    if model is None:
        result["reason"] = "Event model not trained — run ai/flood/train_flood_events.py"
        if river and river["status"] in ("HIGH", "CRITICAL"):
            result["risk"] = "WATCH"
            result["reason"] = f"River level {river['level_m']:.2f}m ({river['status']}) without ML model"
        return result

    proba = float(model.predict_proba(vec)[0][1])
    result["probability"] = round(proba, 4)

    # Combine ML + river level
    risk = "LOW"
    reasons = []
    if proba >= 0.55:
        risk = "HIGH"
        reasons.append(f"ML event probability {proba:.0%}")
    elif proba >= 0.35:
        risk = "WATCH"
        reasons.append(f"ML event probability {proba:.0%}")

    if river:
        if river["status"] == "CRITICAL":
            risk = "HIGH"
            reasons.append(f"river {river['level_m']:.2f}m >= p99")
        elif river["status"] == "HIGH" and risk == "LOW":
            risk = "WATCH"
            reasons.append(f"river {river['level_m']:.2f}m >= p95")

    if features.rain_24h >= 150 and risk == "LOW":
        risk = "WATCH"
        reasons.append(f"heavy rain_24h={features.rain_24h:.1f}mm")

    profile = result.get("ifi_profile")
    if profile and profile["rain_72h_median"] > 0:
        ratio = features.rain_72h / profile["rain_72h_median"]
        if ratio >= 0.85 and risk == "LOW":
            risk = "WATCH"
            reasons.append(f"rain_72h near IFI flood-day median ({ratio:.0%})")
        if ratio >= 1.1:
            risk = "HIGH"
            reasons.append(f"rain_72h exceeds IFI flood-day median ({ratio:.0%})")

    result["risk"] = risk
    result["reason"] = "; ".join(reasons) if reasons else "No elevated flood event signals"
    result["meaning"] = (
        "Predicts likelihood of documented Chennai flood event (IFI inventory) within 24h "
        "from NWDP rainfall patterns. Not guaranteed detection."
    )
    return result


def predict_from_hourly(hourly_mm: list[float], location: str = "Chennai") -> dict:
    f = rainfall_windows(hourly_mm)
    f.location = location
    return predict_event_risk(f)
