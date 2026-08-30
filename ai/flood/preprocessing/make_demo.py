from pathlib import Path
import csv
import random

OUT = Path(__file__).resolve().parents[1] / "data" / "demo_flood.csv"
LOCS = ["Chennai", "Mumbai", "Kochi"]
FEATS = [
    "rain_1h",
    "rain_3h",
    "rain_6h",
    "rain_12h",
    "rain_24h",
    "rain_48h",
    "rain_72h",
    "intensity",
    "trend",
]


def sample(loc, i, flood: bool):
    rng = random.Random(sum(ord(c) for c in loc) * 1000 + i + (500 if flood else 0))
    if not flood:
        r24 = rng.uniform(0, 25)
        intensity = rng.uniform(0, 4)
        label = 0
    else:
        r24 = rng.uniform(70, 180)
        intensity = rng.uniform(12, 40)
        label = 1
    r1 = min(r24, intensity)
    r3 = min(r24, r1 * rng.uniform(2.2, 3.0))
    r6 = min(r24 * 1.1, r3 * rng.uniform(1.5, 2.2))
    r12 = min(r24 * 1.05, r6 * rng.uniform(1.3, 1.8))
    r48 = r24 + rng.uniform(0, 40 if flood else 10)
    r72 = r48 + rng.uniform(0, 50 if flood else 15)
    return {
        "data_kind": "DEMO DATA",
        "location": loc,
        "date": f"2020-{(i % 12)+1:02d}-{(i % 27)+1:02d}",
        "rain_1h": round(r1, 2),
        "rain_3h": round(r3, 2),
        "rain_6h": round(r6, 2),
        "rain_12h": round(r12, 2),
        "rain_24h": round(r24, 2),
        "rain_48h": round(r48, 2),
        "rain_72h": round(r72, 2),
        "intensity": round(intensity, 2),
        "trend": round(rng.uniform(-1, 8 if flood else 1), 2),
        "label": label,
    }


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for loc in LOCS:
        for i in range(40):
            rows.append(sample(loc, i, flood=False))
        for i in range(40, 55):
            rows.append(sample(loc, i, flood=True))
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote", OUT, "DEMO DATA", len(rows))


if __name__ == "__main__":
    main()
