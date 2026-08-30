# Flood data pipeline

## Sources

| Source | Location | Type | Notes |
|--------|----------|------|-------|
| NWDP `51b0e617…` | Chennai | Hourly rainfall (historical) | 2021–2023, 3567 records |
| NWDP `21b02519…` | Chennai | Hourly rainfall (current) | Jun 2026 window |
| NWDP `77459b05…` | Chennai | River water level | Not used for rainfall features |
| NWDP Kanyakumari IDs | Kanyakumari | Solar / temperature | **No rainfall** — PENDING resource |

## Ingestion

```bat
python ai/flood/data/ingest_nwdp.py
python ai/flood/baseline.py
python ai/flood/train_nwdp.py
```

Outputs:
- `data/processed/rainfall/chennai_rainfall.parquet`
- `reports/flood_data_quality.json`
- `data/processed/rainfall/chennai_baseline.json`
- `reports/flood_model_results.json`

## Flood event labels

**PENDING EXTERNAL DATA** — no flood-event labels in supplied NWDP resources.

Proxy ML labels use `rain_24h >= train_p95` for pipeline testing only. **Not flood validation.**

## Internal schema

`timestamp, state, district, agency, station, latitude, longitude, rainfall_mm, rainfall_unit, source, resource_id`
