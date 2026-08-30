"""Health screening ML pipeline. DEMO DATA only unless a real labelled set is provided.

Real model validation: PENDING (no labelled clinical dataset in this repository).
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.tree import DecisionTreeClassifier

from companion_core.config import HEALTH

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "demo_health.csv"
MODELS = ROOT / "models"
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


def load_dataset(path: Path | None = None) -> pd.DataFrame:
    df = pd.read_csv(path or DATA)
    if "data_kind" not in df.columns or not (df["data_kind"] == "DEMO DATA").all():
        raise ValueError("Health CSV must be labelled DEMO DATA in column data_kind")
    return df


def leakage_safe_split(df: pd.DataFrame, seed: int = 7):
    """Split by subject_id so the same person never appears in train and test."""
    gss = GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=seed)
    tr, te = next(gss.split(df, df["label"], df["subject_id"]))
    return df.iloc[tr], df.iloc[te]


def train_candidates(train: pd.DataFrame):
    X = train[FEATURE_COLS].to_numpy()
    y = train["label"].to_numpy()
    models = {
        "decision_tree": DecisionTreeClassifier(max_depth=6, min_samples_leaf=8, random_state=7),
        "random_forest": RandomForestClassifier(
            n_estimators=40, max_depth=6, min_samples_leaf=6, random_state=7
        ),
    }
    try:
        from xgboost import XGBClassifier

        models["xgboost"] = XGBClassifier(
            n_estimators=40, max_depth=4, learning_rate=0.1, eval_metric="logloss"
        )
    except Exception:
        pass
    fitted = {}
    for name, m in models.items():
        m.fit(X, y)
        fitted[name] = m
    return fitted


def evaluate(model, test: pd.DataFrame) -> dict:
    X = test[FEATURE_COLS].to_numpy()
    y = test["label"].to_numpy()
    pred = model.predict(X)
    proba = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else pred
    return {
        "accuracy": float(accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, proba)) if len(np.unique(y)) > 1 else None,
        "confusion_matrix": confusion_matrix(y, pred).tolist(),
        "false_positives": int(((pred == 1) & (y == 0)).sum()),
        "false_negatives": int(((pred == 0) & (y == 1)).sum()),
        "n_test": int(len(y)),
        "note": "DEMO DATA software test metrics. NOT medical validation.",
    }


def main():
    MODELS.mkdir(parents=True, exist_ok=True)
    df = load_dataset()
    train, test = leakage_safe_split(df)
    fitted = train_candidates(train)
    reports = {}
    best_name, best_recall, best_model = None, -1.0, None
    for name, m in fitted.items():
        reports[name] = evaluate(m, test)
        rec = reports[name]["recall"]
        if rec > best_recall or (rec == best_recall and reports[name]["f1"] > reports.get(best_name, {}).get("f1", -1)):
            best_name, best_recall, best_model = name, rec, m
    out = {
        "selected": best_name,
        "reports": reports,
        "feature_schema_version": HEALTH.feature_schema_version,
        "model_name": HEALTH.model_name,
        "model_version": HEALTH.model_version,
        "validation": "PENDING — demo software metrics only",
        "data_kind": "DEMO DATA",
    }
    (MODELS / "eval_report.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    import joblib

    joblib.dump(best_model, MODELS / "selected.joblib")
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
