# Personal baseline calibration (no dataset)

On-device calibration learns **your** normal HR, SpO2, and MLX90614 screening temperature from live sensors. No external training dataset is required.

## When to calibrate

- **First use** of the device (or new user)
- After **baseline reset** on SD card
- If readings seem consistently flagged despite feeling normal

## Sensors used

| Sensor | Role during calibration |
|--------|-------------------------|
| **MAX30102** | HR, SpO2, PPG signal quality (finger required) |
| **MLX90614** | Non-contact object/skin temperature screening |
| **DHT22** | Optional ambient temp/humidity snapshot |
| **MQ135** | Separate warm-up baseline (~40 samples); not part of 5‑min vitals window |

## 5-minute flow

```text
1. MQ135 warm-up (automatic, ~1–2 min while idle)
2. User places finger on MAX30102, faces MLX90614 toward forehead/wrist
3. CALIBRATING for up to 5 minutes (40+ good samples at 1 Hz)
4. Baseline saved to SD (/patient/baseline.json)
5. Health screening compares live readings vs this baseline
```

### Good sample requirements

- PPG quality ≥ 0.50
- Finger present, HR/SpO2 in valid range
- MLX90614 valid object temperature
- User **still** — large HR jumps between samples are rejected

### During calibration

- Status: `CALIBRATING` — **no ELEVATED alerts**
- OLED: progress % and “hold still”
- If time ends with &lt; 40 good samples → `FAILED` (retry)

## Implementation

| Layer | Module |
|-------|--------|
| Python (host sim / backend) | `companion_core/calibration.py` |
| ESP32 | `firmware/src/processing/calibration.cpp` |
| Ongoing adaptation | `companion_core/baseline.py` (slow drift after ready) |

## Python usage

```python
from companion_core.calibration import CalibrationSession
from companion_core.baseline import BaselineLearner

cal = CalibrationSession()
baseline = BaselineLearner()

cal.start(now_s=0.0)
for reading in sensor_stream():
    st = cal.feed(reading, reading.timestamp_s)
    if st["phase"] == "READY":
        b = cal.to_baseline()
        if b:
            baseline.b = b
            break
```

## Privacy

- Baseline stays **on-device** (SD / ESP32 flash)
- No upload required for calibration
- Compares live data to **personal** pattern, not a public dataset

## Not medical validation

Calibration personalizes screening thresholds. It does **not** replace clinical devices or diagnosis.
