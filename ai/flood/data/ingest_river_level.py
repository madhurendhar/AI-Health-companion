"""Ingest real NWDP river water level for Chennai (Adyar)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from backend.services.nwdp.client import NwdpClient
from backend.services.nwdp.config import RESOURCES
from backend.services.nwdp.parser import parse_record

OUT = ROOT / "data" / "processed" / "flood" / "chennai_river_level.parquet"
REPORT = ROOT / "reports" / "river_level_quality.json"


def main():
    res = RESOURCES["Chennai"]["river_level"]
    client = NwdpClient()
    raw = client.fetch_all(res, page_size=500)
    rows = []
    invalid = 0
    for rec in raw:
        parsed = parse_record(rec, res)
        if parsed:
            rows.append(
                {
                    "timestamp": parsed.timestamp,
                    "station": parsed.station,
                    "river": rec.get("River", ""),
                    "level_m": parsed.rainfall_mm,  # field reused as level in parser
                    "latitude": parsed.latitude,
                    "longitude": parsed.longitude,
                    "resource_id": res.resource_id,
                    "source": "NWDP",
                }
            )
        else:
            invalid += 1

    df = pd.DataFrame(rows)
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp", "station"], keep="last")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)

    s = df["level_m"]
    report = {
        "source": "NWDP river_level resource",
        "resource_id": res.resource_id,
        "station": df["station"].iloc[0] if len(df) else None,
        "river": df["river"].iloc[0] if len(df) else None,
        "row_count": int(len(df)),
        "invalid": invalid,
        "date_min": str(df["timestamp"].min()) if len(df) else None,
        "date_max": str(df["timestamp"].max()) if len(df) else None,
        "level_m": {
            "min": float(s.min()) if len(s) else None,
            "max": float(s.max()) if len(s) else None,
            "p90": float(s.quantile(0.9)) if len(s) else None,
            "p95": float(s.quantile(0.95)) if len(s) else None,
            "p99": float(s.quantile(0.99)) if len(s) else None,
        },
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {OUT} rows={len(df)}")


if __name__ == "__main__":
    main()
