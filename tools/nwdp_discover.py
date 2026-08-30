"""Inspect NWDP resource IDs; save samples + inventory JSON. Run once, not in CI."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import httpx

BASE = "https://www.nwdp.nwic.gov.in/api/3/action/datastore_search"

RESOURCES = [
    {
        "resource_id": "51b0e617-02dc-4dd8-a6ce-fdce6c1731b9",
        "district": "Chennai",
        "state": "Tamil Nadu",
        "agency": "Tamil Nadu SW GW",
        "label": "chennai_1",
    },
    {
        "resource_id": "cd797dd2-dff1-45ee-87df-eaa554bbeb5f",
        "district": "Kanyakumari",
        "state": "Tamil Nadu",
        "agency": "Tamil Nadu SW GW",
        "label": "kanyakumari_1",
    },
    {
        "resource_id": "387aa243-ae4d-4aa3-932b-bbc5b09e148e",
        "district": "Kanyakumari",
        "state": "Tamil Nadu",
        "agency": "Tamil Nadu SW GW",
        "label": "kanyakumari_2",
    },
    {
        "resource_id": "21b02519-f3d3-409d-a091-94332d848a8e",
        "district": "Chennai",
        "state": "Tamil Nadu",
        "agency": "Tamil Nadu SW GW",
        "label": "chennai_2",
    },
    {
        "resource_id": "77459b05-fcbd-4b8c-97e1-e2a33d359ce3",
        "district": "Chennai",
        "state": "Tamil Nadu",
        "agency": "Tamil Nadu SW GW",
        "label": "chennai_prev",
    },
]

SAMPLE_DIR = ROOT / "data" / "raw" / "nwdp_samples"
REPORT = ROOT / "reports" / "nwdp_inventory.json"


def fetch(resource_id: str, filters: dict, limit: int = 100, offset: int = 0) -> dict:
    params = {
        "resource_id": resource_id,
        "filters": json.dumps(filters),
        "limit": limit,
        "offset": offset,
    }
    with httpx.Client(timeout=30.0) as c:
        r = c.get(BASE, params=params)
        r.raise_for_status()
        return r.json()


def analyze(meta: dict, records: list[dict]) -> dict:
    fields = list(meta.get("fields", []))
    field_ids = [f.get("id") for f in fields]
    ts_candidates = [k for k in field_ids if k and any(x in k.lower() for x in ("date", "time", "timestamp", "dt"))]
    rain_candidates = [k for k in field_ids if k and any(x in k.lower() for x in ("rain", "precip", "rf", "mm"))]
    station_candidates = [k for k in field_ids if k and any(x in k.lower() for x in ("station", "site", "location", "name"))]
    lat_candidates = [k for k in field_ids if k and "lat" in k.lower()]
    lon_candidates = [k for k in field_ids if k and ("lon" in k.lower() or "lng" in k.lower())]

    dates = []
    ts_field = ts_candidates[0] if ts_candidates else None
    for rec in records:
        if ts_field and rec.get(ts_field):
            dates.append(str(rec[ts_field]))

    return {
        "fields": field_ids,
        "field_types": {f.get("id"): f.get("type") for f in fields},
        "timestamp_field_candidates": ts_candidates,
        "rainfall_field_candidates": rain_candidates,
        "station_field_candidates": station_candidates,
        "latitude_candidates": lat_candidates,
        "longitude_candidates": lon_candidates,
        "record_count_meta": meta.get("total"),
        "record_count_fetched": len(records),
        "date_min": min(dates) if dates else None,
        "date_max": max(dates) if dates else None,
        "sample_record_keys": list(records[0].keys()) if records else [],
    }


def main():
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    inventory = []

    for res in RESOURCES:
        filters = {"State": res["state"], "District": res["district"], "Agency": res["agency"]}
        print(f"Fetching {res['label']} ...")
        try:
            data = fetch(res["resource_id"], filters, limit=100)
        except Exception as exc:
            inventory.append({**res, "error": str(exc)})
            continue

        result = data.get("result", {})
        meta = result.get("meta", {})
        records = result.get("records", [])
        analysis = analyze(meta, records)

        sample_path = SAMPLE_DIR / f"{res['label']}.json"
        sample_path.write_text(
            json.dumps({"meta": meta, "records": records[:5], "total": meta.get("total")}, indent=2),
            encoding="utf-8",
        )

        # pagination probe
        total = meta.get("total") or 0
        has_more = total > 100

        inventory.append(
            {
                "resource_id": res["resource_id"],
                "district": res["district"],
                "state": res["state"],
                "agency": res["agency"],
                "label": res["label"],
                **analysis,
                "pagination_supported": has_more,
                "sample_file": str(sample_path.relative_to(ROOT)),
            }
        )

    REPORT.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    print(f"Wrote {REPORT}")
    for item in inventory:
        print(
            item.get("label"),
            "total=",
            item.get("record_count_meta"),
            "fields=",
            len(item.get("fields", [])),
            "rain=",
            item.get("rainfall_field_candidates"),
        )


if __name__ == "__main__":
    main()
