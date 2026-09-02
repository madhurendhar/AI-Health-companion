# Flood Early-Warning System (+ Health Companion — phase 2)

**Current phase: FLOOD SUBSYSTEM.** Health sensors/AI are intentionally not active in firmware.

Location-specific flood **early-risk** (LOW / WATCH / HIGH). Not guaranteed flood detection.

## Flood quick start

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python ai\flood\data\ingest_nwdp.py
python ai\flood\baseline.py
pytest
set COMPANION_DEMO_MODE=false
set RAINFALL_PROVIDER=nwdp
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8080
```

```bat
python tools\flood_smoke.py --live
pytest -m integration
```

Dashboard: http://127.0.0.1:8080 (Chennai NWDP, Kanyakumari Open-Meteo fallback)

## What runs where (flood)

| Function | Where |
| --- | --- |
| NWDP rainfall (Chennai) | Backend → NWDP API |
| Rainfall fallback (Kanyakumari) | Backend → Open-Meteo |
| Flood risk (baseline + heuristic + ML) | Backend |
| LOW / WATCH / HIGH | ESP32 OLED / LED / buzzer via backend poll |

## Health phase 2

Sensors: MAX30102, MLX90614, DHT22, MQ135. Firmware + on-device ML trees implemented — see `docs/esp_upload.md` and `docs/health_calibration.md`.

**Firmware:** Full ESP32 build with all 4 sensors + edge ML trees + flood WiFi poll. See `docs/esp_upload.md`.

## Firmware (ESP32) — sensors + ML upload

```bat
copy firmware\include\companion_secrets.example.h firmware\include\companion_secrets.h
REM edit WiFi + backend URL in companion_secrets.h

.\.venv\Scripts\python.exe tools\export_esp_models.py

cd firmware
pio run -t upload
pio device monitor
```

Complete guide: **`docs/esp_upload.md`**

## Docs

- `docs/architecture.md`
- `docs/hardware.md`
- `docs/health_ai.md`
- `docs/flood_ai.md`
- `docs/privacy.md`
- `docs/medical_validity.md`
- `docs/deployment.md`
- `docs/testing.md`
- `docs/implementation_state.md`
