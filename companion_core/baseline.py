from companion_core.config import HEALTH
from companion_core.types import Baseline, HealthFeatures


class BaselineLearner:
    def __init__(self):
        self.b = Baseline()

    def update(self, f: HealthFeatures, risk_hint: float) -> Baseline:
        if not f.valid:
            return self.b
        # Do not immediately adapt to abnormal readings (even during warmup).
        if risk_hint >= HEALTH.baseline_abnormal_skip:
            return self.b

        rate = HEALTH.baseline_adapt_rate if self.b.ready else 0.15
        if f.hr is not None:
            self.b.resting_hr = (1 - rate) * self.b.resting_hr + rate * f.hr
            spread = abs(f.hr - self.b.resting_hr)
            self.b.hr_range = (1 - rate) * self.b.hr_range + rate * max(spread, 6.0)
        if f.spo2 is not None:
            self.b.typical_spo2 = (1 - rate) * self.b.typical_spo2 + rate * f.spo2
        if f.temperature is not None:
            self.b.typical_temp = (1 - rate) * self.b.typical_temp + rate * f.temperature
        if f.ambient_temp is not None:
            self.b.ambient_temp = (1 - rate) * self.b.ambient_temp + rate * f.ambient_temp
        if f.humidity is not None:
            self.b.humidity = (1 - rate) * self.b.humidity + rate * f.humidity

        self.b.samples += 1
        self.b.ready = self.b.samples >= HEALTH.baseline_min_samples
        return self.b

    def to_dict(self) -> dict:
        b = self.b
        return {
            "resting_hr": b.resting_hr,
            "hr_range": b.hr_range,
            "typical_spo2": b.typical_spo2,
            "typical_temp": b.typical_temp,
            "ambient_temp": b.ambient_temp,
            "humidity": b.humidity,
            "samples": b.samples,
            "ready": b.ready,
        }

    def load_dict(self, d: dict) -> None:
        for k, v in d.items():
            if hasattr(self.b, k):
                setattr(self.b, k, v)
