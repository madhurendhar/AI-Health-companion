"""End-to-end flood smoke test. Usage: python tools/flood_smoke.py [--live]"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import httpx


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--live", action="store_true", help="use NWDP (COMPANION_DEMO_MODE=false)")
    p.add_argument("--url", default=os.getenv("BACKEND_URL", "http://127.0.0.1:8080"))
    p.add_argument("--location", default="Chennai")
    args = p.parse_args()

    demo_q = "" if args.live else ""
    if args.live:
        os.environ["COMPANION_DEMO_MODE"] = "false"
        os.environ["RAINFALL_PROVIDER"] = "nwdp"

    base = args.url.rstrip("/")
    for path in ("/data-status", f"/rainfall?location={args.location}", f"/flood/status?location={args.location}"):
        r = httpx.get(base + path, timeout=30)
        print(path, r.status_code)
        if r.status_code != 200:
            print(r.text[:200])
            sys.exit(1)
        data = r.json()
        if "flood" in path:
            print("  risk:", data.get("status"), "source:", data.get("source"), "data:", data.get("data_status"))
        elif "rainfall" in path:
            print("  source:", data.get("source"), "tail:", data.get("hourly_tail_mm"))
        else:
            print("  locations:", data.get("supported_locations"))

    print("OK")


if __name__ == "__main__":
    main()
