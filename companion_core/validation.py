from companion_core.config import HEALTH
from companion_core.types import SensorReading, SensorState


def _in_range(value, lo, hi) -> bool:
    return value is not None and lo <= value <= hi


def validate_reading(r: SensorReading) -> SensorReading:
    out = SensorReading(**r.__dict__)

    if out.max30102_state == SensorState.OK:
        hr_ok = _in_range(out.hr_bpm, HEALTH.hr_min, HEALTH.hr_max)
        spo2_ok = _in_range(out.spo2_pct, HEALTH.spo2_min, HEALTH.spo2_max)
        if out.ppg_quality < HEALTH.signal_quality_min:
            out.max30102_state = SensorState.NO_SIGNAL if out.ppg_quality < 0.15 else SensorState.INVALID_READING
            out.hr_bpm = None
            out.spo2_pct = None
        elif not hr_ok or not spo2_ok:
            out.max30102_state = SensorState.INVALID_READING
            if not hr_ok:
                out.hr_bpm = None
            if not spo2_ok:
                out.spo2_pct = None

    if out.mlx_state == SensorState.OK:
        if not _in_range(out.object_temp_c, HEALTH.object_temp_min_c, HEALTH.object_temp_max_c):
            out.mlx_state = SensorState.INVALID_READING
            out.object_temp_c = None

    if out.dht_state == SensorState.OK:
        t_ok = _in_range(out.dht_temp_c, HEALTH.ambient_temp_min_c, HEALTH.ambient_temp_max_c)
        h_ok = _in_range(out.humidity_pct, HEALTH.humidity_min, HEALTH.humidity_max)
        if not t_ok or not h_ok:
            out.dht_state = SensorState.INVALID_READING
            if not t_ok:
                out.dht_temp_c = None
            if not h_ok:
                out.humidity_pct = None

    return out
