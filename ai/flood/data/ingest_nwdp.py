"""Ingest NWDP historical rainfall into data/processed/rainfall/."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import pandas as pd

from backend.services.nwdp.client import NwdpClient
from backend.services.nwdp.config import RESOURCES, rainfall_resource
from backend.services.nwdp.parser import parse_record

OUT = ROOT / "data" / "processed" / "rainfall"
REPORT = ROOT / "reports" / "flood_data_quality.json"


def ingest_location(location: str, *, max_records: int | None = None, merge_all: bool = True) -> pd.DataFrame:
    client = NwdpClient()
    loc_res = RESOURCES.get(location, {})
    keys = []
    if merge_all and location == "Chennai":
        keys = [k for k in ("rainfall_historical", "rainfall_current") if k in loc_res]
    else:
        res = rainfall_resource(location, prefer_current=False) or rainfall_resource(location, prefer_current=True)
        if res is None:
            raise ValueError(f"No rainfall resource for {location}")
        keys = []

    rows = []
    invalid = 0
    if keys:
        for key in keys:
            res = loc_res[key]
            raw = client.fetch_all(res, page_size=500, max_records=max_records)
            for rec in raw:
                parsed = parse_record(rec, res)
                if parsed:
                    rows.append(parsed.to_dict())
                else:
                    invalid += 1
    else:
        res = rainfall_resource(location, prefer_current=False) or rainfall_resource(location, prefer_current=True)
        raw = client.fetch_all(res, page_size=500, max_records=max_records)
        for rec in raw:
            parsed = parse_record(rec, res)
            if parsed:
                rows.append(parsed.to_dict())
            else:
                invalid += 1

    df = pd.DataFrame(rows)
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.sort_values("timestamp")
        df = df.drop_duplicates(subset=["timestamp", "station", "resource_id"], keep="last")

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{location.lower()}_rainfall.parquet"
    df.to_parquet(path, index=False)
    print(f"wrote {path} rows={len(df)} invalid={invalid}")
    return df


def quality_report(df: pd.DataFrame, location: str) -> dict:
    if df.empty:
        return {"location": location, "row_count": 0, "valid_count": 0, "note": "empty dataset"}

    rain = df["rainfall_mm"]
    report = {
        "location": location,
        "row_count": int(len(df)),
        "valid_count": int(rain.notna().sum()),
        "invalid_count": int(rain.isna().sum()),
        "duplicates_removed": True,
        "date_min": str(df["timestamp"].min()),
        "date_max": str(df["timestamp"].max()),
        "stations": sorted(df["station"].dropna().unique().tolist()),
        "districts": sorted(df["district"].dropna().unique().tolist()),
        "rainfall_mm": {
            "min": float(rain.min()),
            "max": float(rain.max()),
            "mean": float(rain.mean()),
            "p50": float(rain.quantile(0.5)),
            "p90": float(rain.quantile(0.9)),
            "p95": float(rain.quantile(0.95)),
            "p99": float(rain.quantile(0.99)),
        },
        "negative_rainfall": int((rain < 0).sum()),
        "missing_station": int(df["station"].isna().sum()),
        "source": "NWDP",
        "flood_event_labels": "PENDING EXTERNAL DATA",
        "note": "Rainfall ingestion only. Supervised flood labels not available in NWDP resources.",
    }
    return report


def main():
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    all_reports = {}
    for loc in ("Chennai",):
        df = ingest_location(loc)
        all_reports[loc] = quality_report(df, loc)
    REPORT.write_text(json.dumps(all_reports, indent=2), encoding="utf-8")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
