"""
Companion AI training — Problem 26181 aligned.

Models:
  1. health_screening  → abnormal pattern (binary, demo labels)
  2. env_disaster      → LOW/WATCH/HIGH environmental risk (demo labels)

NOT medical or operational disaster validation without real labelled datasets.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ai.companion.features import ENV_FEATURE_NAMES, HEALTH_FEATURE_NAMES

MODELS = Path(__file__).resolve().parent / "models"
REPORT = ROOT / "reports" / "companion_model_results.json"


def _metrics(y_true, y_pred, labels=None) -> dict:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
        "n_test": int(len(y_true)),
    }


def _train_candidates(X, y, multiclass: bool = False):
    cw = "balanced"
    models = {
        "logistic_regression": LogisticRegression(max_iter=800, class_weight=cw),
        "decision_tree": DecisionTreeClassifier(max_depth=6, min_samples_leaf=6, class_weight=cw, random_state=7),
        "random_forest": RandomForestClassifier(n_estimators=50, max_depth=6, min_samples_leaf=5, class_weight=cw, random_state=7),
    }
    fitted = {}
    for name, m in models.items():
        m.fit(X, y)
        fitted[name] = m
    return fitted


def _select_best(reports: dict, fitted: dict, prefer_high_recall: bool = True):
    best_name, best_score, best_model = None, -1.0, None
    for name, m in fitted.items():
        rec = reports[name].get("recall_macro", reports[name].get("recall", 0))
        f1 = reports[name].get("f1_macro", reports[name].get("f1", 0))
        score = rec if prefer_high_recall else f1
        if score > best_score or (score == best_score and f1 > reports.get(best_name, {}).get("f1_macro", -1)):
            best_name, best_score, best_model = name, score, m
    return best_name, best_model


def train_health() -> dict:
    from ai.health.train import FEATURE_COLS, load_dataset, leakage_safe_split, evaluate

    df = load_dataset()
    train, test = leakage_safe_split(df)
    Xtr, ytr = train[FEATURE_COLS].to_numpy(), train["label"].to_numpy()
    fitted = _train_candidates(Xtr, ytr)
    reports = {n: evaluate(m, test) for n, m in fitted.items()}
    best_name, best_model = _select_best(reports, fitted)
    import joblib

    joblib.dump(best_model, MODELS / "health_selected.joblib")
    joblib.dump(best_model, ROOT / "ai" / "health" / "models" / "selected.joblib")
    return {"task": "health_screening", "selected": best_name, "reports": reports, "data_kind": "DEMO DATA"}


def train_environment() -> dict:
    path = Path(__file__).resolve().parent / "data" / "demo_environment.csv"
    if not path.exists():
        from ai.companion.make_demo import main as mk

        mk()
    df = pd.read_csv(path)
    if not (df["data_kind"] == "DEMO DATA").all():
        raise ValueError("Environment CSV must be DEMO DATA")

    gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=13)
    tr, te = next(gss.split(df, df["label"], df["scenario"]))
    train, test = df.iloc[tr], df.iloc[te]
    Xtr, ytr = train[ENV_FEATURE_NAMES].to_numpy(), train["label"].to_numpy()
    Xte, yte = test[ENV_FEATURE_NAMES].to_numpy(), test["label"].to_numpy()

    fitted = _train_candidates(Xtr, ytr, multiclass=True)
    reports = {}
    for name, m in fitted.items():
        pred = m.predict(Xte)
        reports[name] = _metrics(yte, pred, labels=[0, 1, 2])
        reports[name]["note"] = "DEMO DATA — not operational disaster validation"

    best_name, best_model = _select_best(reports, fitted)
    import joblib

    joblib.dump(best_model, MODELS / "env_selected.joblib")
    export_tree = fitted["decision_tree"]
    joblib.dump(export_tree, MODELS / "env_export_tree.joblib")
    return {
        "task": "environmental_disaster",
        "selected": best_name,
        "export_tree": "decision_tree",
        "labels": ["LOW", "WATCH", "HIGH"],
        "features": ENV_FEATURE_NAMES,
        "reports": reports,
        "data_kind": "DEMO DATA",
    }


def main():
    MODELS.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    out = {
        "problem_id": "26181",
        "problem_title": "AI Personal Health Companion — privacy-preserving screening + disaster early warning",
        "validation": "DEMO DATA pipeline test only — NOT clinical or operational disaster validation",
        "models": {},
    }
    out["models"]["health"] = train_health()
    out["models"]["environment"] = train_environment()

    REPORT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))

    from ai.health.export import main as hexport
    from ai.companion.export import main as eexport

    hexport()
    eexport()
    return out


if __name__ == "__main__":
    main()
