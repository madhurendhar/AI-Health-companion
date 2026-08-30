#include "companion/sensors/mlx90614.h"
#include "companion/config.h"

#if defined(ARDUINO)
#include <Arduino.h>
#include <Wire.h>
#define MLX_ADDR 0x5A

static uint16_t mlx_read16(uint8_t ram) {
  Wire.beginTransmission(MLX_ADDR);
  Wire.write(ram);
  if (Wire.endTransmission(false) != 0) return 0xFFFF;
  if (Wire.requestFrom((uint8_t)MLX_ADDR, (uint8_t)3) < 2) return 0xFFFF;
  uint8_t lsb = Wire.read();
  uint8_t msb = Wire.read();
  Wire.read(); /* pec ignored */
  return ((uint16_t)msb << 8) | lsb;
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
    out->temp_valid = 0;
    return;
  }
  float tc = (obj * 0.02f) - 273.15f;
  float ta = (amb * 0.02f) - 273.15f;
  out->mlx_ambient_c = ta;
  if (tc < COMPANION_OBJ_TEMP_MIN || tc > COMPANION_OBJ_TEMP_MAX) {
    out->mlx_state = COMP_INVALID_READING;
    out->temp_valid = 0;
    return;
  }
  out->object_temp_c = tc;
  out->temp_valid = 1;
  out->mlx_state = COMP_OK;
}
#else
uint8_t mlx90614_begin() { return 0; }
void mlx90614_read(companion_reading_t *out) { out->mlx_state = COMP_SENSOR_ERROR; }
#endif
