# Finish / run the project

## Status

| Piece | Status |
| --- | --- |
| PlatformIO firmware build | **SUCCESS** (SparkFun MAX3010x + Adafruit MLX/DHT + MQ135) |
| Upload to ESP32 | Plug board in USB, then upload (COM port was not available) |
| Circuit / pins | `docs/circuit.md`, `firmware/include/companion/pins.h` |
| Backend flood API | Optional — start when WiFi secrets are set |

## Upload now

1. Connect ESP32 USB cable (you should see e.g. **COM3**, not Bluetooth COM5/COM6).
2. In a terminal:

```bat
cd C:\AI-Health-companion\firmware
python -m platformio run -t upload
python -m platformio device monitor
```

Or open `firmware` in PlatformIO IDE → **Upload** → **Serial Monitor** (115200).

## Wiring (modules)

| Module | ESP32 |
| --- | --- |
| MAX30102 / MLX90614 | 3.3V, GND, SDA **21**, SCL **22** |
| DHT22 | 3.3V, GND, DATA **4** |
| MQ135 | 5V, GND, AO→**10k→GPIO34→10k→GND** |
| Buzzer (optional) | SIG **15** |

## Serial after upload

```
MAX30102: SparkFun library OK
MLX90614: Adafruit library OK
MQ135: ADC GPIO 34 (10k+10k divider from AO)
Ready. Place finger on MAX30102.
```

Pages every 3 s: HEALTH → ENVIRONMENT → FLOOD  
Keys: `D` demo flood, `L` live, `C` calibrate, `S` skip cal

## WiFi / flood (optional)

Edit `firmware/include/companion_secrets.h` (gitignored), then:

```bat
cd C:\AI-Health-companion
.\.venv\Scripts\activate
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8080
```
