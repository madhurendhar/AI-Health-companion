# Companion AI models (Problem 26181)

## Models

| Model | Input | Output | Deployment |
|-------|-------|--------|------------|
| `health_screening` | HR, SpO2, temp, trends, baseline dev, MQ135, DHT | abnormal pattern score | ESP32 tree + host |
| `env_disaster` | heat index, humidity, MQ135, rainfall windows | LOW / WATCH / HIGH | Backend tree (+ ESP32 optional) |
| `flood_tree_v1` | NWDP rainfall features | LOW / WATCH / HIGH | Backend |

## Train

```bat
python -m ai.companion.make_demo
python -m ai.companion.train
```

Exports: `ai/companion/models/`, `ai/health/models/`, `reports/companion_model_results.json`

## Validation status

- **Health:** PENDING labelled clinical dataset
- **Environment:** DEMO DATA (heat wave, pollution, flood rain scenarios)
- **Flood NWDP:** rainfall percentile proxy — NOT flood-event labels

Never present demo metrics as medical or disaster operational validation.
