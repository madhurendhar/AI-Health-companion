#include "companion/health_engine.h"
#include "companion/config.h"
#include <math.h>

void companion_baseline_init(companion_baseline_t *b) {
  b->resting_hr = 72.f;
  b->hr_range = 12.f;
  b->typical_spo2 = 97.5f;
  b->typical_temp = 36.4f;
  b->samples = 0;
  b->ready = 0;
}

float companion_clip01(float x) {
  if (x < 0) return 0;
  if (x > 1) return 1;
  return x;
}

void companion_baseline_update(companion_baseline_t *b, const companion_features_t *f, float risk) {
  if (!f->valid) return;
  if (risk >= COMPANION_BASELINE_SKIP && b->ready) return;
  float rate = b->ready ? COMPANION_BASELINE_RATE : 0.15f;
  b->resting_hr = (1 - rate) * b->resting_hr + rate * f->hr;
  float spread = fabsf(f->hr - b->resting_hr);
  if (spread < 6.f) spread = 6.f;
  b->hr_range = (1 - rate) * b->hr_range + rate * spread;
  b->typical_spo2 = (1 - rate) * b->typical_spo2 + rate * f->spo2;
  b->typical_temp = (1 - rate) * b->typical_temp + rate * f->temperature;
  b->samples++;
  if (b->samples >= COMPANION_BASELINE_MIN_SAMPLES) b->ready = 1;
}

float companion_heuristic_risk(const companion_features_t *f, const companion_baseline_t *b) {
  (void)b;
  if (f->signal_quality < COMPANION_SIGNAL_Q_MIN || !f->valid) return 0.f;
  float score = 0.f;
  float hr_dev = fabsf(f->hr_dev);
  float spo2_dev = f->spo2_dev > 0 ? f->spo2_dev : 0;
  float temp_dev = fabsf(f->temp_dev);
  score += 0.22f * companion_clip01((hr_dev - 0.8f) / 2.f);
  score += 0.28f * companion_clip01((spo2_dev - 0.3f) / 1.5f);
  score += 0.18f * companion_clip01((temp_dev - 0.6f) / 1.8f);
  score += 0.08f * companion_clip01(fabsf(f->hr_trend) / 4.f);
  score += 0.10f * companion_clip01((-(f->spo2_trend)) / 1.5f);
  score += 0.06f * companion_clip01(fabsf(f->temperature_trend) / 0.4f);
  score += 0.08f * f->persistence;
  float env = 1.f;
  if (f->ambient_temp >= 34.f) env += 0.05f;
  if (f->humidity >= 85.f) env += 0.03f;
  if (f->mq135_relative >= 0.7f) env += 0.04f;
  return companion_clip01(score * env);
}

companion_health_status_t companion_health_status(float score, const companion_features_t *f) {
  if (!f->valid) return HEALTH_INSUFFICIENT;
  if (f->signal_quality < COMPANION_SIGNAL_Q_MIN) return HEALTH_RECHECK;
  if (score >= COMPANION_RISK_ELEVATED) return HEALTH_ELEVATED;
  if (score >= COMPANION_RISK_RECHECK) return HEALTH_RECHECK;
  return HEALTH_NORMAL;
}
