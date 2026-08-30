from companion_core.demo import demo_reading
from tools.device_sim import CompanionPipeline


def test_normal_and_deviation(tmp_path):
    pipe = CompanionPipeline(str(tmp_path), demo=True)
    last = None
    for i in range(25):
        last, _, _ = pipe.step(demo_reading(i, "normal"))
    assert last.status.value in ("NORMAL", "INSUFFICIENT", "RECHECK")
    pipe2 = CompanionPipeline(str(tmp_path / "b"), demo=True)
    last2 = None
    for i in range(30):
        last2, snap, _ = pipe2.step(demo_reading(i, "persistent_deviation"))
    assert snap["demo_mode"] is True
    assert last2.status.value in ("RECHECK", "ELEVATED")


def test_offline_health_does_not_need_network(tmp_path):
    pipe = CompanionPipeline(str(tmp_path), demo=True)
    r, snap, _ = pipe.step(demo_reading(1, "normal"))
    assert snap["system"]["offline_health"] is True
    assert (tmp_path / "patient" / "readings.csv").exists()
