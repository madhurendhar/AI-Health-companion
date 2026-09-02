AI Health Companion — Arduino IDE sketch (ESP32 ONLY)

REQUIRED before Upload:
1. File -> Preferences -> Additional boards manager URLs:
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
2. Tools -> Board -> Boards Manager -> install "esp32" by Espressif Systems
3. Tools -> Board -> ESP32 Dev Module
4. Tools -> Port -> COM3 (your ESP32 port)
5. Tools -> Flash Size -> 4MB (32Mb)

Edit companion_secrets.h (WiFi + backend URL) before upload.

Regenerate this folder after code changes:
  python tools/prepare_arduino_sketch.py
