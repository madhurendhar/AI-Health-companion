from ai.flood.train import evaluate, leakage_safe_split, load_dataset
import joblib
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent


def main():
    model = joblib.load(ROOT / "models" / "selected.joblib")
    df = load_dataset()
    _, test = leakage_safe_split(df)
    print(json.dumps(evaluate(model, test), indent=2))


if __name__ == "__main__":
    main()
