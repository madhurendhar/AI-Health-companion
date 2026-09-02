"""Export environmental disaster tree for backend + optional ESP32."""

from pathlib import Path
import json
import joblib

from ai.health.export import export_estimator, write_c_header
from ai.companion.features import ENV_FEATURE_NAMES

MODELS = Path(__file__).resolve().parent / "models"
HEADER = Path(__file__).resolve().parents[2] / "firmware" / "include" / "companion" / "env_tree_model.h"


def main():
    est = joblib.load(MODELS / "env_export_tree.joblib")
    payload = export_estimator(
        est, len(ENV_FEATURE_NAMES), "env_disaster_tree_v1", "1.0.0", "environment"
    )
    payload["labels"] = ["LOW", "WATCH", "HIGH"]
    payload["feature_names"] = ENV_FEATURE_NAMES
    payload["data_kind"] = "DEMO DATA"
    payload["validation"] = "PENDING real disaster labels"
    (MODELS / "env_disaster_tree.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_c_header(payload, HEADER, guard="COMPANION_ENV_TREE_MODEL_H")
    text = HEADER.read_text(encoding="utf-8")
    text = text.replace("HEALTH_TREE_N_FEATURES", "ENV_TREE_N_FEATURES")
    text = text.replace("HEALTH_TREE_N_NODES", "ENV_TREE_N_NODES")
    text = text.replace("HEALTH_TREE_NODES", "ENV_TREE_NODES")
    HEADER.write_text(text, encoding="utf-8")
    print("exported", MODELS / "env_disaster_tree.json")


if __name__ == "__main__":
    main()
