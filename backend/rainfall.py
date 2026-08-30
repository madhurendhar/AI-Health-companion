"""NWDP rainfall provider with cache and stale fallback."""

from __future__ import annotations

import os
import time
from pathlib import Path

from dotenv import load_dotenv

from backend.services.nwdp.client import FileCache, NwdpClient
from backend.services.nwdp.config import rainfall_resource, supported_rainfall_locations
from backend.services.nwdp.parser import hourly_mm_series, parse_record
from companion_core.flood_features import rainfall_windows
from companion_core.types import FloodFeatures

load_dotenv()

CACHE_DIR = Path(os.getenv("NWDP_CACHE_DIR", "data/processed/rainfall/cache"))


class RainfallProvider:
    def hourly_mm(self, location: str) -> tuple[list[float], float, str, dict]:
        """Returns (hourly_mm oldest->newest, updated_s, source_label, meta)."""
        raise NotImplementedError


class NwdpRainfallProvider(RainfallProvider):
    def __init__(self, cache_ttl_s: int | None = None):
        self.client = NwdpClient()
        self.cache = FileCache(CACHE_DIR)
        self.cache_ttl_s = cache_ttl_s or int(os.getenv("NWDP_CACHE_TTL_S", "600"))

    def hourly_mm(self, location: str) -> tuple[list[float], float, str, dict]:
        if location not in supported_rainfall_locations():
            raise ValueError(
                f"No NWDP rainfall resource for {location}. "
                f"Supported: {supported_rainfall_locations()}. Kanyakumari: PENDING rainfall resource."
            )
        res = rainfall_resource(location, prefer_current=True)
        if res is None:
            raise ValueError(f"No rainfall resource for {location}")

        cache_key = f"nwdp_{location}_recent"
        cached = self.cache.get(cache_key, self.cache_ttl_s)
        if cached:
            return (
                cached["hourly_mm"],
                cached["updated_s"],
                "NWDP",
                {"data_status": "LIVE", "stale": False, "resource_id": res.resource_id},
            )

        try:
            raw = self.client.fetch_recent(res, limit=500)
            parsed = [p for r in raw if (p := parse_record(r, res))]
            hours = hourly_mm_series(parsed, hours=72)
            updated = time.time()
            payload = {"hourly_mm": hours, "updated_s": updated, "record_count": len(parsed)}
            self.cache.set(cache_key, payload)
            return hours, updated, "NWDP", {
                "data_status": "LIVE",
                "stale": False,
                "resource_id": res.resource_id,
                "stations": list({p.station for p in parsed})[:5],
            }
        except Exception as exc:
            stale = self.cache.get_stale(cache_key)
            if stale:
                age = time.time() - stale.get("cached_at_s", stale.get("updated_s", 0))
                return (
                    stale["hourly_mm"],
                    stale.get("updated_s", 0),
                    "NWDP",
                    {"data_status": "STALE_DATA", "stale": True, "error": str(exc), "age_s": age},
                )
            raise


class DemoRainfallProvider(RainfallProvider):
    def __init__(self, scenario: str = "normal"):
        self.scenario = scenario

    def hourly_mm(self, location: str) -> tuple[list[float], float, str, dict]:
        from companion_core.demo import DEMO_FLOOD_HOURLY

        hours = list(DEMO_FLOOD_HOURLY.get(self.scenario, DEMO_FLOOD_HOURLY["normal"]))
        return hours, time.time(), "DEMO MODE / SIMULATED DATA", {"data_status": "DEMO", "stale": False}


class OpenMeteoProvider(RainfallProvider):
    """Fallback when NWDP unavailable for a location."""

    def __init__(self, base: str | None = None):
        import os

        self.base = base or os.getenv("OPEN_METEO_BASE_URL", "https://api.open-meteo.com/v1/forecast")
        self._coords = {
            "Chennai": (13.0827, 80.2707),
            "Kanyakumari": (8.0883, 77.5385),
            "Mumbai": (19.0760, 72.8777),
        }

    def hourly_mm(self, location: str) -> tuple[list[float], float, str, dict]:
        import httpx

        if location not in self._coords:
            raise ValueError(f"Unknown location {location}")
        lat, lon = self._coords[location]
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "precipitation",
            "past_days": 3,
            "forecast_days": 1,
            "timezone": "auto",
        }
        with httpx.Client(timeout=20.0) as client:
            res = client.get(self.base, params=params)
            res.raise_for_status()
            precip = res.json()["hourly"]["precipitation"]
        hours = [float(x or 0.0) for x in precip[-72:]]
        return hours, time.time(), "open_meteo_fallback", {"data_status": "LIVE", "stale": False}


class CachedRainfall:
    def __init__(self, inner: RainfallProvider, ttl_s: int = 600):
        self.inner = inner
        self.ttl_s = ttl_s
        self._mem: dict[str, tuple] = {}

    def hourly_mm(self, location: str) -> tuple[list[float], float, str, dict]:
        hit = self._mem.get(location)
        if hit and (time.time() - hit[1]) < self.ttl_s:
            return hit
        val = self.inner.hourly_mm(location)
        self._mem[location] = val
        return val


def features_for(hours: list[float], location: str) -> FloodFeatures:
    f = rainfall_windows(hours)
    f.location = location
    return f


class CompositeRainfallProvider(RainfallProvider):
    """Route each district to NWDP or Open-Meteo fallback."""

    def __init__(self, scenario: str = "normal"):
        from backend.services.nwdp.locations import source_for

        self._nwdp = NwdpRainfallProvider()
        self._meteo = OpenMeteoProvider()
        self._source_for = source_for

    def hourly_mm(self, location: str) -> tuple[list[float], float, str, dict]:
        src = self._source_for(location)
        if src == "nwdp":
            return self._nwdp.hourly_mm(location)
        return self._meteo.hourly_mm(location)


def build_provider(demo: bool = False, scenario: str = "normal") -> RainfallProvider:
    if demo or os.getenv("RAINFALL_PROVIDER") == "demo":
        return DemoRainfallProvider(scenario)
    primary = os.getenv("RAINFALL_PROVIDER", "nwdp")
    if primary == "open_meteo":
        return OpenMeteoProvider()
    if primary == "nwdp":
        return CompositeRainfallProvider(scenario)
    return NwdpRainfallProvider()
