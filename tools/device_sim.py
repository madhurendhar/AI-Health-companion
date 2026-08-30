"""Host-side device simulator. Mirrors firmware pipeline. DEMO MODE is explicit."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import httpx
from dotenv import load_dotenv

from companion_core.baseline import BaselineLearner
from companion_core.compact_tree import CompactTree
from companion_core.config import HEALTH
from companion_core.demo import demo_reading
from companion_core.features import FeatureExtractor
from companion_core.health_risk import ALERT_COPY, combine_tree_score, heuristic_risk, make_result
from companion_core.health_vector import health_vector
from companion_core.mq135 import Mq135Tracker
from companion_core.sd_store import PatientStore
from companion_core.validation import validate_reading

load_dotenv()


class CompanionPipeline:
    def __init__(self, sd_root: str, demo: bool):
        self.demo = demo
        self.extract = FeatureExtractor()
        self.baseline = BaselineLearner()
        self.mq = Mq135Tracker(warmup_samples=0 if demo else 40)
        self.store = PatientStore(sd_root)
        saved = self.store.read_baseline()
        if saved:
            self.baseline.load_dict(saved)
        self.tree = None
        p = Path("ai/health/models/health_tree.json")
        if p.exists():
            self.tree = CompactTree.load(p)
        self.prev_abnormal = False
        self.last_status = None

    def step(self, reading):
        reading.demo_mode = reading.demo_mode or self.demo
        rel, air, mq_state = self.mq.update(reading.mq135_raw if reading.mq135_raw is not None else 1000.0)
        if rel is not None:
            reading.mq135_relative = rel
        reading.mq_state = mq_state
        reading = validate_reading(reading)
        feats = self.extract.extract(reading, self.baseline.b, self.prev_abnormal)
        h_score, reason = heuristic_risk(feats, self.baseline.b)
        t_score = self.tree.predict_score(health_vector(feats)) if self.tree and feats.valid else None
        score = combine_tree_score(h_score, t_score)
        result = make_result(feats, self.baseline.b, score, reason, reading.demo_mode, t_score is not None)
        self.baseline.update(feats, score)
        self.store.write_baseline(self.baseline.to_dict())
        self.prev_abnormal = result.status.value in ("RECHECK", "ELEVATED")
        self.store.append_reading(
            {
                "timestamp_s": reading.timestamp_s,
                "hr": feats.hr,
                "spo2": feats.spo2,
                "temperature": feats.temperature,
                "ambient_temp": feats.ambient_temp,
                "humidity": feats.humidity,
                "mq135_relative": feats.mq135_relative,
                "hr_dev": feats.hr_dev,
                "spo2_dev": feats.spo2_dev,
                "temp_dev": feats.temp_dev,
                "signal_quality": feats.signal_quality,
                "risk_score": result.risk_score,
                "status": result.status.value,
            }
        )
        if self.last_status != result.status:
            self.store.append_event(reading.timestamp_s, "health_status", result.status.value)
            self.last_status = result.status
        snap = {
            "device_id": os.getenv("DEVICE_ID", "companion-01"),
            "demo_mode": reading.demo_mode,
            "health": {
                "hr": feats.hr,
                "spo2": feats.spo2,
                "temperature": feats.temperature,
                "status": result.status.value,
                "risk_score": result.risk_score,
                "risk_kind": "AI-DERIVED RISK",
                "measured": {
                    "hr": reading.hr_bpm,
                    "spo2": reading.spo2_pct,
                    "object_temp_c": reading.object_temp_c,
                    "kind": "MEASURED SENSOR DATA" if not reading.demo_mode else "DEMO MODE / SIMULATED DATA",
                },
                "baseline": self.baseline.to_dict(),
                "signal_quality": feats.signal_quality,
                "reason": result.reason,
                "alert": ALERT_COPY[result.status],
                "edge_ai": True,
                "model_name": result.model_name,
                "model_version": result.model_version,
            },
            "environment": {
                "ambient_temp": feats.ambient_temp,
                "humidity": feats.humidity,
                "mq135_relative": feats.mq135_relative,
                "air_status": air.value,
                "dht_state": reading.dht_state.value,
                "mq_state": reading.mq_state.value,
            },
            "system": {
                "sd_ok": self.store.ok,
                "network": "ONLINE",
                "edge_ai": True,
                "offline_health": True,
            },
        }
        return result, snap, air


def post_snapshot(snap: dict):
    url = os.getenv("BACKEND_URL", "http://127.0.0.1:8080") + "/device/status"
    token = os.getenv("COMPANION_API_TOKEN", "change-me-local-token")
    try:
        httpx.post(url, json=snap, headers={"X-Api-Token": token}, timeout=5.0)
        return True
    except Exception:
        return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scenario", default="normal")
    p.add_argument("--steps", type=int, default=25)
    p.add_argument("--offline", action="store_true")
    p.add_argument("--sd", default="data/runtime/sd")
    args = p.parse_args()
    pipe = CompanionPipeline(args.sd, demo=True)
    print("DEMO MODE / SIMULATED DATA scenario=", args.scenario)
    net_ok = True
    for i in range(args.steps):
        r = demo_reading(time.time(), args.scenario)
        result, snap, air = pipe.step(r)
        if args.offline:
            net_ok = False
        else:
            net_ok = post_snapshot(snap)
        print(
            f"i={i} HEALTH {result.status.value} score={result.risk_score:.3f} "
            f"HR={result.features.hr} SpO2={result.features.spo2} AIR={air.value} net={net_ok}"
        )
    print("SD", Path(args.sd) / "patient")


if __name__ == "__main__":
    main()
