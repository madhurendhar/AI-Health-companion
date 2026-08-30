# Health AI

Task: **physiological abnormality screening**, not diagnosis.

Features actually used: HR, SpO2, object temperature (screening), trends, signal quality, baseline deviations, persistence, ambient temp/humidity, MQ135 relative.

Engine: multi-feature heuristic (not “HR > 100”) plus optional compact decision tree exported from sklearn (`ai/health/`).

Labels in `ai/health/data/` are **DEMO DATA**. Metrics in `ai/health/models/eval_report.json` are software-test numbers. **Real model validation: PENDING.**

On-device: `companion_tree_infer` + `HEALTH_TREE_NODES` (INT-free float tree, tens of KB). TensorFlow Lite Micro not required.

Outputs: `risk_score` 0–1, status NORMAL / RECHECK / ELEVATED. Low signal quality does not produce ELEVATED.
