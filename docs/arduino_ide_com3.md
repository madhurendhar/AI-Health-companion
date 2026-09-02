# Arduino IDE upload (COM3)

Use this if you prefer **Arduino IDE** instead of PlatformIO.

## 1. One-time: install ESP32 support

1. Open **Arduino IDE**
2. **File → Preferences**
3. **Additional boards manager URLs**, add:
   ```
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```
4. **Tools → Board → Boards Manager** → search **esp32** → install **esp32 by Espressif Systems**
5. Restart Arduino IDE

## 2. Generate the sketch folder

From project root (PowerShell):

```bat
cd C:\AI-Health-companion
.\.venv\Scripts\python.exe tools\prepare_arduino_sketch.py
.\.venv\Scripts\python.exe tools\export_esp_models.py
.\.venv\Scripts\python.exe tools\prepare_arduino_sketch.py
```

Second `prepare_arduino_sketch.py` refreshes ML headers into the sketch.

Sketch path:

```
C:\AI-Health-companion\firmware\arduino\AIHealthCompanion\AIHealthCompanion.ino
```

## 3. Edit WiFi and backend IP

Open in Notepad:

`firmware\arduino\AIHealthCompanion\companion_secrets.h`

```c
#define COMPANION_WIFI_SSID "your_wifi_name"
#define COMPANION_WIFI_PASS "your_wifi_password"
#define COMPANION_BACKEND_URL "http://192.168.1.XX:8080"
#define COMPANION_API_TOKEN "change-me-local-token"
#define COMPANION_LOCATION "Chennai"
```

- Replace `192.168.1.XX` with your PC IPv4 (`ipconfig` → Wi-Fi IPv4 Address)
- Token must match `.env` → `COMPANION_API_TOKEN`

## 4. Open sketch in Arduino IDE

1. **File → Open**
2. Select:
   `C:\AI-Health-companion\firmware\arduino\AIHealthCompanion\AIHealthCompanion.ino`

## 5. Board settings (important)

| Menu | Setting |
|------|---------|
| **Tools → Board** | **ESP32 Dev Module** |
| **Tools → Port** | **COM3** |
| **Tools → Upload Speed** | **115200** (if upload fails, try 921600) |
| **Tools → Flash Size** | **4MB (32Mb)** |
| **Tools → Partition Scheme** | **Default 4MB with spiffs** |
| **Tools → CPU Frequency** | 240 MHz |
| **Tools → Core Debug Level** | None |

## 6. Start backend on PC (same WiFi)

```bat
cd C:\AI-Health-companion
.\.venv\Scripts\activate
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8080
```

## 7. Upload to ESP32

1. Connect ESP32 USB → should show as **COM3**
2. Click **Upload** (→ arrow button)
3. Wait for `Hard resetting via RTS pin...`
4. **Tools → Serial Monitor** → **115200 baud**

Expected output:

```text
AI Health Companion ESP32 ready
Sensors: MAX30102 MLX90614 DHT22 MQ135
```

## 8. If upload fails on COM3

| Problem | Fix |
|---------|-----|
| Port not listed | Install CP210x or CH340 USB driver |
| `Failed to connect` | Hold **BOOT** button, click Upload, release when "Connecting..." |
| Wrong port | Device Manager → Ports → note COM number |
| `Sketch too big` | Flash Size = 4MB |
| Compile errors | Re-run `prepare_arduino_sketch.py` after code changes |

## 9. After changing firmware code

Whenever you edit files under `firmware/src/`:

```bat
python tools\prepare_arduino_sketch.py
python tools\export_esp_models.py
python tools\prepare_arduino_sketch.py
```

Then upload again from Arduino IDE.

## Wiring (same as PlatformIO)

| Sensor | ESP32 |
|--------|--------|
| MAX30102 / MLX90614 / I2C OLED | SDA **21**, SCL **22**, 3.3V, GND |
| DHT22 | GPIO **4** |
| MQ135 | GPIO **34** |
| Buzzer | GPIO **15** |
| LED | GPIO **2** |

Do **not** upload individual `.cpp` files — always open the **AIHealthCompanion** sketch folder and click **Upload**.
