#include "companion/sensors/mlx90614.h"
#include "companion/config.h"

#if defined(ARDUINO)
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_MLX90614.h>

static Adafruit_MLX90614 mlx = Adafruit_MLX90614();
static uint8_t sensor_ready = 0;

uint8_t mlx90614_begin() {
  sensor_ready = 0;
  if (!mlx.begin(COMPANION_MLX90614_ADDR, &Wire)) {
    Serial.println("MLX90614: begin failed");
    return 0;
  }
  sensor_ready = 1;
  Serial.println("MLX90614: Adafruit library OK");
  return 1;
}

void mlx90614_read(companion_reading_t *out) {
  if (!sensor_ready) {
    out->mlx_state = COMP_SENSOR_ERROR;
    out->temp_valid = 0;
    return;
  }

  float obj = mlx.readObjectTempC();
  float amb = mlx.readAmbientTempC();
  out->mlx_ambient_c = amb;
  out->object_temp_c = obj;

  if (isnan(obj) || obj < COMPANION_OBJ_TEMP_MIN || obj > COMPANION_OBJ_TEMP_MAX) {
    out->mlx_state = COMP_INVALID_READING;
    out->temp_valid = 0;
    return;
  }

  out->temp_valid = 1;
  out->mlx_state = COMP_OK;
}

#else
uint8_t mlx90614_begin() { return 0; }
void mlx90614_read(companion_reading_t *out) { out->mlx_state = COMP_SENSOR_ERROR; }
#endif
