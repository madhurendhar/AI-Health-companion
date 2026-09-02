#include "companion/features.h"
#include "companion/config.h"
#include <math.h>
#include <string.h>

void companion_features_init(companion_feature_state_t *s) {
  memset(s, 0, sizeof(*s));
  companion_ema_init(&s->hr, COMPANION_EMA_ALPHA);
  companion_ema_init(&s->spo2, COMPANION_EMA_ALPHA);
  companion_ema_init(&s->temp, COMPANION_EMA_ALPHA);
  companion_ema_init(&s->amb, COMPANION_EMA_ALPHA);
  companion_ema_init(&s->hum, COMPANION_EMA_ALPHA);
  companion_ema_init(&s->mq, 0.15f);
}

void companion_features_extract(
    companion_feature_state_t *s,
    const companion_reading_t *r,
    const companion_baseline_t *b,
    uint8_t prev_abnormal,
    companion_features_t *out) {
  memset(out, 0, sizeof(*out));
  out->signal_quality = r->ppg_quality;

  if (r->max_state == COMP_OK && r->hr_valid) {
    out->hr = companion_ema_update(&s->hr, r->hr, 1);
    if (s->hr_prev_ok) out->hr_trend = out->hr - s->hr_prev;
    s->hr_prev = out->hr;
    s->hr_prev_ok = 1;
  }
  if (r->max_state == COMP_OK && r->spo2_valid) {
    out->spo2 = companion_ema_update(&s->spo2, r->spo2, 1);
    if (s->spo2_prev_ok) out->spo2_trend = out->spo2 - s->spo2_prev;
    s->spo2_prev = out->spo2;
    s->spo2_prev_ok = 1;
  }
  if (r->mlx_state == COMP_OK && r->temp_valid) {
    out->temperature = companion_ema_update(&s->temp, r->object_temp_c, 1);
    if (s->temp_prev_ok) out->temperature_trend = out->temperature - s->temp_prev;
    s->temp_prev = out->temperature;
    s->temp_prev_ok = 1;
  }
  if (r->dht_valid) {
    out->ambient_temp = companion_ema_update(&s->amb, r->dht_temp_c, 1);
    out->humidity = companion_ema_update(&s->hum, r->humidity, 1);
  }
  if (r->mq_state == COMP_OK) {
    out->mq135_relative = companion_ema_update(&s->mq, r->mq135_relative, 1);
  }

  if (out->hr > 0) out->hr_dev = (out->hr - b->resting_hr) / (b->hr_range > 4.f ? b->hr_range : 4.f);
  if (out->spo2 > 0) out->spo2_dev = (b->typical_spo2 - out->spo2) / 4.f;
  if (out->temperature > 0) out->temp_dev = (out->temperature - b->typical_temp) / 1.2f;

  if (prev_abnormal) {
    if (s->persist_hits < 100) s->persist_hits++;
  } else if (s->persist_hits > 0) {
    s->persist_hits--;
  }
  out->persistence = s->persist_hits / 6.f;
  if (out->persistence > 1.f) out->persistence = 1.f;

  out->valid = (out->hr > 0 && out->spo2 > 0 && r->ppg_quality >= COMPANION_SIGNAL_Q_MIN) ? 1 : 0;
#if !COMPANION_CAL_MLX_OPTIONAL
  if (out->temperature <= 0) out->valid = 0;
#endif
}

void companion_features_vector(const companion_features_t *f, float *x, int n) {
  if (n < 14) return;
  x[0] = f->hr;
  x[1] = f->spo2;
  x[2] = f->temperature;
  x[3] = f->hr_trend;
  x[4] = f->spo2_trend;
  x[5] = f->temperature_trend;
  x[6] = f->signal_quality;
  x[7] = f->hr_dev;
  x[8] = f->spo2_dev;
  x[9] = f->temp_dev;
  x[10] = f->persistence;
  x[11] = f->ambient_temp;
  x[12] = f->humidity;
  x[13] = f->mq135_relative;
}

void companion_flood_vector(float rain24, float *x, int n) {
  if (n < 9) return;
  memset(x, 0, sizeof(float) * (size_t)n);
  x[4] = rain24;
  x[6] = rain24;
}
