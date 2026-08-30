# Implementation state

**CURRENT PHASE:** Flood event pipeline complete (real IFI labels + NWDP river level)

**COMPLETED:**
- Real NWDP ingest (3822 rows Chennai historical+current)
- Historical percentile stats (`chennai_historical_stats.json`) from REAL data
- Live vs historical comparison engine (`companion_core/historical_monitor.py`)
- Realtime monitor log + trend (`backend/monitor.py`, `tools/monitor_loop.py`)
- **Flood events:** IFI-Impacts v3 Chennai catalog (58 events, 546 flood-days)
- **River level:** NWDP Adyar Nandambakkam (~22k hourly readings)
- **Event dataset:** rainfall + IFI labels + river (`chennai_event_dataset.parquet`)
- **Event model:** trained on real labels (`ai/flood/train_flood_events.py`)
- **Runtime:** `companion_core/flood_events.py` — ML + river + IFI rain profile
- API: `/flood/status` (includes `flood_event`), `/flood/events`, `/monitor/*`
- Dashboard flood-event panel

**INFERENCE:**
1. Rainfall anomaly: NWDP live vs historical p90/p95/p99 → LOW/WATCH/HIGH
2. Flood event: IFI-trained model + river level + documented flood-day rain profile

**LIMITATIONS (documented honestly):**
- NWDP rainfall window (2021–2023) overlaps only 15 IFI flood-days; test split has 0 event positives
- River level p95≈10.065m (telemetry may plateau at gauge max)
- Kanyakumari: no NWDP rainfall in supplied IDs

**NOT USED:** synthetic demo ML, proxy percentile labels for flood-event validation

**PENDING:** Health sensors (phase 2)

**RUN flood event pipeline:**
```bat
python ai\flood\data\process_flood_events.py
python ai\flood\data\ingest_river_level.py
python ai\flood\build_event_dataset.py
python ai\flood\train_flood_events.py
```

**RUN monitoring:**
```bat
python ai\flood\data\ingest_nwdp.py
python ai\flood\build_historical_stats.py
set COMPANION_DEMO_MODE=false
python tools\monitor_loop.py
```
