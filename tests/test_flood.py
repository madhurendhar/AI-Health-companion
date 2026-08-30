from companion_core.flood_features import rainfall_windows
from companion_core.flood_risk import FloodStateMachine, heuristic_flood_score
from companion_core.types import FloodStatus


def test_windows():
    h = [1] * 24 + [2] * 24 + [3] * 24
    f = rainfall_windows(h)
    assert f.rain_1h == 3
    assert f.rain_24h == 3 * 24
    assert f.rain_72h == sum(h)


def test_hysteresis_no_oscillation():
    sm = FloodStateMachine()
    sm.update(0.5, 0)
    assert sm.status == FloodStatus.WATCH
    sm.update(0.39, 10)
    # still in cooldown / hysteresis band
    assert sm.status == FloodStatus.WATCH
    sm.update(0.2, 10000)
    assert sm.status == FloodStatus.LOW


def test_heuristic_high_rain():
    f = rainfall_windows([20.0] * 72)
    score, _ = heuristic_flood_score(f)
    assert score >= 0.4
