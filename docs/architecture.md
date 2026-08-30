# Architecture

```
MAX30102 MLX90614 DHT22 MQ135
        -> drivers -> validation -> filter -> features
        -> personal baseline -> local health tree/heuristic
        -> NORMAL | RECHECK | ELEVATED
        -> OLED / LED / buzzer
        -> SD /patient (not S3)

ESP32 --HTTPS--> backend -- Open-Meteo --> rainfall windows
                        -- flood tree/heuristic --> LOW | WATCH | HIGH
                        -- local_s3 fallback if AWS unset
Dashboard <-- GET /health/status /environment/status /flood/status
Device POST /device/status  (current screening snapshot only)
```

Health inference is designed to run **on the ESP32** (`firmware/src/main.cpp` + `health_engine.cpp` + compact tree header). Flood inference needs rainfall from the network; the **backend** runs the flood model and the device displays last result (stale if offline).

Demo path: `COMPANION_DEMO_MODE` / `tools/device_sim.py` / `/demo/scenario`. Never mixed with live FIFO bytes in the same reading.
