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

## Health phase 2 (not built yet)

Sensors: MAX30102, MLX90614, DHT22, MQ135. See `docs/architecture.md`.

## Firmware (ESP32)

Install [PlatformIO](https://platformio.org/), copy `firmware/include/companion_secrets.example.h` values into `companion_secrets.h`, then:

```bat
cd firmware
pio run
pio run -t upload
```

Host in this workspace: install dev deps and build firmware:

```bat
pip install -r requirements-dev.txt
cd firmware
pio run
```

RAM ~15%, Flash ~77% on esp32dev (4MB). Live Open-Meteo: set `COMPANION_DEMO_MODE=false` in `.env`, then `pytest -m integration`.

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
