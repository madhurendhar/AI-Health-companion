/* Health baseline calibration (on-device, no external dataset) */

#ifndef COMPANION_CALIBRATION_H
#define COMPANION_CALIBRATION_H

#include "types.h"
#include <stdint.h>

typedef enum {
  CAL_IDLE = 0,
  CALIBRATING,
  CAL_READY,
  CAL_FAILED
} companion_cal_phase_t;

typedef struct {
  companion_cal_phase_t phase;
  uint32_t started_ms;
  uint16_t good_samples;
  uint16_t rejected;
  float hr_sum;
  float spo2_sum;
  float temp_sum;
  float hr_min;
  float hr_max;
  float last_hr;
  uint32_t last_accept_ms;
  char message[64];
} companion_calibration_t;

void companion_cal_init(companion_calibration_t *c);
void companion_cal_start(companion_calibration_t *c, uint32_t now_ms);
uint8_t companion_cal_feed(companion_calibration_t *c, const companion_reading_t *r, uint32_t now_ms);
void companion_cal_apply_baseline(companion_calibration_t *c, companion_baseline_t *b);

#endif
