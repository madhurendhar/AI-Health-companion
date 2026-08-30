"""Join NWDP rainfall + river level with real IFI flood event labels (Chennai)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from companion_core.flood_features import FEATURE_NAMES, rainfall_windows

RAIN = ROOT / "data" / "processed" / "rainfall" / "chennai_rainfall.parquet"
EVENTS = ROOT / "data" / "processed" / "flood" / "chennai_flood_events.parquet"
RIVER = ROOT / "data" / "processed" / "flood" / "chennai_river_level.parquet"
OUT = ROOT / "data" / "processed" / "flood" / "chennai_event_dataset.parquet"
REPORT = ROOT / "reports" / "flood_event_dataset.json"


def daily_rainfall_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["hour"] = pd.to_datetime(df["timestamp"], utc=True).dt.floor("h")
    hourly = df.groupby("hour", as_index=False)["rainfall_mm"].sum().sort_values("hour")
    vals = hourly["rainfall_mm"].tolist()
    hours = hourly["hour"].tolist()
    rows = []
    # Map hour index -> date for end-of-day features (use last hour of each calendar day)
    by_date: dict[pd.Timestamp, int] = {}
    for i, h in enumerate(hours):
        d = pd.Timestamp(h).normalize()
        by_date[d] = i

    for date, idx in sorted(by_date.items()):
        if idx < 24:
            continue
        window = vals[max(0, idx - 71) : idx + 1]
        f = rainfall_windows(window)
        row = {k: getattr(f, k) for k in FEATURE_NAMES}
        row["date"] = date
        row["location"] = "Chennai"
        rows.append(row)
    return pd.DataFrame(rows)


def river_daily_stats(river: pd.DataFrame) -> pd.DataFrame:
    if river.empty:
        return pd.DataFrame(columns=["date", "level_max_m", "level_mean_m", "level_last_m"])
    r = river.copy()
    r["timestamp"] = pd.to_datetime(r["timestamp"], utc=True)
    r["date"] = r["timestamp"].dt.normalize()
    g = r.groupby("date")["level_m"].agg(level_max_m="max", level_mean_m="mean", level_last_m="last").reset_index()
    return g


def main():
    if not RAIN.exists():
        raise SystemExit("Run ai/flood/data/ingest_nwdp.py first")
    if not EVENTS.exists():
        raise SystemExit("Run ai/flood/data/process_flood_events.py first")

    rain_df = pd.read_parquet(RAIN)
    events = pd.read_parquet(EVENTS)
    events["date"] = pd.to_datetime(events["date"], utc=True).dt.normalize()

    feat = daily_rainfall_features(rain_df)
    merged = feat.merge(events[["date", "flood_event"]], on="date", how="left")
    merged["flood_event"] = merged["flood_event"].fillna(0).astype(int)

    # Next-day target (features through day D predict event on D+1)
    merged = merged.sort_values("date")
    merged["flood_event_next_day"] = merged["flood_event"].shift(-1).fillna(0).astype(int)

    river_stats = {}
    if RIVER.exists():
        river = pd.read_parquet(RIVER)
        rd = river_daily_stats(river)
        merged = merged.merge(rd, on="date", how="left")
        s = river["level_m"]
        river_stats = {
            "p90": float(s.quantile(0.9)),
            "p95": float(s.quantile(0.95)),
            "p99": float(s.quantile(0.99)),
        }
        merged["river_high"] = (merged["level_max_m"] >= river_stats["p95"]).astype(int)
        merged["river_high"] = merged["river_high"].fillna(0).astype(int)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(OUT, index=False)

    pos = int(merged["flood_event"].sum())
    pos_next = int(merged["flood_event_next_day"].sum())
    report = {
        "source_labels": "IFI-Impacts v3 (Chennai LGD 568)",
        "source_rainfall": "NWDP Chennai",
        "source_river": "NWDP Adyar river level" if RIVER.exists() else None,
        "rows": int(len(merged)),
        "flood_event_days": pos,
        "flood_event_next_day_positives": pos_next,
        "date_min": str(merged["date"].min()),
        "date_max": str(merged["date"].max()),
        "positive_rate": float(pos / len(merged)) if len(merged) else 0,
        "river_level_thresholds_m": river_stats,
        "target_columns": ["flood_event", "flood_event_next_day"],
        "validation": "REAL IFI flood inventory labels — not synthetic",
    }
    REPORT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
