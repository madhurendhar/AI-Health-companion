#include "companion/sensors/mlx90614.h"
#include "companion/config.h"

#if defined(ARDUINO)
#include <Arduino.h>
#include <Wire.h>
#define MLX_ADDR 0x5A

static float last_obj_c = 0.f;
static float last_amb_c = 0.f;
static uint8_t last_ok = 0;

static uint16_t mlx_read16(uint8_t ram) {
  for (uint8_t attempt = 0; attempt < 3; attempt++) {
    Wire.beginTransmission(MLX_ADDR);
    Wire.write(ram);
    if (Wire.endTransmission(false) != 0) {
      delay(2);
      continue;
    }
    if (Wire.requestFrom((uint8_t)MLX_ADDR, (uint8_t)3) < 2) {
      delay(2);
      continue;
    }
    uint8_t lsb = Wire.read();
    uint8_t msb = Wire.read();
    Wire.read();
    return ((uint16_t)msb << 8) | lsb;
  }
  return 0xFFFF;
}

uint8_t mlx90614_begin() {
  Wire.beginTransmission(MLX_ADDR);
  return Wire.endTransmission() == 0;
}

void mlx90614_read(companion_reading_t *out) {
  uint16_t obj = mlx_read16(0x07);
  uint16_t amb = mlx_read16(0x06);
  if (obj == 0xFFFF || amb == 0xFFFF) {
    out->mlx_state = COMP_SENSOR_ERROR;
    if (last_ok) {
      out->object_temp_c = last_obj_c;
      out->mlx_ambient_c = last_amb_c;
      out->temp_valid = 1;
      out->mlx_state = COMP_STALE_DATA;
    } else {
      out->temp_valid = 0;
    }
    return;
  }
  float tc = (obj * 0.02f) - 273.15f;
  float ta = (amb * 0.02f) - 273.15f;
  out->mlx_ambient_c = ta;
  out->object_temp_c = tc;
  if (tc < COMPANION_OBJ_TEMP_MIN || tc > COMPANION_OBJ_TEMP_MAX) {
    out->mlx_state = COMP_INVALID_READING;
    out->temp_valid = 0;
    return;
  }
  last_obj_c = tc;
  last_amb_c = ta;
  last_ok = 1;
  out->temp_valid = 1;
  out->mlx_state = COMP_OK;
}
#else
uint8_t mlx90614_begin() { return 0; }
void mlx90614_read(companion_reading_t *out) { out->mlx_state = COMP_SENSOR_ERROR; }
#endif
