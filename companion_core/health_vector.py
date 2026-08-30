from companion_core.types import HealthFeatures

HEALTH_FEATURE_ORDER = [
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


def health_vector(f: HealthFeatures) -> list[float]:
    d = f.__dict__
    return [float(d[k]) if d.get(k) is not None else 0.0 for k in HEALTH_FEATURE_ORDER]
