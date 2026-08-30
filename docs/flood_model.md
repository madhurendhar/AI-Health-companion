# Flood model

## Production risk engine (no flood-event labels)

| Layer | Method | Validation |
|-------|--------|------------|
| Heuristic | rain24/rain72/intensity thresholds | Reference screening only |
| Baseline | NWDP Chennai historical percentiles (p90/p95/p99) | Rainfall anomaly, not floods |
| ML tree | Decision tree on proxy labels | **NOT flood-event validation** |

Final score = average of active layers.

## Supervised ML status

**PENDING EXTERNAL DATA** — no flood-event labels in supplied NWDP resources.

`ai/flood/train_nwdp.py` uses proxy labels (`rain_24h >= train_p95`) for pipeline testing. Temporal holdout had insufficient positive cases for meaningful metrics.

## Reports

- `reports/flood_model_results.json`
- `reports/flood_feature_importance.json`
- `reports/flood_baseline.json`

## Inference

- **Backend:** sklearn joblib + compact tree JSON
- **ESP32:** receives LOW/WATCH/HIGH from backend only (no flood model on device)
