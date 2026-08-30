from companion_core.baseline import BaselineLearner
from companion_core.types import HealthFeatures


def test_skips_abnormal_adaptation():
    l = BaselineLearner()
    l.b.ready = True
    l.b.samples = 30
    l.b.resting_hr = 72
    f = HealthFeatures(hr=140, spo2=98, temperature=36.4, signal_quality=0.9, valid=True)
    l.update(f, risk_hint=0.9)
    assert abs(l.b.resting_hr - 72) < 0.01


def test_adapts_to_valid_normal():
    l = BaselineLearner()
    f = HealthFeatures(hr=80, spo2=98, temperature=36.4, signal_quality=0.9, valid=True)
    before = l.b.resting_hr
    l.update(f, risk_hint=0.05)
    assert l.b.resting_hr != before
