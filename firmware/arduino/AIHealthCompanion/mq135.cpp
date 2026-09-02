#include "companion/sensors/mq135.h"
#include "companion/config.h"

#if defined(ARDUINO)
#include <Arduino.h>

static uint16_t warmup = 80;
static float r0 = 0;
static float ema = 0;
static uint8_t ema_has = 0;

void mq135_begin() {
  analogReadResolution(12);
  warmup = 80;
  r0 = 0;
}

void mq135_read(companion_reading_t *out, companion_air_status_t *air) {
  int raw = analogRead(COMPANION_MQ135_PIN);
  out->mq135_raw = (float)raw;
  if (warmup > 0) {
    warmup--;
    r0 = (r0 == 0) ? raw : (0.9f * r0 + 0.1f * raw);
    out->mq_state = COMP_WARMING_UP;
    out->mq_valid = 0;
    *air = AIR_WARMING_UP;
    return;
  }
  float rel = raw / (r0 < 1 ? 1 : r0);
  if (!ema_has) {
    ema = rel;
    ema_has = 1;
  } else {
    ema = 0.15f * rel + 0.85f * ema;
  }
  out->mq135_relative = ema;
  out->mq_valid = 1;
  out->mq_state = COMP_OK;
  if (ema < 1.25f) *air = AIR_NORMAL;
  else if (ema < 1.8f) *air = AIR_ELEVATED;
  else *air = AIR_HIGH;
}
#else
void mq135_begin() {}
void mq135_read(companion_reading_t *out, companion_air_status_t *air) {
  out->mq_state = COMP_SENSOR_ERROR;
  *air = AIR_WARMING_UP;
}
#endif
