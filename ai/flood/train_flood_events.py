"""Train flood EVENT model on real IFI labels + NWDP rainfall (temporal split)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from companion_core.flood_features import FEATURE_NAMES

DATASET = ROOT / "data" / "processed" / "flood" / "chennai_event_dataset.parquet"
REPORT = ROOT / "reports" / "flood_event_model_results.json"
MODEL_DIR = ROOT / "ai" / "flood" / "models"
TARGET = "flood_event_next_day"


def temporal_split(df: pd.DataFrame, test_frac: float = 0.25):
    df = df.sort_values("date")
    cut = int(len(df) * (1 - test_frac))
    return df.iloc[:cut].copy(), df.iloc[cut:].copy()


def train_and_report(df: pd.DataFrame) -> dict:
    train, test = temporal_split(df)
    Xtr, ytr = train[FEATURE_NAMES].to_numpy(), train[TARGET].to_numpy()
    Xte, yte = test[FEATURE_NAMES].to_numpy(), test[TARGET].to_numpy()

    models = {
        "logistic_regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "decision_tree": DecisionTreeClassifier(max_depth=5, min_samples_leaf=4, class_weight="balanced"),
        "random_forest": RandomForestClassifier(
            n_estimators=80, max_depth=6, min_samples_leaf=3, class_weight="balanced", random_state=7
        ),
    }

    reports = {}
    best_name, best_f1, best_model = None, -1.0, None
    for name, m in models.items():
        m.fit(Xtr, ytr)
        pred = m.predict(Xte)
        proba = m.predict_proba(Xte)[:, 1] if hasattr(m, "predict_proba") else pred.astype(float)
        reports[name] = {
            "accuracy": float(accuracy_score(yte, pred)),
            "precision": float(precision_score(yte, pred, zero_division=0)),
            "recall": float(recall_score(yte, pred, zero_division=0)),
            "f1": float(f1_score(yte, pred, zero_division=0)),
            "roc_auc": float(roc_auc_score(yte, proba)) if len(np.unique(yte)) > 1 else None,
            "confusion_matrix": confusion_matrix(yte, pred).tolist(),
            "false_positives": int(((pred == 1) & (yte == 0)).sum()),
            "false_negatives": int(((pred == 0) & (yte == 1)).sum()),
            "n_test": int(len(yte)),
            "n_test_positives": int(yte.sum()),
        }
        if reports[name]["f1"] > best_f1:
            best_name, best_f1, best_model = name, reports[name]["f1"], m

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, MODEL_DIR / "flood_event.joblib")

    out = {
        "selected": best_name,
        "reports": reports,
        "target": TARGET,
        "features": FEATURE_NAMES,
        "data_kind": "REAL_FLOOD_EVENT_LABELS",
        "label_source": "IFI-Impacts v3 (Chennai)",
        "rainfall_source": "NWDP",
        "split": "temporal (earlier train, later test)",
        "n_train": len(train),
        "n_test": len(test),
        "train_positives": int(ytr.sum()),
        "test_positives": int(yte.sum()),
        "validation": "Honest metrics on held-out future dates — limited overlap window (NWDP 2021-2023 vs IFI events)",
        "model_path": str(MODEL_DIR / "flood_event.joblib"),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return out


def main():
    if not DATASET.exists():
        raise SystemExit("Run ai/flood/build_event_dataset.py first")
    df = pd.read_parquet(DATASET)
    if df[TARGET].sum() == 0:
        raise SystemExit("No positive flood event labels in dataset overlap window")
    train_and_report(df)


if __name__ == "__main__":
    main()
