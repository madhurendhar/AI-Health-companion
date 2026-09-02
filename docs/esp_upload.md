# ESP32 upload guide — sensors + edge ML

Complete firmware lives in `firmware/`. It reads **MAX30102, MLX90614, DHT22, MQ135**, runs **compact ML trees** on-device, and polls the backend for **flood early-warning**.

## 1. Wire hardware

See `docs/hardware.md`:

| Sensor | Bus | ESP32 pin |
|--------|-----|-----------|
| MAX30102 | I2C | SDA 21, SCL 22 |
| MLX90614 | I2C | same bus, addr 0x5A |
| DHT22 | 1-wire | GPIO 4 |
| MQ135 | ADC | GPIO 34 |
| SD card | SPI | CS GPIO 5 |
| OLED (optional) | I2C | 0x3C |
| Buzzer | digital | GPIO 15 |
| LED | digital | GPIO 2 |

## 2. WiFi + backend secrets

```bat
copy firmware\include\companion_secrets.example.h firmware\include\companion_secrets.h
```

Edit `companion_secrets.h`:

```c
#define COMPANION_WIFI_SSID "your_wifi"
#define COMPANION_WIFI_PASS "your_password"
#define COMPANION_BACKEND_URL "http://192.168.1.10:8080"
#define COMPANION_API_TOKEN "change-me-local-token"
#define COMPANION_LOCATION "Chennai"
```

Start backend on your PC (same WiFi):

```bat
cd C:\AI-Health-companion
.\.venv\Scripts\activate
set COMPANION_DEMO_MODE=false
uvicorn backend.app:app --host 0.0.0.0 --port 8080
```

## 3. Export ML models to ESP32 headers

Trees are tiny C arrays (no TensorFlow on ESP32):

```bat
cd C:\AI-Health-companion
.\.venv\Scripts\python.exe tools\export_esp_models.py
```

This writes:

- `firmware/include/companion/health_tree_model.h` — 14-feature health screening tree
- `firmware/include/companion/flood_tree_model.h` — 9-feature rainfall tree (rain24 from backend)

Re-run after retraining:

```bat
python ai\health\train.py
python ai\health\export.py
python ai\flood\train_nwdp.py
python ai\flood\export.py
```

Or use `tools\export_esp_models.py` for both.

## 4. Build and upload

Install [PlatformIO](https://platformio.org/) (VS Code extension or CLI).

```bat
cd C:\AI-Health-companion\firmware
pio run
pio run -t upload
pio device monitor
```

Expected serial output:

```text
AI Health Companion ESP32 ready
Sensors: MAX30102 MLX90614 DHT22 MQ135
Edge ML: health_tree + flood_tree
Starting 5-min baseline calibration — place finger on MAX30102
```

## 5. First boot — baseline calibration

1. Place finger on **MAX30102**; point **MLX90614** at forehead/wrist.
2. Hold still ~5 minutes (40 good samples).
3. Baseline saved to SD: `/patient/baseline.json`.
4. Health ML compares live readings vs **your** baseline (no cloud dataset).

Press **C** in serial monitor to recalibrate.

## 6. Runtime behavior

| Subsystem | On ESP32 | ML |
|-----------|----------|-----|
| Health | MAX30102 + MLX90614 + DHT + MQ135 | `health_tree` + heuristic |
| Environment | DHT22 + MQ135 warm-up | rules |
| Flood | WiFi → `/flood/status` | backend NWDP + optional `flood_tree` |

OLED/serial cycles: **Health → Environment → Flood** every few seconds.

Serial keys:

- `D` — demo flood data from backend
- `L` — live NWDP flood data
- `C` — restart baseline calibration

## 7. Flash / RAM

Typical build: ~70–75% flash, ~14–16% RAM on ESP32 dev board (4 MB flash).

## 8. Troubleshooting

| Issue | Fix |
|-------|-----|
| MAX30102 init failed | Check I2C wiring, 3.3 V, pull-ups |
| DHT22 errors | GPIO 4, 10k pull-up, 2 s read interval |
| WiFi offline | SSID/password, 2.4 GHz network |
| Flood OFFLINE | Backend URL must be `http://PC_IP:8080`, not localhost |
| HEALTH INSUFFICIENT | Complete calibration; improve finger placement |
| SD optional | Device works without SD; baseline not persisted |

## 9. What runs where

```text
ESP32 (edge)                    Backend (optional WiFi)
─────────────                   ─────────────────────
MAX30102 → HR/SpO2              NWDP rainfall API
MLX90614 → temp                 Historical percentiles
DHT22 / MQ135 → env             Flood event IFI labels
health_tree (14 feat)           Full flood event model
flood_tree (rain24 hint)        Dashboard / monitor
Personal baseline on SD
```

**No external health dataset required** for on-device operation — see `docs/health_calibration.md`.
