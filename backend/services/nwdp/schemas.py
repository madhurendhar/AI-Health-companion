from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class RainfallRecord:
    timestamp: str  # ISO8601 UTC
    state: str
    district: str
    agency: str
    station: str
    latitude: float | None
    longitude: float | None
    rainfall_mm: float
    rainfall_unit: str
    source: str
    resource_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
