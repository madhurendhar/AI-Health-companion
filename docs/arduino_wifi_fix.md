# Arduino IDE — fix "WiFi.h: No such file or directory"

This error means Arduino is **not** using the **ESP32** board package.

`WiFi.h` exists only for **ESP32** (and ESP8266), **not** for Arduino Uno/Nano.

## Fix (5 minutes)

### Step 1 — Add ESP32 board URL

**File → Preferences → Additional boards manager URLs** — paste:

```
https://espressif.github.io/arduino-esp32/package_esp32_index.json
```

Click OK.

### Step 2 — Install ESP32 package

**Tools → Board → Boards Manager**

Search: `esp32`

Install: **esp32** by **Espressif Systems** (version 2.x or 3.x)

Wait until install finishes (can take several minutes).

### Step 3 — Select correct board

| Setting | Value |
|---------|--------|
| **Tools → Board** | **ESP32 Dev Module** |
| **Tools → Port** | **COM3** |
| **Tools → Upload Speed** | 115200 |
| **Tools → Flash Size** | **4MB (32Mb)** |

Do **not** use Arduino Uno, Nano, or Mega.

### Step 4 — Regenerate sketch and upload

```bat
cd C:\AI-Health-companion
.\.venv\Scripts\python.exe tools\prepare_arduino_sketch.py
```

Open:

`firmware\arduino\AIHealthCompanion\AIHealthCompanion.ino`

Click **Upload**.

---

## Verify board is ESP32

After selecting ESP32 Dev Module, the bottom-right of Arduino IDE should show something like:

`ESP32 Dev Module on COM3`

If it says `Arduino Uno on COM3`, WiFi.h will always fail.

---

## Sketch location (full code)

All files are in:

```
C:\AI-Health-companion\firmware\arduino\AIHealthCompanion\
  AIHealthCompanion.ino      ← main program
  companion_secrets.h        ← WiFi + backend URL
  *.cpp                      ← sensors, ML, WiFi
  companion\                 ← headers + ML trees
```

You upload the **whole folder** by opening the `.ino` file — not individual `.cpp` files.
