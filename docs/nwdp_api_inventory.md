# NWDP API inventory

Inspected: 2026-08-30 via `tools/nwdp_discover.py` and live API calls.

Endpoint: `https://www.nwdp.nwic.gov.in/api/3/action/datastore_search`

## Summary

| Label | Resource ID | District | Purpose | Rainfall field | Date range (approx) | Records |
|-------|-------------|----------|---------|----------------|---------------------|---------|
| chennai_1 | 51b0e617-02dc-4dd8-a6ce-fdce6c1731b9 | Chennai | Historical hourly rainfall | Telemetry Hourly Rainfall (mm) | 2021-08-09 → 2023-12-31 | 3567 |
| chennai_2 | 21b02519-f3d3-409d-a091-94332d848a8e | Chennai | Current hourly rainfall | Telemetry Hourly Rainfall (mm) | 2026-06-27 → 2026-06-30 | 255 |
| chennai_prev | 77459b05-fcbd-4b8c-97e1-e2a33d359ce3 | Chennai | River water level | River Water Level Telemetry Hourly (meter) | — | — |
| kanyakumari_1 | cd797dd2-dff1-45ee-87df-eaa554bbeb5f | Kanyakumari | Solar radiation | Solar Radiation (Watt/m2) | — | NOT rainfall |
| kanyakumari_2 | 387aa243-ae4d-4aa3-932b-bbc5b09e148e | Kanyakumari | Air temperature | Air Temperature Telemetry Hourly (AoC) | — | NOT rainfall |

**chennai_1 vs chennai_2:** Same station schema, **different time periods** — not duplicates. Use chennai_2 for live, chennai_1 for historical baseline/training features.

**Kanyakumari:** No rainfall in supplied resource IDs → rainfall flood pipeline **PENDING** external NWDP rainfall resource. Fallback: Open-Meteo or demo mode.

## Common schema fields

- `timestamp_field`: `Data Acquisition Time` (format `DD-MM-YYYY HH:MM`, treated as IST)
- `station_field`: `Station`
- `latitude`: `Latitude`, `longitude`: `Longitude`
- `rainfall_unit`: mm (Chennai rainfall resources)
- `temporal_resolution`: sub-hourly telemetry (~5 min); aggregated to hourly for features

## Flood event labels

**PENDING EXTERNAL DATA** — none of the five resources contain flood-event labels. Supervised flood ML uses demo data only; production risk uses **historical rainfall baseline/anomaly** on NWDP Chennai data.

## Machine-readable inventory

See `reports/nwdp_inventory.json`.
