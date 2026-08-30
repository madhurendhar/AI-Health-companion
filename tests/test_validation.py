from companion_core.types import SensorReading, SensorState
from companion_core.validation import validate_reading


def test_rejects_out_of_range_hr():
    r = SensorReading(
        timestamp_s=1,
        hr_bpm=300,
        spo2_pct=98,
        ppg_quality=0.9,
        max30102_state=SensorState.OK,
    )
    o = validate_reading(r)
    assert o.hr_bpm is None
    assert o.max30102_state == SensorState.INVALID_READING


def test_no_finger_quality():
    r = SensorReading(timestamp_s=1, hr_bpm=70, spo2_pct=98, ppg_quality=0.05, max30102_state=SensorState.OK)
    o = validate_reading(r)
    assert o.hr_bpm is None
    assert o.max30102_state == SensorState.NO_SIGNAL
