# Privacy

- Raw health history: **SD `/patient/`** (`profile.json`, `baseline.json`, `readings.csv`, `events.csv`). No personal identifiers by default.
- Device may POST a **current screening snapshot** to the backend for the dashboard. It does not upload CSV history.
- S3 / `data/local_s3`: rainfall cache, models, environmental files — not identifiable patient history.
- Tokens: `.env` / `companion_secrets.h` (placeholders in repo). Never put AWS keys in firmware.
- Encryption: not enabled by default (no hard-coded keys). Optional future: NVS-generated key.
