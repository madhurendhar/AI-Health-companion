"""Clearly labelled DEMO MODE generators. Never mix with live sensor bytes."""

from companion_core.types import SensorReading, SensorState


def demo_reading(t_s: float, scenario: str) -> SensorReading:
    r = SensorReading(timestamp_s=t_s, demo_mode=True, mq_state=SensorState.OK)
    r.dht_state = SensorState.OK
    r.mlx_state = SensorState.OK
    r.max30102_state = SensorState.OK
    r.ppg_quality = 0.85
    r.dht_temp_c = 29.0
    r.humidity_pct = 70.0
    r.mq135_relative = 1.05
    r.mq135_raw = 1200
    r.mlx_ambient_c = 29.0

    if scenario == "normal":
        r.hr_bpm = 74.0
        r.spo2_pct = 98.0
        r.object_temp_c = 36.4
    elif scenario == "persistent_deviation":
        r.hr_bpm = 118.0
        r.spo2_pct = 91.0
        r.object_temp_c = 38.1
        r.ppg_quality = 0.8
    elif scenario == "environment_change":
        r.hr_bpm = 76.0
        r.spo2_pct = 97.5
        r.object_temp_c = 36.5
        r.dht_temp_c = 36.0
        r.humidity_pct = 90.0
        r.mq135_relative = 2.1
        r.mq135_raw = 2500
    elif scenario == "low_signal":
        r.hr_bpm = 80.0
        r.spo2_pct = 96.0
        r.object_temp_c = 36.4
        r.ppg_quality = 0.2
        r.max30102_state = SensorState.NO_FINGER
    else:
        r.hr_bpm = 74.0
        r.spo2_pct = 98.0
        r.object_temp_c = 36.4
    return r


DEMO_FLOOD_HOURLY = {
    "normal": [0.0] * 72,
    "approaching": [1.2] * 48 + [6.0] * 18 + [12.0] * 6,
    "high": [8.0] * 24 + [15.0] * 24 + [22.0] * 24,
}
