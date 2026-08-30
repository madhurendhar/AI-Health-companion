from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from backend.services.nwdp.config import BASE_URL, NwdpResource
from backend.services.nwdp.schemas import RainfallRecord

_TS_RE = re.compile(r"^(\d{2})-(\d{2})-(\d{4})\s+(\d{2}):(\d{2})$")


def parse_timestamp(raw: str) -> datetime | None:
    """NWDP uses DD-MM-YYYY HH:MM (assumed IST per agency context)."""
    m = _TS_RE.match(str(raw).strip())
    if not m:
        return None
    d, mo, y, h, mi = map(int, m.groups())
    try:
        # Store as naive then tag IST (+5:30) — simplified as UTC offset fixed
        from datetime import timedelta

        dt = datetime(y, mo, d, h, mi)
        return dt.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
    except ValueError:
        return None


def parse_record(rec: dict[str, Any], res: NwdpResource) -> RainfallRecord | None:
    if not res.rainfall_field:
        return None
    raw_r = rec.get(res.rainfall_field)
    if raw_r is None or str(raw_r).strip() in ("", "-", "NA", "null"):
        return None
    try:
        rainfall = float(raw_r)
    except (TypeError, ValueError):
        return None
    ts = parse_timestamp(rec.get(res.timestamp_field, ""))
    if ts is None:
        return None
    lat = lon = None
    try:
        if rec.get(res.lat_field):
            lat = float(rec[res.lat_field])
        if rec.get(res.lon_field):
            lon = float(rec[res.lon_field])
    except (TypeError, ValueError):
        pass
    return RainfallRecord(
        timestamp=ts.isoformat(),
        state=str(rec.get("State", res.state)),
        district=str(rec.get("District", res.district)),
        agency=str(rec.get("Agency", res.agency)),
        station=str(rec.get(res.station_field, "")),
        latitude=lat,
        longitude=lon,
        rainfall_mm=rainfall,
        rainfall_unit="mm",
        source="NWDP",
        resource_id=res.resource_id,
    )


def aggregate_hourly(records: list[RainfallRecord]) -> list[tuple[datetime, float]]:
    """Sum sub-hourly readings into hourly buckets (oldest -> newest)."""
    buckets: dict[str, float] = {}
    order: list[str] = []
    for r in records:
        dt = datetime.fromisoformat(r.timestamp)
        key = dt.strftime("%Y-%m-%dT%H")
        if key not in buckets:
            order.append(key)
            buckets[key] = 0.0
        buckets[key] += r.rainfall_mm
    out: list[tuple[datetime, float]] = []
    tz = datetime.fromisoformat(records[0].timestamp).tzinfo if records else None
    for key in sorted(buckets.keys()):
        y, mo, d, h = int(key[0:4]), int(key[5:7]), int(key[8:10]), int(key[11:13])
        out.append((datetime(y, mo, d, h, tzinfo=tz), buckets[key]))
    return out


def hourly_mm_series(records: list[RainfallRecord], hours: int = 72) -> list[float]:
    agg = aggregate_hourly(records)
    vals = [v for _, v in agg]
    if len(vals) > hours:
        vals = vals[-hours:]
    return vals
