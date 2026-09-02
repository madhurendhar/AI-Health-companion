"""Export sklearn trees to ESP32 C headers (health + flood)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = {**os.environ, "PYTHONPATH": str(ROOT)}


def main():
    steps = [
        [sys.executable, str(ROOT / "ai" / "health" / "export.py")],
        [sys.executable, str(ROOT / "ai" / "flood" / "export.py")],
    ]
    for cmd in steps:
        print("running", " ".join(cmd))
        subprocess.check_call(cmd, cwd=str(ROOT), env=ENV)
    print("ESP32 headers updated:")
    print("  firmware/include/companion/health_tree_model.h")
    print("  firmware/include/companion/flood_tree_model.h")
    print("Upload: cd firmware && pio run -t upload")


if __name__ == "__main__":
    main()
