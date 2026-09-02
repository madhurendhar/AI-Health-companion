"""Build Arduino IDE sketch folder from PlatformIO firmware sources."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FW = ROOT / "firmware"
OUT = FW / "arduino" / "AIHealthCompanion"

# Only .cpp files required by the main firmware (skip optional robot/audio).
CPP_MAP = {
    FW / "src" / "display" / "oled.cpp": OUT / "oled.cpp",
    FW / "src" / "processing" / "features.cpp": OUT / "features.cpp",
    FW / "src" / "processing" / "calibration.cpp": OUT / "calibration.cpp",
    FW / "src" / "processing" / "flood_sm.cpp": OUT / "flood_sm.cpp",
    FW / "src" / "processing" / "health_engine.cpp": OUT / "health_engine.cpp",
    FW / "src" / "network" / "wifi_cloud.cpp": OUT / "wifi_cloud.cpp",
    FW / "src" / "storage" / "sd_manager.cpp": OUT / "sd_manager.cpp",
    FW / "src" / "sensors" / "max30102.cpp": OUT / "max30102.cpp",
    FW / "src" / "sensors" / "mlx90614.cpp": OUT / "mlx90614.cpp",
    FW / "src" / "sensors" / "dht22.cpp": OUT / "dht22.cpp",
    FW / "src" / "sensors" / "mq135.cpp": OUT / "mq135.cpp",
}

README = """AI Health Companion — Arduino IDE sketch (ESP32 ONLY)

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
"""


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    ino_src = FW / "src" / "main.cpp"
    ino_dst = OUT / "AIHealthCompanion.ino"
    ino_dst.write_text(ino_src.read_text(encoding="utf-8"), encoding="utf-8")

    for src, dst in CPP_MAP.items():
        if src.exists():
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    copy_tree(FW / "include" / "companion", OUT / "companion")

    secrets = FW / "include" / "companion_secrets.h"
    if not secrets.exists():
        secrets = FW / "include" / "companion_secrets.example.h"
    (OUT / "companion_secrets.h").write_text(secrets.read_text(encoding="utf-8"), encoding="utf-8")

    (OUT / "README.txt").write_text(README, encoding="utf-8")

    # Remove stale optional files from older prepares
    for stale in ("motors.cpp", "voice.cpp"):
        p = OUT / stale
        if p.exists():
            p.unlink()

    print(f"Arduino sketch ready: {OUT}")
    print("Board: ESP32 Dev Module | Port: COM3")
    print("Open AIHealthCompanion.ino and Upload")


if __name__ == "__main__":
    main()
