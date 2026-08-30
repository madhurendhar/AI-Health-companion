"""Per-district rainfall source routing."""

from __future__ import annotations

# nwdp = NWDP telemetry; open_meteo = fallback when no NWDP rainfall resource
LOCATION_SOURCES: dict[str, str] = {
    "Chennai": "nwdp",
    "Kanyakumari": "open_meteo",
}

SUPPORTED_LOCATIONS = list(LOCATION_SOURCES.keys())


def source_for(location: str) -> str:
    if location not in LOCATION_SOURCES:
        raise ValueError(f"Unknown location {location}. Supported: {SUPPORTED_LOCATIONS}")
    return LOCATION_SOURCES[location]
