"""Sklearn model loader for backend flood inference (not ESP32)."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np


class SklearnFloodModel:
    def __init__(self, est, model_name: str, model_version: str):
        self.est = est
        self.model_name = model_name
        self.model_version = model_version

    @classmethod
    def load(cls, path: str | Path, name: str, version: str) -> "SklearnFloodModel | None":
        p = Path(path)
        if not p.exists():
            return None
        return cls(joblib.load(p), name, version)

    def predict_score(self, x: list[float]) -> float:
        arr = np.array([x])
        if hasattr(self.est, "predict_proba"):
            proba = self.est.predict_proba(arr)[0]
            return float(proba[-1]) if len(proba) > 1 else float(proba[0])
        pred = self.est.predict(arr)[0]
        return float(pred)
