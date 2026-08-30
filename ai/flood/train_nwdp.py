"""Flood ML on NWDP Chennai rainfall — proxy labels (NOT flood events)."""

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

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

from companion_core.config import FLOOD
from companion_core.flood_features import FEATURE_NAMES, rainfall_windows

PARQUET = ROOT / "data" / "processed" / "rainfall" / "chennai_rainfall.parquet"
REPORT = ROOT / "reports" / "flood_model_results.json"
IMPORTANCE = ROOT / "reports" / "flood_feature_importance.json"
DEMO = ROOT / "data" / "demo_health.csv"


def build_nwdp_dataset() -> pd.DataFrame | None:
    if not PARQUET.exists():
        return None
    df = pd.read_parquet(PARQUET)
    df["hour"] = df["timestamp"].dt.floor("h")
    hourly = df.groupby("hour", as_index=False)["rainfall_mm"].sum().sort_values("hour")
    vals = hourly["rainfall_mm"].tolist()
    rows = []
    for i in range(24, len(vals)):
        window = vals[i - 72 : i] if i >= 72 else vals[:i]
        f = rainfall_windows(window)
        r24 = f.rain_24h
        rows.append({**{k: getattr(f, k) for k in FEATURE_NAMES}, "hour": hourly.iloc[i]["hour"], "rain_24h": r24})
    feat_df = pd.DataFrame(rows)
    feat_df["data_kind"] = "NWDP_PROXY_LABEL"
    return feat_df


def temporal_split(df: pd.DataFrame, test_frac: float = 0.2):
    n = len(df)
    cut = int(n * (1 - test_frac))
    train_raw = df.iloc[:cut].copy()
    test_raw = df.iloc[cut:].copy()
    p95 = train_raw["rain_24h"].quantile(0.95)
    train_raw["label"] = (train_raw["rain_24h"] >= p95).astype(int)
    test_raw["label"] = (test_raw["rain_24h"] >= p95).astype(int)
    note = f"rain_24h >= train_p95 ({p95:.1f}mm) — NOT flood event labels"
    train_raw["label_note"] = note
    test_raw["label_note"] = note
    return train_raw, test_raw, p95


def train_and_report(df: pd.DataFrame) -> dict:
    train, test, p95 = temporal_split(df)
    Xtr, ytr = train[FEATURE_NAMES].to_numpy(), train["label"].to_numpy()
    Xte, yte = test[FEATURE_NAMES].to_numpy(), test["label"].to_numpy()
    models = {
        "logistic_regression": LogisticRegression(max_iter=500, class_weight="balanced"),
        "decision_tree": DecisionTreeClassifier(max_depth=6, min_samples_leaf=8, class_weight="balanced"),
        "random_forest": RandomForestClassifier(
            n_estimators=50, max_depth=6, min_samples_leaf=6, class_weight="balanced", random_state=11
        ),
    }
    try:
        from xgboost import XGBClassifier

        models["xgboost"] = XGBClassifier(
            n_estimators=40, max_depth=4, learning_rate=0.1, eval_metric="logloss", scale_pos_weight=3
        )
    except Exception:
        pass

    reports = {}
    best_name, best_rec, best_model = None, -1.0, None
    for name, m in models.items():
        m.fit(Xtr, ytr)
        pred = m.predict(Xte)
        proba = m.predict_proba(Xte)[:, 1] if hasattr(m, "predict_proba") else pred
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
        }
        if reports[name]["recall"] > best_rec or (
            reports[name]["recall"] == best_rec and reports[name]["f1"] > reports.get(best_name, {}).get("f1", -1)
        ):
            best_name, best_rec, best_model = name, reports[name]["recall"], m

    # Prefer exportable tree for compact JSON; else keep best sklearn in joblib
    export_model = best_model
    if best_name != "decision_tree" and "decision_tree" in models:
        export_model = models["decision_tree"]

    imp = {}
    if hasattr(best_model, "feature_importances_"):
        imp = dict(zip(FEATURE_NAMES, [float(x) for x in best_model.feature_importances_]))

    out = {
        "selected": best_name,
        "reports": reports,
        "data_kind": "NWDP_PROXY_LABEL",
        "validation": "NOT flood-event validation — rainfall percentile proxy labels",
        "split": "temporal (earlier train, later test)",
        "flood_event_labels": "PENDING EXTERNAL DATA",
        "model_name": FLOOD.model_name,
        "model_version": FLOOD.model_version,
        "n_train": len(train),
        "n_test": len(test),
        "label_definition": train["label_note"].iloc[0] if len(train) else "",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    IMPORTANCE.write_text(json.dumps(imp, indent=2), encoding="utf-8")
    import joblib

    joblib.dump(best_model, ROOT / "ai" / "flood" / "models" / "selected.joblib")
    joblib.dump(export_model, ROOT / "ai" / "flood" / "models" / "export_tree.joblib")
    print(json.dumps(out, indent=2))
    return out, best_model


def main():
    df = build_nwdp_dataset()
    if df is None:
        print("No NWDP parquet — run ai/flood/data/ingest_nwdp.py first")
        return
    train_and_report(df)
    from ai.flood.export import main as export_main

    export_main()


if __name__ == "__main__":
    main()
