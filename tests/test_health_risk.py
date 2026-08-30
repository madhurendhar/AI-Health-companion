from companion_core.baseline import BaselineLearner
from companion_core.features import FeatureExtractor
from companion_core.health_risk import heuristic_risk, status_from_score
from companion_core.types import HealthStatus, SensorReading, SensorState


def _ok(hr, spo2, temp, q=0.9):
    return SensorReading(
        timestamp_s=1,
        hr_bpm=hr,
        spo2_pct=spo2,
        object_temp_c=temp,
        dht_temp_c=28,
        humidity_pct=60,
        mq135_relative=1.0,
        ppg_quality=q,
        max30102_state=SensorState.OK,
        mlx_state=SensorState.OK,
        dht_state=SensorState.OK,
        mq_state=SensorState.OK,
    )


def test_low_quality_does_not_alert():
    b = BaselineLearner()
    b.b.ready = True
    fx = FeatureExtractor()
    f = fx.extract(_ok(130, 88, 38.5, q=0.1), b.b, False)
    score, reason = heuristic_risk(f, b.b)
    assert score == 0.0
    assert "low_signal" in reason or score == 0.0


def test_persistent_deviation_not_simple_hr_threshold():
    """HR 101 alone is not enough; uses baseline deviation + other features."""
    b = BaselineLearner()
    b.b.ready = True
    b.b.resting_hr = 100.0
    b.b.hr_range = 20.0
    fx = FeatureExtractor()
    f = fx.extract(_ok(101, 98, 36.4), b.b, False)
    score, _ = heuristic_risk(f, b.b)
    assert score < 0.35
    assert status_from_score(score, f) == HealthStatus.NORMAL


def test_combined_abnormal_pattern_elevates():
    b = BaselineLearner()
    b.b.ready = True
    b.b.resting_hr = 70
    b.b.typical_spo2 = 98
    b.b.typical_temp = 36.4
    fx = FeatureExtractor()
    f = None
    for _ in range(8):
        f = fx.extract(_ok(125, 90, 38.4), b.b, True)
    score, reason = heuristic_risk(f, b.b)
    assert score >= 0.35
    assert "hr_baseline_dev" in reason or "spo2_baseline_dev" in reason
