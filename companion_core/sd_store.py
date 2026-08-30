"""Local-only patient history (SD card analogue). Never sent to S3 by default."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from companion_core.config import STORAGE

HEADER = [
    "timestamp_s",
    "hr",
    "spo2",
    "temperature",
    "ambient_temp",
    "humidity",
    "mq135_relative",
    "hr_dev",
    "spo2_dev",
    "temp_dev",
    "signal_quality",
    "risk_score",
    "status",
]


class PatientStore:
    def __init__(self, root: str | Path):
        self.root = Path(root) / "patient"
        self.root.mkdir(parents=True, exist_ok=True)
        self.ok = True
        self._ensure()

    def _ensure(self):
        profile = self.root / "profile.json"
        if not profile.exists():
            profile.write_text(json.dumps({"note": "no personal identifiers stored"}, indent=2), encoding="utf-8")
        readings = self.root / "readings.csv"
        if not readings.exists():
            with readings.open("w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(HEADER)
        events = self.root / "events.csv"
        if not events.exists():
            with events.open("w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(["timestamp_s", "kind", "detail"])

    def write_baseline(self, data: dict) -> None:
        (self.root / "baseline.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    def read_baseline(self) -> dict | None:
        p = self.root / "baseline.json"
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

    def append_reading(self, row: dict) -> None:
        path = self.root / "readings.csv"
        self._rotate(path, STORAGE.max_readings_rows)
        with path.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([row.get(h, "") for h in HEADER])

    def append_event(self, ts: float, kind: str, detail: str) -> None:
        path = self.root / "events.csv"
        self._rotate(path, STORAGE.max_events_rows)
        with path.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([ts, kind, detail])

    def _rotate(self, path: Path, max_rows: int) -> None:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            self.ok = False
            return
        if len(lines) <= max_rows:
            return
        keep = [lines[0]] + lines[-(max_rows - 1) :]
        path.write_text("\n".join(keep) + "\n", encoding="utf-8")
