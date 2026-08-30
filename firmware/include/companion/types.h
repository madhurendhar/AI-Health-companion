#ifndef COMPANION_TYPES_H
#define COMPANION_TYPES_H

#include <stdint.h>
#include <stdbool.h>

typedef enum {
  COMP_OK = 0,
  COMP_SENSOR_ERROR,
  COMP_NO_SIGNAL,
  COMP_INVALID_READING,
  COMP_WARMING_UP,
  COMP_STALE_DATA,
  COMP_NO_FINGER
} companion_sensor_state_t;

typedef enum {
  HEALTH_NORMAL = 0,
  HEALTH_RECHECK,
  HEALTH_ELEVATED,
  HEALTH_INSUFFICIENT
} companion_health_status_t;

typedef enum {
  AIR_NORMAL = 0,
  AIR_ELEVATED,
  AIR_HIGH,
  AIR_WARMING_UP
} companion_air_status_t;

typedef enum {
  FLOOD_LOW = 0,
  FLOOD_WATCH,
  FLOOD_HIGH
} companion_flood_status_t;

typedef struct {
  float hr;
  float spo2;
  float object_temp_c;
  float mlx_ambient_c;
  float dht_temp_c;
  float humidity;
  float mq135_raw;
  float mq135_relative;
  float ppg_quality;
  uint8_t hr_valid;
  uint8_t spo2_valid;
  uint8_t temp_valid;
  uint8_t dht_valid;
  uint8_t mq_valid;
  companion_sensor_state_t max_state;
  companion_sensor_state_t mlx_state;
  companion_sensor_state_t dht_state;
  companion_sensor_state_t mq_state;
  uint8_t demo_mode;
} companion_reading_t;

typedef struct {
  float resting_hr;
  float hr_range;
  float typical_spo2;
  float typical_temp;
  uint16_t samples;
  uint8_t ready;
} companion_baseline_t;

typedef struct {
  float hr, spo2, temperature;
  float hr_trend, spo2_trend, temperature_trend;
  float signal_quality;
  float hr_dev, spo2_dev, temp_dev;
  float persistence;
  float ambient_temp, humidity, mq135_relative;
  uint8_t valid;
} companion_features_t;

#endif
