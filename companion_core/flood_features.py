from companion_core.types import FloodFeatures


def rainfall_windows(hourly_mm: list[float]) -> FloodFeatures:
    """hourly_mm oldest -> newest. Missing hours treated as 0 only if list is provided."""
    h = list(hourly_mm)

    def s(n: int) -> float:
        if not h:
            return 0.0
        return float(sum(h[-n:])) if n <= len(h) else float(sum(h))

    last = h[-1] if h else 0.0
    prev = h[-2] if len(h) > 1 else last
    f = FloodFeatures(
        rain_1h=s(1),
        rain_3h=s(3),
        rain_6h=s(6),
        rain_12h=s(12),
        rain_24h=s(24),
        rain_48h=s(48),
        rain_72h=s(72),
        intensity=last,
        trend=last - prev,
    )
    return f


def feature_vector(f: FloodFeatures) -> list[float]:
    return [
        f.rain_1h,
        f.rain_3h,
        f.rain_6h,
        f.rain_12h,
        f.rain_24h,
        f.rain_48h,
        f.rain_72h,
        f.intensity,
        f.trend,
    ]


FEATURE_NAMES = [
    "rain_1h",
    "rain_3h",
    "rain_6h",
    "rain_12h",
    "rain_24h",
    "rain_48h",
    "rain_72h",
    "intensity",
    "trend",
]
