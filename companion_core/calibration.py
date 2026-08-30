"""On-device personal baseline calibration — MAX30102 + MLX90614.

No external dataset. User sits still with finger on PPG for ~5 minutes while
good-quality HR, SpO2, and object-temperature samples are collected.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from enum import Enum

from companion_core.config import HEALTH
from companion_core.types import Baseline, SensorReading, SensorState


class CalibrationPhase(str, Enum):
    IDLE = "IDLE"
    CALIBRATING = "CALIBRATING"
    READY = "READY"
    FAILED = "FAILED"


@dataclass(frozen=True)
class CalibrationConfig:
    duration_s: float = 300.0
    min_good_samples: int = 40
    min_ppg_quality: float = 0.50
    max_hr_jump_bpm: float = 25.0
    sample_interval_s: float = 1.0


@dataclass
class CalibrationSession:
    """Collect personal vitals baseline from live sensors."""

    cfg: CalibrationConfig = field(default_factory=CalibrationConfig)
    phase: CalibrationPhase = CalibrationPhase.IDLE
    started_s: float | None = None
    last_accept_s: float | None = None
    good_samples: int = 0
    rejected_samples: int = 0
    hr_values: list[float] = field(default_factory=list)
    spo2_values: list[float] = field(default_factory=list)
    temp_values: list[float] = field(default_factory=list)
    ambient_values: list[float] = field(default_factory=list)
    humidity_values: list[float] = field(default_factory=list)
    message: str = ""

    def start(self, now_s: float) -> dict:
        self.phase = CalibrationPhase.CALIBRATING
        self.started_s = now_s
        self.last_accept_s = None
        self.good_samples = 0
        self.rejected_samples = 0
        self.hr_values.clear()
        self.spo2_values.clear()
        self.temp_values.clear()
        self.ambient_values.clear()
        self.humidity_values.clear()
        self.message = "Place finger on MAX30102. Hold still for 5 minutes."
        return self.status(now_s)

    def _reading_ok(self, r: SensorReading) -> tuple[bool, str]:
        if r.max30102_state not in (SensorState.OK,):
            return False, "ppg_no_signal"
        if r.ppg_quality < self.cfg.min_ppg_quality:
            return False, "low_ppg_quality"
        if r.hr_bpm is None or r.spo2_pct is None:
            return False, "missing_hr_spo2"
        if not (HEALTH.hr_min <= r.hr_bpm <= HEALTH.hr_max):
            return False, "hr_out_of_range"
        if not (HEALTH.spo2_min <= r.spo2_pct <= HEALTH.spo2_max):
            return False, "spo2_out_of_range"
        if r.mlx_state != SensorState.OK or r.object_temp_c is None:
            return False, "mlx_not_ready"
        if not (HEALTH.object_temp_min_c <= r.object_temp_c <= HEALTH.object_temp_max_c):
            return False, "temp_out_of_range"
        if self.hr_values:
            if abs(r.hr_bpm - self.hr_values[-1]) > self.cfg.max_hr_jump_bpm:
                return False, "hr_unstable"
        return True, "ok"

    def feed(self, reading: SensorReading, now_s: float) -> dict:
        if self.phase == CalibrationPhase.IDLE:
            return self.status(now_s)
        if self.phase in (CalibrationPhase.READY, CalibrationPhase.FAILED):
            return self.status(now_s)

        elapsed = (now_s - self.started_s) if self.started_s is not None else 0.0
        ok, reason = self._reading_ok(reading)
        if not ok:
            self.rejected_samples += 1
            self.message = f"Keep finger still — {reason}"
            if elapsed >= self.cfg.duration_s and self.good_samples < self.cfg.min_good_samples:
                self.phase = CalibrationPhase.FAILED
                self.message = "Calibration failed — not enough good samples. Try again."
            return self.status(now_s)

        if self.last_accept_s is not None and (now_s - self.last_accept_s) < self.cfg.sample_interval_s:
            return self.status(now_s)

        self.last_accept_s = now_s
        self.good_samples += 1
        self.hr_values.append(float(reading.hr_bpm))
        self.spo2_values.append(float(reading.spo2_pct))
        self.temp_values.append(float(reading.object_temp_c))
        if reading.dht_temp_c is not None:
            self.ambient_values.append(float(reading.dht_temp_c))
        if reading.humidity_pct is not None:
            self.humidity_values.append(float(reading.humidity_pct))

        progress = min(1.0, self.good_samples / self.cfg.min_good_samples)
        self.message = f"Calibrating… {int(progress * 100)}% — hold still"

        time_done = elapsed >= self.cfg.duration_s
        samples_done = self.good_samples >= self.cfg.min_good_samples
        if time_done and samples_done:
            self.phase = CalibrationPhase.READY
            self.message = "Calibration complete. Personal baseline saved."
        elif time_done and not samples_done:
            self.phase = CalibrationPhase.FAILED
            self.message = "Calibration failed — not enough good samples. Try again."

        return self.status(now_s)

    def status(self, now_s: float) -> dict:
        elapsed = 0.0
        if self.started_s is not None:
            elapsed = max(0.0, now_s - self.started_s)
        remaining = max(0.0, self.cfg.duration_s - elapsed)
        progress_time = min(1.0, elapsed / self.cfg.duration_s) if self.cfg.duration_s else 0.0
        progress_samples = min(1.0, self.good_samples / self.cfg.min_good_samples)
        return {
            "phase": self.phase.value,
            "elapsed_s": round(elapsed, 1),
            "remaining_s": round(remaining, 1),
            "good_samples": self.good_samples,
            "min_good_samples": self.cfg.min_good_samples,
            "rejected_samples": self.rejected_samples,
            "progress_time_pct": round(progress_time * 100, 1),
            "progress_samples_pct": round(progress_samples * 100, 1),
            "message": self.message,
            "sensors": ["MAX30102", "MLX90614"],
            "optional_sensors": ["DHT22", "MQ135"],
            "no_dataset_required": True,
        }

    def to_baseline(self) -> Baseline | None:
        if self.phase != CalibrationPhase.READY or not self.hr_values:
            return None
        hr = statistics.median(self.hr_values)
        spo2 = statistics.median(self.spo2_values)
        temp = statistics.median(self.temp_values)
        spread = max(self.hr_values) - min(self.hr_values)
        if len(self.hr_values) >= 4:
            q = statistics.quantiles(self.hr_values, n=4)
            spread = max(spread, q[2] - q[0])
        b = Baseline(
            resting_hr=hr,
            hr_range=max(6.0, spread / 2.0),
            typical_spo2=spo2,
            typical_temp=temp,
            samples=self.good_samples,
            ready=True,
        )
        if self.ambient_values:
            b.ambient_temp = statistics.median(self.ambient_values)
        if self.humidity_values:
            b.humidity = statistics.median(self.humidity_values)
        return b

    def reset(self) -> None:
        self.phase = CalibrationPhase.IDLE
        self.started_s = None
        self.message = ""
