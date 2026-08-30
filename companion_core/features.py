from companion_core.filtering import Ema, Trend
from companion_core.types import Baseline, HealthFeatures, SensorReading, SensorState


class FeatureExtractor:
    def __init__(self):
        self.hr_ema = Ema()
        self.spo2_ema = Ema()
        self.temp_ema = Ema()
        self.amb_ema = Ema()
        self.hum_ema = Ema()
        self.mq_ema = Ema()
        self.hr_tr = Trend()
        self.spo2_tr = Trend()
        self.temp_tr = Trend()
        self._persist_hits = 0

    def extract(self, r: SensorReading, baseline: Baseline, prev_abnormal: bool) -> HealthFeatures:
        f = HealthFeatures()
        f.signal_quality = r.ppg_quality

        if r.max30102_state == SensorState.OK:
            f.hr = self.hr_ema.update(r.hr_bpm)
            f.spo2 = self.spo2_ema.update(r.spo2_pct)
            f.hr_trend = self.hr_tr.update(f.hr)
            f.spo2_trend = self.spo2_tr.update(f.spo2)
        if r.mlx_state == SensorState.OK:
            f.temperature = self.temp_ema.update(r.object_temp_c)
            f.temperature_trend = self.temp_tr.update(f.temperature)
        if r.dht_state == SensorState.OK:
            f.ambient_temp = self.amb_ema.update(r.dht_temp_c)
            f.humidity = self.hum_ema.update(r.humidity_pct)
        if r.mq_state in (SensorState.OK,):
            f.mq135_relative = self.mq_ema.update(r.mq135_relative)

        if f.hr is not None:
            f.hr_dev = (f.hr - baseline.resting_hr) / max(baseline.hr_range, 4.0)
        if f.spo2 is not None:
            f.spo2_dev = (baseline.typical_spo2 - f.spo2) / 4.0
        if f.temperature is not None:
            f.temp_dev = (f.temperature - baseline.typical_temp) / 1.2

        if prev_abnormal:
            self._persist_hits += 1
        else:
            self._persist_hits = max(0, self._persist_hits - 1)
        f.persistence = min(1.0, self._persist_hits / 6.0)

        f.valid = (f.hr is not None and f.spo2 is not None and f.temperature is not None
                   and f.signal_quality >= 0.45)
        return f
