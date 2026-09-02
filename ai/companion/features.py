"""Feature helpers for companion environmental disaster model."""

from __future__ import annotations

import math


def heat_index_approx(temp_c: float, humidity: float) -> float:
    """Screening heat-stress index (°C-scale proxy). Not clinical heat-index validation."""
    if temp_c < 27.0:
        return temp_c
    # Simplified humid-heat stress above 27°C
    t, h = temp_c, max(0.0, min(100.0, humidity))
    return temp_c + 0.33 * max(0.0, h - 40.0) + 0.15 * max(0.0, t - 32.0)


ENV_FEATURE_NAMES = [
    "ambient_temp_c",
    "humidity",
    "heat_index",
    "mq135_relative",
    "rain_1h",
    "rain_24h",
    "rain_72h",
    "intensity",
    "trend",
]

HEALTH_FEATURE_NAMES = [
    "hr",
    "spo2",
    "temperature",
    "hr_trend",
    "spo2_trend",
    "temperature_trend",
    "signal_quality",
    "hr_dev",
    "spo2_dev",
    "temp_dev",
    "persistence",
    "ambient_temp",
    "humidity",
    "mq135_relative",
]
