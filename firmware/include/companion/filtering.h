#ifndef COMPANION_FILTERING_H
#define COMPANION_FILTERING_H

#include "companion/config.h"
#include <math.h>
#include <stdint.h>

typedef struct {
  float alpha;
  float value;
  uint8_t has;
} companion_ema_t;

static inline void companion_ema_init(companion_ema_t *e, float a) {
  e->alpha = a;
  e->value = 0;
  e->has = 0;
}

static inline float companion_ema_update(companion_ema_t *e, float x, uint8_t valid) {
  if (!valid) return e->has ? e->value : NAN;
  if (!e->has) {
    e->value = x;
    e->has = 1;
  } else {
    e->value = e->alpha * x + (1.f - e->alpha) * e->value;
  }
  return e->value;
}

#endif
