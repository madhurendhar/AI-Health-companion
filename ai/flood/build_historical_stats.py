"""Build historical percentile stats from real NWDP ingested parquet."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from companion_core.flood_features import FEATURE_NAMES, rainfall_windows

DATA = ROOT / "data" / "processed" / "rainfall"
WINDOWS = ["rain_1h", "rain_3h", "rain_6h", "rain_12h", "rain_24h", "rain_48h", "rain_72h"]


def rolling_features(hourly_mm: list[float]) -> pd.DataFrame:
    rows = []
    for i in range(len(hourly_mm)):
        window = hourly_mm[max(0, i - 71) : i + 1]
        f = rainfall_windows(window)
        rows.append({w: getattr(f, w) for w in WINDOWS})
    return pd.DataFrame(rows)


def build_stats(location: str) -> dict:
    p = DATA / f"{location.lower()}_rainfall.parquet"
    if not p.exists():
        raise FileNotFoundError(f"Run ingest first: {p}")
    df = pd.read_parquet(p)
    df["hour"] = df["timestamp"].dt.floor("h")
    hourly = df.groupby("hour", as_index=False)["rainfall_mm"].sum().sort_values("hour")
    feats = rolling_features(hourly["rainfall_mm"].tolist())

    out: dict = {
        "location": location,
        "source": "NWDP",
        "data_kind": "REAL NWDP HISTORICAL",
        "n_hours": int(len(hourly)),
        "date_min": str(hourly["hour"].min()),
        "date_max": str(hourly["hour"].max()),
        "stations": sorted(df["station"].dropna().unique().tolist())[:10],
        "method": "rolling_window_percentiles",
        "validation": "Historical rainfall anomaly baseline — not flood-event labels",
    }
    for w in WINDOWS:
        s = feats[w]
        for p in (50, 90, 95, 99):
            out[f"{w}_p{p}"] = float(s.quantile(p / 100))
        out[f"{w}_max"] = float(s.max())
        out[f"{w}_mean"] = float(s.mean())

    out_path = DATA / f"{location.lower()}_historical_stats.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    (ROOT / "reports" / f"{location.lower()}_historical_stats.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8"
    )
    print(f"wrote {out_path}")
    return out


def main():
    for loc in ("Chennai",):
        build_stats(loc)


if __name__ == "__main__":
    main()
