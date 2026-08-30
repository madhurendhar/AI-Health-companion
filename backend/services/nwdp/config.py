"""NWDP resource registry — inspect docs/nwdp_api_inventory.md before changing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NwdpResource:
    resource_id: str
    district: str
    state: str
    agency: str
    purpose: str
    rainfall_field: str | None = None
    timestamp_field: str = "Data Acquisition Time"
    station_field: str = "Station"
    lat_field: str = "Latitude"
    lon_field: str = "Longitude"


BASE_URL = "https://www.nwdp.nwic.gov.in/api/3/action/datastore_search"

# Inspected 2026-08-30 — see docs/nwdp_api_inventory.md
RESOURCES: dict[str, dict[str, NwdpResource]] = {
    "Chennai": {
        "rainfall_historical": NwdpResource(
            resource_id="51b0e617-02dc-4dd8-a6ce-fdce6c1731b9",
            district="Chennai",
            state="Tamil Nadu",
            agency="Tamil Nadu SW GW",
            purpose="hourly_rainfall_historical",
            rainfall_field="Telemetry Hourly Rainfall (mm)",
        ),
        "rainfall_current": NwdpResource(
            resource_id="21b02519-f3d3-409d-a091-94332d848a8e",
            district="Chennai",
            state="Tamil Nadu",
            agency="Tamil Nadu SW GW",
            purpose="hourly_rainfall_current",
            rainfall_field="Telemetry Hourly Rainfall (mm)",
        ),
        "river_level": NwdpResource(
            resource_id="77459b05-fcbd-4b8c-97e1-e2a33d359ce3",
            district="Chennai",
            state="Tamil Nadu",
            agency="Tamil Nadu SW GW",
            purpose="river_water_level",
            rainfall_field="River Water Level Telemetry Hourly (meter)",
        ),
    },
    "Kanyakumari": {
        "solar": NwdpResource(
            resource_id="cd797dd2-dff1-45ee-87df-eaa554bbeb5f",
            district="Kanyakumari",
            state="Tamil Nadu",
            agency="Tamil Nadu SW GW",
            purpose="solar_radiation",
            rainfall_field=None,
        ),
        "temperature": NwdpResource(
            resource_id="387aa243-ae4d-4aa3-932b-bbc5b09e148e",
            district="Kanyakumari",
            state="Tamil Nadu",
            agency="Tamil Nadu SW GW",
            purpose="air_temperature",
            rainfall_field=None,
        ),
    },
}


def rainfall_resource(location: str, prefer_current: bool = True) -> NwdpResource | None:
    loc = RESOURCES.get(location, {})
    key = "rainfall_current" if prefer_current else "rainfall_historical"
    return loc.get(key)


def supported_rainfall_locations() -> list[str]:
    return [k for k, v in RESOURCES.items() if "rainfall_current" in v or "rainfall_historical" in v]
