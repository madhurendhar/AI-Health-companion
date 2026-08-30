"""Export sklearn DecisionTree or first tree of forest to compact JSON + C header."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from companion_core.config import HEALTH

ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "models"
FIRMWARE_HEADER = Path(__file__).resolve().parents[2] / "firmware" / "include" / "companion" / "health_tree_model.h"


def _tree_to_nodes(tree) -> list[dict]:
    t = tree.tree_
    nodes = []
    for i in range(t.node_count):
        if t.children_left[i] == t.children_right[i]:
            # leaf: class probability of positive class if classifier
            val = t.value[i]
            if val.ndim == 2:
                counts = val[0]
                total = counts.sum() if counts.sum() else 1.0
                v = float(counts[-1] / total)
            else:
                v = float(val.ravel()[0])
            nodes.append({"f": -1, "t": 0.0, "l": -1, "r": -1, "v": v})
        else:
            nodes.append(
                {
                    "f": int(t.feature[i]),
                    "t": float(t.threshold[i]),
                    "l": int(t.children_left[i]),
                    "r": int(t.children_right[i]),
                    "v": 0.0,
                }
            )
    return nodes


def export_estimator(est, n_features: int, name: str, version: str, task: str) -> dict:
    if isinstance(est, (DecisionTreeClassifier, DecisionTreeRegressor)):
        tree = est
    elif hasattr(est, "estimators_"):
        tree = est.estimators_[0]
    else:
        raise TypeError(f"Cannot export {type(est)}")
    payload = {
        "type": "tree",
        "task": task,
        "n_features": n_features,
        "nodes": _tree_to_nodes(tree),
        "model_name": name,
        "model_version": version,
        "feature_schema_version": HEALTH.feature_schema_version,
        "data_kind": "DEMO DATA",
        "validation": "PENDING",
    }
    return payload


def write_c_header(payload: dict, path: Path, guard: str = "COMPANION_HEALTH_TREE_MODEL_H"):
    nodes = payload["nodes"]
    lines = [
        f"#ifndef {guard}",
        f"#define {guard}",
        '#include "companion/tree_infer.h"',
        f"#define HEALTH_TREE_N_FEATURES {payload['n_features']}",
        f"#define HEALTH_TREE_N_NODES {len(nodes)}",
        "static const companion_tree_node_t HEALTH_TREE_NODES[HEALTH_TREE_N_NODES] = {",
    ]
    for n in nodes:
        lines.append(f"  {{{int(n['f'])}, {float(n['t']):.8f}f, {int(n['l'])}, {int(n['r'])}, {float(n['v']):.8f}f}},")
    lines += [
        "};",
        f"#endif /* {guard} */",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    est = joblib.load(MODELS / "selected.joblib")
    n_features = 14
    payload = export_estimator(est, n_features, HEALTH.model_name, HEALTH.model_version, "health")
    MODELS.mkdir(parents=True, exist_ok=True)
    (MODELS / "health_tree.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_c_header(payload, FIRMWARE_HEADER)
    print("exported", MODELS / "health_tree.json")


if __name__ == "__main__":
    main()
