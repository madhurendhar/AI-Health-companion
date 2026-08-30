"""Relative air-quality indicator from MQ135 analog. Not PM2.5 / concentration."""

from companion_core.filtering import Ema
from companion_core.types import AirStatus, SensorState


class Mq135Tracker:
    def __init__(self, warmup_samples: int = 40):
        self.warmup_left = warmup_samples
        self.r0 = None
        self.ema = Ema(0.15)

    def update(self, raw: float | None) -> tuple[float | None, AirStatus, SensorState]:
        if raw is None:
            return None, AirStatus.WARMING_UP, SensorState.SENSOR_ERROR
        if self.warmup_left > 0:
            self.warmup_left -= 1
            if self.r0 is None:
                self.r0 = raw
            else:
                self.r0 = 0.9 * self.r0 + 0.1 * raw
            return None, AirStatus.WARMING_UP, SensorState.WARMING_UP

        rel = raw / max(self.r0 or raw, 1.0)
        smoothed = self.ema.update(rel)
        assert smoothed is not None
        if smoothed < 1.25:
            air = AirStatus.NORMAL
        elif smoothed < 1.8:
            air = AirStatus.ELEVATED
        else:
            air = AirStatus.HIGH
        return smoothed, air, SensorState.OK
