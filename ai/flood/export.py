from pathlib import Path
import json
import joblib

from ai.health.export import export_estimator, write_c_header
from companion_core.config import FLOOD
from companion_core.flood_features import FEATURE_NAMES

ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "models"
FIRMWARE_HEADER = Path(__file__).resolve().parents[2] / "firmware" / "include" / "companion" / "flood_tree_model.h"


def main():
    est_path = MODELS / "export_tree.joblib"
    if not est_path.exists():
        est_path = MODELS / "selected.joblib"
    est = joblib.load(est_path)
    try:
        payload = export_estimator(est, len(FEATURE_NAMES), FLOOD.model_name, FLOOD.model_version, "flood")
        payload["feature_schema_version"] = FLOOD.feature_schema_version
        (MODELS / "flood_tree.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        write_c_header(payload, FIRMWARE_HEADER, guard="COMPANION_FLOOD_TREE_MODEL_H")
        text = FIRMWARE_HEADER.read_text(encoding="utf-8")
        text = text.replace("HEALTH_TREE_N_FEATURES", "FLOOD_TREE_N_FEATURES")
        text = text.replace("HEALTH_TREE_N_NODES", "FLOOD_TREE_N_NODES")
        text = text.replace("HEALTH_TREE_NODES", "FLOOD_TREE_NODES")
        FIRMWARE_HEADER.write_text(text, encoding="utf-8")
        print("exported tree", MODELS / "flood_tree.json")
    except TypeError as exc:
        meta = {
            "type": "sklearn",
            "sklearn_class": type(est).__name__,
            "model_name": FLOOD.model_name,
            "model_version": FLOOD.model_version,
            "note": str(exc),
        }
        (MODELS / "flood_model_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print("sklearn-only export (no tree header):", type(est))


if __name__ == "__main__":
    main()
