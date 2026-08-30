"""Generate clearly labelled DEMO DATA for software tests. Not medical data."""

from pathlib import Path
import csv
import random

OUT = Path(__file__).resolve().parents[1] / "data" / "demo_health.csv"
FEATURE_COLS = [
    "hr",
    "spo2",
    "temperature",
    "hr_trend",
    "spo2_trend",
    "temperature_trend",
    "signal_quality",
    "hr_dev",
    "spo2_dev",
    "temp_dev",
    "persistence",
    "ambient_temp",
    "humidity",
    "mq135_relative",
]


def row(subject, seed_off, abnormal: bool):
    rng = random.Random(subject * 1000 + seed_off)
    if not abnormal:
        hr, spo2, temp = rng.uniform(62, 82), rng.uniform(96.5, 99.5), rng.uniform(35.8, 36.9)
        hr_dev, spo2_dev, temp_dev = rng.uniform(-0.4, 0.4), rng.uniform(-0.2, 0.3), rng.uniform(-0.3, 0.3)
        pers = rng.uniform(0, 0.15)
        label = 0
    else:
        hr, spo2, temp = rng.uniform(105, 130), rng.uniform(86, 93), rng.uniform(37.6, 39.0)
        hr_dev, spo2_dev, temp_dev = rng.uniform(1.2, 2.8), rng.uniform(0.8, 2.0), rng.uniform(0.9, 2.2)
        pers = rng.uniform(0.5, 1.0)
        label = 1
    return {
        "data_kind": "DEMO DATA",
        "subject_id": f"demo-{subject}",
        "ts_index": seed_off,
        "hr": round(hr, 2),
        "spo2": round(spo2, 2),
        "temperature": round(temp, 2),
        "hr_trend": round(rng.uniform(-0.5, 1.5) if abnormal else rng.uniform(-0.2, 0.2), 3),
        "spo2_trend": round(rng.uniform(-0.8, 0.1) if abnormal else rng.uniform(-0.1, 0.1), 3),
        "temperature_trend": round(rng.uniform(0.0, 0.3) if abnormal else rng.uniform(-0.05, 0.05), 3),
        "signal_quality": round(rng.uniform(0.7, 0.95), 3),
        "hr_dev": round(hr_dev, 3),
        "spo2_dev": round(spo2_dev, 3),
        "temp_dev": round(temp_dev, 3),
        "persistence": round(pers, 3),
        "ambient_temp": round(rng.uniform(26, 34), 2),
        "humidity": round(rng.uniform(50, 90), 2),
        "mq135_relative": round(rng.uniform(0.9, 1.6), 3),
        "label": label,
    }


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for sub in range(12):
        for i in range(18):
            rows.append(row(sub, i, abnormal=False))
        for i in range(18, 28):
            rows.append(row(sub, i, abnormal=True))
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote", OUT, "rows", len(rows), "DEMO DATA")


if __name__ == "__main__":
    main()
