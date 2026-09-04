#include "companion/sensors/dht22.h"
#include "companion/config.h"

#if defined(ARDUINO)
#include <Arduino.h>
#include <DHT.h>

static DHT dht(COMPANION_DHT_PIN, DHT22);
static uint8_t sensor_ready = 0;

uint8_t dht22_begin() {
  dht.begin();
  delay(1500);
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  sensor_ready = 1;
  if (!isnan(t) && !isnan(h)) {
    Serial.println("DHT22: Adafruit library OK");
  } else {
    Serial.println("DHT22: started (first read pending — check GPIO4)");
  }
  return 1;
}

void dht22_read(companion_reading_t *out) {
  if (!sensor_ready) {
    out->dht_state = COMP_SENSOR_ERROR;
    out->dht_valid = 0;
    return;
  }

  float t = dht.readTemperature();
  float h = dht.readHumidity();
  if (isnan(t) || isnan(h) || h < 1.f || h > 100.f || t < -10.f || t > 60.f) {
    out->dht_state = COMP_INVALID_READING;
    out->dht_valid = 0;
    return;
  }

  out->dht_temp_c = t;
  out->humidity = h;
  out->dht_valid = 1;
  out->dht_state = COMP_OK;
}

#else
uint8_t dht22_begin() { return 0; }
void dht22_read(companion_reading_t *out) { out->dht_state = COMP_SENSOR_ERROR; }
#endif
