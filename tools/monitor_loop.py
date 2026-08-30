"""Continuous NWDP realtime monitor — compares live vs historical baseline."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("COMPANION_DEMO_MODE", "false")
os.environ.setdefault("RAINFALL_PROVIDER", "nwdp")

from backend.flood_service import FloodEngine
from backend.rainfall import build_provider


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--location", default="Chennai")
    p.add_argument("--interval", type=int, default=300, help="poll seconds (default 5 min)")
    p.add_argument("--once", action="store_true")
    args = p.parse_args()

    eng = FloodEngine(build_provider(demo=False))
    print(f"NWDP realtime monitor — {args.location} (REAL DATA, no synthetic)")
    while True:
        try:
            r = eng.evaluate(args.location, demo=False)
            print(
                f"[{time.strftime('%H:%M:%S')}] {r['status']} score={r['risk_score']:.3f} "
                f"rain24={r['rainfall']['24h']:.1f}mm source={r['source']} "
                f"trend_escalating={r.get('monitor_trend', {}).get('escalating')}"
            )
            if r.get("historical_comparison"):
                hc = r["historical_comparison"]
                for a in hc.get("anomalies", []):
                    if a["level"] != "normal":
                        print(f"  ANOMALY {a['window']}: {a['current_mm']}mm vs p90={a['historical_p90']} ({a['level']})")
        except Exception as exc:
            print(f"ERROR: {exc}")
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
