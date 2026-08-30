from pathlib import Path
from companion_core.sd_store import PatientStore


def test_sd_roundtrip(tmp_path: Path):
    s = PatientStore(tmp_path)
    s.write_baseline({"resting_hr": 70, "samples": 3, "ready": False})
    assert s.read_baseline()["resting_hr"] == 70
    s.append_reading({"timestamp_s": 1, "hr": 72, "status": "NORMAL"})
    s.append_event(1, "health_status", "NORMAL")
    text = (tmp_path / "patient" / "readings.csv").read_text(encoding="utf-8")
    assert "NORMAL" in text
    assert s.ok
