#include "companion/sensors/mq135.h"
#include "companion/config.h"

#if defined(ARDUINO)
#include <Arduino.h>

/*
 * MQ135 AO -> 10k + 10k divider -> GPIO 34
 *   AO --[10k]-- mid --[10k]-- GND
 *                 |
 *              GPIO 34
 */

static uint16_t warmup = 100;
static float r0 = 0;
static float ema = 0;
static uint8_t ema_has = 0;

void mq135_begin() {
  analogReadResolution(12);
  analogSetPinAttenuation(COMPANION_MQ135_PIN, ADC_11db);
  pinMode(COMPANION_MQ135_PIN, INPUT);
  warmup = 100;
  r0 = 0;
  ema = 0;
  ema_has = 0;
  Serial.printf("MQ135: ADC GPIO %d (10k+10k divider from AO)\n", COMPANION_MQ135_PIN);
}

void mq135_read(companion_reading_t *out, companion_air_status_t *air) {
  int raw = analogRead(COMPANION_MQ135_PIN);
  out->mq135_raw = (float)raw;

  if (warmup > 0) {
    warmup--;
    r0 = (r0 == 0) ? (float)raw : (0.9f * r0 + 0.1f * (float)raw);
    out->mq_state = COMP_WARMING_UP;
    out->mq_valid = 0;
    out->mq135_relative = 0.f;
    *air = AIR_WARMING_UP;
    return;
  }

  float rel = (float)raw / (r0 < 1.f ? 1.f : r0);
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
