# Flood AI

**LOCATION-SPECIFIC FLOOD EARLY-RISK PREDICTION**, not guaranteed flood detection. No water-level / ultrasonic sensors.

Features from hourly precipitation: 1h, 3h, 6h, 12h, 24h, 48h, 72h, intensity, trend.

Production rainfall: [Open-Meteo](https://open-meteo.com) forecast+past_days (no API key). If the HTTP call fails: `NETWORK_ERROR` / last data + `stale`.

`ai/flood/data/` is **DEMO DATA** (Chennai, Mumbai, Kochi). Supervised columns: location, date, rainfall windows, flood-event label. **Operational validation: PENDING.**

State machine: LOW → WATCH → HIGH with hysteresis and cooldown (`companion_core/flood_risk.py`, firmware `flood_sm.cpp`).

Polling: LOW 30 min, WATCH 12 min, HIGH 5 min (backend `poll_interval_s`).
