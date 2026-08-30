"""Parse real Chennai flood events from India Flood Inventory (IFI v3, Zenodo)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

IFI = ROOT / "data" / "raw" / "flood_events" / "India_Flood_Inventory_v3.csv"
OUT = ROOT / "data" / "processed" / "flood" / "chennai_flood_events.parquet"
REPORT = ROOT / "reports" / "flood_events_inventory.json"

CHENNAI_LGD = "568"


def parse_date(s: str) -> datetime | None:
    for fmt in ("%d-%m-%Y %H:%M", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(s).strip(), fmt)
        except ValueError:
            continue
    return None


def main():
    df = pd.read_csv(IFI)
    chen = df[df["District_LGD_Codes"].astype(str).str.contains(CHENNAI_LGD, na=False)].copy()
    rows = []
    for _, ev in chen.iterrows():
        start = parse_date(ev["Start Date"])
        end = parse_date(ev["End Date"])
        if not start or not end:
            continue
        d = start.date()
        end_d = end.date()
        while d <= end_d:
            rows.append(
                {
                    "date": pd.Timestamp(d),
                    "location": "Chennai",
                    "flood_event": 1,
                    "source": "IFI-Impacts v3 (IMD)",
                    "uei": ev.get("UEI"),
                    "severity": ev.get("Severity"),
                }
            )
            d += timedelta(days=1)

    daily = pd.DataFrame(rows).drop_duplicates(subset=["date", "location"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    daily.to_parquet(OUT, index=False)

    report = {
        "source": "India_Flood_Inventory_v3.csv (Zenodo 16994648)",
        "location": "Chennai",
        "lgd_code": CHENNAI_LGD,
        "event_records": int(len(chen)),
        "flood_days": int(len(daily)),
        "date_min": str(daily["date"].min()) if len(daily) else None,
        "date_max": str(daily["date"].max()) if len(daily) else None,
        "validation": "REAL historical flood events (IMD-sourced inventory). Not guaranteed future prediction.",
        "notable_events": chen[chen["Start Date"].astype(str).str.contains("2015", na=False)][
            ["Start Date", "End Date", "Districts"]
        ].head(3).to_dict(orient="records"),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
