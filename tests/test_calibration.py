from companion_core.calibration import CalibrationConfig, CalibrationPhase, CalibrationSession
from companion_core.types import SensorReading, SensorState


def _good_reading(ts: float, hr: float = 72.0, spo2: float = 98.0, temp: float = 36.2) -> SensorReading:
    return SensorReading(
        timestamp_s=ts,
        hr_bpm=hr,
        spo2_pct=spo2,
        object_temp_c=temp,
        ppg_quality=0.85,
        max30102_state=SensorState.OK,
        mlx_state=SensorState.OK,
    )


def test_calibration_completes_with_enough_samples():
    cal = CalibrationSession(CalibrationConfig(duration_s=5.0, min_good_samples=5, sample_interval_s=0.0))
    cal.start(0.0)
    for i in range(6):
        cal.feed(_good_reading(float(i + 1)), float(i + 1))
    assert cal.phase == CalibrationPhase.READY
    b = cal.to_baseline()
    assert b is not None
    assert b.ready is True
    assert 70 < b.resting_hr < 75
    assert b.typical_spo2 > 97


def test_calibration_rejects_low_ppg():
    cal = CalibrationSession(CalibrationConfig(duration_s=2.0, min_good_samples=3, sample_interval_s=0.0))
    cal.start(0.0)
    bad = _good_reading(1.0)
    bad.ppg_quality = 0.2
    cal.feed(bad, 1.0)
    assert cal.good_samples == 0
    assert cal.rejected_samples == 1


def test_calibration_fails_if_timeout():
    cal = CalibrationSession(CalibrationConfig(duration_s=1.0, min_good_samples=10, sample_interval_s=0.0))
    cal.start(0.0)
    cal.feed(_good_reading(2.0), 2.0)
    assert cal.phase == CalibrationPhase.FAILED
