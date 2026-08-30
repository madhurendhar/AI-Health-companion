"""Historical rainfall baseline — percentile anomaly risk (not flood-event labels)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from companion_core.types import FloodFeatures

DATA = ROOT / "data" / "processed" / "rainfall"
REPORT = ROOT / "reports" / "flood_baseline.json"


def load_hourly(location: str) -> pd.DataFrame:
    p = DATA / f"{location.lower()}_rainfall.parquet"
    if not p.exists():
        raise FileNotFoundError(f"Run ingest_nwdp first: {p}")
    df = pd.read_parquet(p)
    df["hour"] = df["timestamp"].dt.floor("h")
    hourly = df.groupby("hour", as_index=False)["rainfall_mm"].sum()
    return hourly.sort_values("hour")


def compute_baseline(hourly: pd.DataFrame) -> dict:
    r24 = []
    vals = hourly["rainfall_mm"].tolist()
    for i in range(len(vals)):
        r24.append(sum(vals[max(0, i - 23) : i + 1]))
    s = pd.Series(r24)
    return {
        "rain_24h_p50": float(s.quantile(0.5)),
        "rain_24h_p90": float(s.quantile(0.9)),
        "rain_24h_p95": float(s.quantile(0.95)),
        "rain_24h_p99": float(s.quantile(0.99)),
        "n_hours": len(vals),
    }


def baseline_score(f: FloodFeatures, baseline: dict) -> tuple[float, str]:
    p90 = baseline.get("rain_24h_p90") or 30.0
    p95 = baseline.get("rain_24h_p95") or 60.0
    p99 = baseline.get("rain_24h_p99") or 100.0
    s24 = f.rain_24h
    score = 0.0
    if s24 >= p99:
        score = 0.85 + min(0.15, (s24 - p99) / max(p99, 1) * 0.15)
    elif s24 >= p95:
        score = 0.65 + (s24 - p95) / max(p99 - p95, 1) * 0.2
    elif s24 >= p90:
        score = 0.40 + (s24 - p90) / max(p95 - p90, 1) * 0.25
    else:
        score = min(0.35, s24 / max(p90, 1) * 0.35)
    score = max(0.0, min(1.0, score))
    reason = f"baseline anomaly rain24={s24:.1f} p90={p90:.1f} p95={p95:.1f} p99={p99:.1f}"
    return score, reason


def main():
    hourly = load_hourly("Chennai")
    bl = compute_baseline(hourly)
    bl["location"] = "Chennai"
    bl["method"] = "historical_rainfall_percentile"
    bl["validation"] = "NOT flood-event validation — rainfall anomaly baseline only"
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(bl, indent=2), encoding="utf-8")
    out_path = DATA / "chennai_baseline.json"
    out_path.write_text(json.dumps(bl, indent=2), encoding="utf-8")
    print(json.dumps(bl, indent=2))


if __name__ == "__main__":
    main()
