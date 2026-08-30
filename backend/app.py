from __future__ import annotations

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.flood_service import FloodEngine, load_baseline
from backend.monitor import recent, trend
from backend.rainfall import build_provider, features_for
from companion_core.demo import DEMO_FLOOD_HOURLY
from backend.services.nwdp.locations import LOCATION_SOURCES, SUPPORTED_LOCATIONS

load_dotenv()

API_TOKEN = os.getenv("COMPANION_API_TOKEN", "change-me-local-token")
DEMO_MODE = os.getenv("COMPANION_DEMO_MODE", "false").lower() in ("1", "true", "yes")

app = FastAPI(title="Flood Early-Warning Backend", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_demo_scenario = "normal"
_engine: FloodEngine | None = None


def _load_engine():
    global _engine
    _engine = FloodEngine(build_provider(demo=DEMO_MODE, scenario=_demo_scenario))


_load_engine()


def require_token(authorization: str | None = Header(default=None), x_api_token: str | None = Header(default=None)):
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    if x_api_token:
        token = x_api_token
    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")
    return True


def engine(demo: bool | None = None) -> FloodEngine:
    use_demo = DEMO_MODE if demo is None else demo
    return FloodEngine(build_provider(demo=use_demo, scenario=_demo_scenario))


@app.get("/monitor/status")
def monitor_status(location: str = "Chennai"):
    f = engine().evaluate(location, demo=DEMO_MODE)
    return {
        "location": location,
        "live": f,
        "trend": trend(location),
        "data_source": "NWDP",
    }


@app.get("/monitor/history")
def monitor_history(location: str = "Chennai", n: int = 20):
    return {"location": location, "entries": recent(location, n), "trend": trend(location)}


@app.get("/data-status")
def data_status():
    return {
        "rainfall_provider": os.getenv("RAINFALL_PROVIDER", "nwdp"),
        "demo_mode": DEMO_MODE,
        "nwdp_locations": [k for k, v in LOCATION_SOURCES.items() if v == "nwdp"],
        "open_meteo_locations": [k for k, v in LOCATION_SOURCES.items() if v == "open_meteo"],
        "supported_locations": SUPPORTED_LOCATIONS,
        "kanyakumari_rainfall": "open_meteo_fallback (no NWDP rainfall resource in supplied IDs)",
        "inference_mode": "NWDP live vs historical percentiles (no synthetic data)",
        "historical_stats": {loc: load_baseline(loc) is not None for loc in ("Chennai",)},
    }


@app.get("/system/status")
def system_status():
    return {
        "subsystem": "flood_early_warning",
        "health_subsystem": "NOT IMPLEMENTED — phase 2",
        "network": "ONLINE",
        "demo_mode": DEMO_MODE,
        "flood_model": {
            "name": "nwdp_historical_monitor_v1",
            "method": "live NWDP vs historical percentile comparison",
            "synthetic_ml": False,
            "flood_event_model": "flood_event_ifi_nwdp_v1",
            "flood_event_labels": "IFI-Impacts v3 (real Chennai events)",
        },
        "rainfall_provider": os.getenv("RAINFALL_PROVIDER", "nwdp"),
    }


@app.get("/rainfall")
def rainfall(location: str = "Chennai", demo: bool | None = None):
    try:
        hours, ts, src, meta = engine(demo).provider(demo).hourly_mm(location)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"rainfall error: {exc}") from exc
    f = features_for(hours, location)
    return {
        "location": location,
        "source": src,
        "updated_s": ts,
        "data_status": meta.get("data_status", "LIVE"),
        "hourly_tail_mm": hours[-6:],
        "windows": f.__dict__,
        "demo": src.startswith("DEMO"),
    }


@app.get("/flood/status")
def flood_status(location: str = "Chennai", demo: bool | None = None):
    try:
        return engine(demo).evaluate(location, demo=demo if demo is not None else DEMO_MODE)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/flood/events")
def flood_events(location: str = "Chennai", limit: int = 50):
    from companion_core.flood_events import event_inventory_summary, latest_river_level, list_historical_events

    return {
        "location": location,
        "inventory": event_inventory_summary(),
        "historical_event_days": list_historical_events(location, limit),
        "river_level": latest_river_level(),
        "label_source": "IFI-Impacts v3 (IMD) — real documented flood events",
        "validation": "Not synthetic — see reports/flood_events_inventory.json",
    }


@app.get("/flood/history")
def flood_history(location: str = "Chennai"):
    p = Path(f"data/processed/rainfall/{location.lower()}_rainfall.parquet")
    if not p.exists():
        return {"location": location, "available": False, "reason": "run ai/flood/data/ingest_nwdp.py"}
    import pandas as pd

    df = pd.read_parquet(p)
    df["hour"] = df["timestamp"].dt.floor("h")
    hourly = df.groupby("hour", as_index=False)["rainfall_mm"].sum().tail(168)
    return {
        "location": location,
        "available": True,
        "source": "NWDP historical",
        "points": [
            {"t": str(r["hour"]), "mm": float(r["rainfall_mm"])} for _, r in hourly.iterrows()
        ],
    }


class DemoIn(BaseModel):
    flood_scenario: str = "normal"


@app.post("/demo/scenario")
def set_demo(body: DemoIn, _: bool = Depends(require_token)):
    global _demo_scenario
    if body.flood_scenario not in DEMO_FLOOD_HOURLY:
        raise HTTPException(400, "unknown flood scenario")
    _demo_scenario = body.flood_scenario
    return {"ok": True, "flood_scenario": _demo_scenario, "banner": "DEMO MODE / SIMULATED DATA"}


# ESP32 posts flood poll results (optional)
class DeviceFloodIn(BaseModel):
    device_id: str
    location: str
    flood_status: str


_device_flood: dict = {}


@app.post("/device/flood")
def device_flood(body: DeviceFloodIn, _: bool = Depends(require_token)):
    global _device_flood
    _device_flood = {**body.model_dump(), "received_s": time.time()}
    return {"ok": True}


dash = Path("dashboard")
if dash.exists():
    app.mount("/", StaticFiles(directory=str(dash), html=True), name="dashboard")
