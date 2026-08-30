from ai.health.train import evaluate, leakage_safe_split, load_dataset
import joblib
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent


def main():
    model = joblib.load(ROOT / "models" / "selected.joblib")
    df = load_dataset()
    _, test = leakage_safe_split(df)
    report = evaluate(model, test)
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
