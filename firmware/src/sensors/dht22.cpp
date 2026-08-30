#include "companion/sensors/dht22.h"
#include "companion/config.h"

#if defined(ARDUINO)
#include <Arduino.h>

static uint8_t dht_data[5];

static int dht_expect(uint8_t level, uint32_t timeout) {
  uint32_t t = 0;
  while (digitalRead(COMPANION_DHT_PIN) == level) {
    delayMicroseconds(1);
    if (++t > timeout) return -1;
  }
  return (int)t;
}

uint8_t dht22_begin() {
  pinMode(COMPANION_DHT_PIN, INPUT_PULLUP);
  return 1;
}

void dht22_read(companion_reading_t *out) {
  pinMode(COMPANION_DHT_PIN, OUTPUT);
  digitalWrite(COMPANION_DHT_PIN, LOW);
  delay(2);
  digitalWrite(COMPANION_DHT_PIN, HIGH);
  delayMicroseconds(30);
  pinMode(COMPANION_DHT_PIN, INPUT_PULLUP);
  if (dht_expect(HIGH, 100) < 0 || dht_expect(LOW, 100) < 0 || dht_expect(HIGH, 100) < 0) {
    out->dht_state = COMP_SENSOR_ERROR;
    out->dht_valid = 0;
    return;
  }
  for (int i = 0; i < 40; i++) {
    if (dht_expect(LOW, 80) < 0) {
      out->dht_state = COMP_SENSOR_ERROR;
      return;
    }
    int hi = dht_expect(HIGH, 90);
    if (hi < 0) {
      out->dht_state = COMP_SENSOR_ERROR;
      return;
    }
    dht_data[i / 8] <<= 1;
    if (hi > 40) dht_data[i / 8] |= 1;
  }
  uint8_t sum = (uint8_t)(dht_data[0] + dht_data[1] + dht_data[2] + dht_data[3]);
  if (sum != dht_data[4]) {
    out->dht_state = COMP_INVALID_READING;
    out->dht_valid = 0;
    return;
  }
  int16_t rawh = ((int16_t)dht_data[0] << 8) | dht_data[1];
  int16_t rawt = ((int16_t)dht_data[2] << 8) | dht_data[3];
  float hum = rawh * 0.1f;
  float temp = rawt * 0.1f;
  if (rawt & 0x8000) temp = -((rawt & 0x7FFF) * 0.1f);
  if (hum < 0 || hum > 100 || temp < -10 || temp > 60) {
    out->dht_state = COMP_INVALID_READING;
    out->dht_valid = 0;
    return;
  }
  out->humidity = hum;
  out->dht_temp_c = temp;
  out->dht_valid = 1;
  out->dht_state = COMP_OK;
}
#else
uint8_t dht22_begin() { return 0; }
void dht22_read(companion_reading_t *out) { out->dht_state = COMP_SENSOR_ERROR; }
#endif
