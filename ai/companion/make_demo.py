"""DEMO DATA — India disaster-context scenarios for pipeline testing only."""

from __future__ import annotations

import csv
import random
from pathlib import Path

from ai.companion.features import ENV_FEATURE_NAMES, heat_index_approx

OUT = Path(__file__).resolve().parent / "data" / "demo_environment.csv"


def row(scenario: str, i: int) -> dict:
    rng = random.Random(hash(scenario) * 1000 + i)
    if scenario == "normal":
        t, h, mq, r1, r24, r72, inten, trend = 30.0, 65.0, 1.0, 0.5, 8.0, 25.0, 0.5, 0.0
        label = 0
    elif scenario == "heat_wave":
        t, h = rng.uniform(38, 44), rng.uniform(55, 75)
        mq, r1, r24, r72, inten, trend = 1.2, 0.0, 2.0, 10.0, 0.0, 0.5
        label = 2
    elif scenario == "pollution":
        t, h = 32.0, 55.0
        mq = rng.uniform(2.2, 3.5)
        r1, r24, r72, inten, trend = 0.0, 5.0, 15.0, 0.0, 0.0
        label = 1
    elif scenario == "flood_rain":
        t, h, mq = 28.0, 88.0, 1.1
        r1, r24, r72 = rng.uniform(8, 20), rng.uniform(70, 120), rng.uniform(150, 220)
        inten, trend = rng.uniform(10, 25), rng.uniform(3, 8)
        label = 2
    elif scenario == "compound":
        t, h = rng.uniform(36, 40), rng.uniform(70, 85)
        mq = rng.uniform(1.8, 2.5)
        r1, r24, r72 = rng.uniform(5, 15), rng.uniform(40, 80), rng.uniform(90, 140)
        inten, trend = rng.uniform(8, 18), rng.uniform(2, 6)
        label = 2
    else:
        t, h, mq, r1, r24, r72, inten, trend = 30.0, 65.0, 1.0, 0.0, 5.0, 20.0, 0.0, 0.0
        label = 0

    hi = heat_index_approx(t, h)
    return {
        "data_kind": "DEMO DATA",
        "scenario": scenario,
        "ambient_temp_c": round(t, 2),
        "humidity": round(h, 2),
        "heat_index": round(hi, 2),
        "mq135_relative": round(mq, 3),
        "rain_1h": round(r1, 2),
        "rain_24h": round(r24, 2),
        "rain_72h": round(r72, 2),
        "intensity": round(inten, 2),
        "trend": round(trend, 2),
        "label": label,
        "label_name": ["LOW", "WATCH", "HIGH"][label],
    }


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    scenarios = ["normal", "heat_wave", "pollution", "flood_rain", "compound"]
    rows = []
    for s in scenarios:
        n = 40 if s == "normal" else 25
        for i in range(n):
            rows.append(row(s, i))
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote", OUT, len(rows), "DEMO DATA")


if __name__ == "__main__":
    main()
