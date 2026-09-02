#ifndef COMPANION_FEATURES_H
#define COMPANION_FEATURES_H

#include "filtering.h"
#include "types.h"

typedef struct {
  companion_ema_t hr;
  companion_ema_t spo2;
  companion_ema_t temp;
  companion_ema_t amb;
  companion_ema_t hum;
  companion_ema_t mq;
  float hr_prev;
  float spo2_prev;
  float temp_prev;
  uint8_t hr_prev_ok;
  uint8_t spo2_prev_ok;
  uint8_t temp_prev_ok;
  uint16_t persist_hits;
} companion_feature_state_t;

void companion_features_init(companion_feature_state_t *s);
void companion_features_extract(
    companion_feature_state_t *s,
    const companion_reading_t *r,
    const companion_baseline_t *b,
    uint8_t prev_abnormal,
    companion_features_t *out);
void companion_features_vector(const companion_features_t *f, float *x, int n);
void companion_flood_vector(float rain24, float *x, int n);

#endif
