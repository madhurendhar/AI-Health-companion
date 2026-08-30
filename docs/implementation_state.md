# Implementation state

**CURRENT PHASE:** Flood subsystem — NWDP integrated

**COMPLETED:**
- NWDP API inventory (5 resources) → `docs/nwdp_api_inventory.md`, `reports/nwdp_inventory.json`
- NWDP client + cache + parser (`backend/services/nwdp/`)
- Chennai ingestion (3567 rows) + `reports/flood_data_quality.json`
- Historical baseline (`chennai_baseline.json`, p90/p95/p99)
- Backend flood API (NWDP primary, demo, Open-Meteo fallback)
- Flood-only ESP32 firmware (Flash 72.8%, RAM 14.4%)
- Flood dashboard
- NWDP proxy ML train (`ai/flood/train_nwdp.py`) + export
- Tests: 21 passed

**IN PROGRESS:** none

**PENDING:**
- Real flood-event labels (supervised validation)
- Kanyakumari NWDP rainfall resource
- Health subsystem (phase 2 — intentionally not built)

**KNOWN ISSUES:**
- Temporal test split has **zero positive proxy labels** in holdout — ML metrics not meaningful; production risk uses **heuristic + historical baseline**
- chennai_1 ends 2023; live NWDP uses chennai_2 (Jun 2026)
- Kanyakumari: demo or Open-Meteo fallback only

**LAST TEST:** pytest 23 passed; integration 5 passed; merged ingest 3822 rows; pio SUCCESS

**NEXT STEP:** Set `COMPANION_DEMO_MODE=false`, `RAINFALL_PROVIDER=nwdp`, flash ESP32, point `companion_secrets.h` at backend

**FLOOD SUBSYSTEM:** functional prototype complete (pending real flood labels for supervised validation)
