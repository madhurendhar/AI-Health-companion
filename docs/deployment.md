# Deployment

## Backend

`uvicorn backend.app:app --host 127.0.0.1 --port 8080`

Set `COMPANION_API_TOKEN`. Leave `S3_BUCKET` empty for `LocalObjectStore` (`data/local_s3`). Target extra cloud cost: ₹0.

`RAINFALL_PROVIDER=open_meteo` when not in demo. `COMPANION_DEMO_MODE=true` uses simulated rainfall.

## ESP32

1. PlatformIO `env:esp32dev`
2. Wi-Fi + backend URL in `firmware/include/companion_secrets.h`
3. Same API token as backend
4. Flash 4 MB partition default

## Offline

Health path does not require Wi-Fi. Flood display must show stale / network error — firmware sets `flood_stale` when GET fails.
