# Testing

```
pytest
```

Coverage (host):

- sensor validation / invalid rejection
- health multi-feature risk (not HR>100)
- baseline skip on abnormal
- flood windows + state hysteresis
- SD append/read
- device pipeline demo scenarios + offline SD
- API auth, privacy flags, demo flood
- secret scan

Firmware: `pip install -r requirements-dev.txt` then `cd firmware && pio run` (RAM ~15%, Flash ~77% on esp32dev). On-hardware: serial `D` demo, `L` live, `f/b/s` motors.

Live Open-Meteo: `pytest -m integration` (network required). CI runs unit + integration + firmware build.

AI: `python -m ai.health.train` then `evaluate` / `export`. Reports marked DEMO DATA / PENDING validation.
