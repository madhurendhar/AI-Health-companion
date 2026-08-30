"""Compact tree inference shared by host sim and export format.

JSON schema:
{"type":"tree","n_features":N,"nodes":[{f,t,l,r,v},...]}
leaf: f=-1, v=value; branch: feature index f, threshold t, left l, right r
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class CompactTree:
    def __init__(self, payload: dict[str, Any]):
        self.n_features = int(payload["n_features"])
        self.nodes = payload["nodes"]
        self.model_name = payload.get("model_name", "tree")
        self.model_version = payload.get("model_version", "0")
        self.task = payload.get("task", "")

    @classmethod
    def load(cls, path: str | Path) -> "CompactTree":
        with open(path, "r", encoding="utf-8") as f:
            return cls(json.load(f))

    def predict_value(self, x: list[float]) -> float:
        i = 0
        nodes = self.nodes
        while True:
            n = nodes[i]
            if int(n["f"]) < 0:
                return float(n["v"])
            feat = int(n["f"])
            val = x[feat] if feat < len(x) else 0.0
            i = int(n["l"]) if val <= float(n["t"]) else int(n["r"])

    def predict_score(self, x: list[float]) -> float:
        v = self.predict_value(x)
        return max(0.0, min(1.0, v))
