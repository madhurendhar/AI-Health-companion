#include "companion/calibration.h"
#include "companion/config.h"
#include <math.h>
#include <string.h>

#ifndef COMPANION_CAL_DURATION_MS
#define COMPANION_CAL_DURATION_MS 300000UL
#endif
#ifndef COMPANION_CAL_MIN_SAMPLES
#define COMPANION_CAL_MIN_SAMPLES 40
#endif
#ifndef COMPANION_CAL_MIN_PPG
#define COMPANION_CAL_MIN_PPG 0.50f
#endif
#ifndef COMPANION_CAL_INTERVAL_MS
#define COMPANION_CAL_INTERVAL_MS 1000UL
#endif

void companion_cal_init(companion_calibration_t *c) {
  memset(c, 0, sizeof(*c));
  c->phase = CAL_IDLE;
  strncpy(c->message, "Hold finger on sensor", sizeof(c->message) - 1);
}

void companion_cal_start(companion_calibration_t *c, uint32_t now_ms) {
  memset(c, 0, sizeof(*c));
  c->phase = CALIBRATING;
  c->started_ms = now_ms;
  c->hr_min = 999.f;
  c->hr_max = 0.f;
  strncpy(c->message, "Calibrating 5 min - hold still", sizeof(c->message) - 1);
}

static uint8_t reading_ok(const companion_reading_t *r, companion_calibration_t *c) {
  if (r->max_state != COMP_OK || !r->hr_valid || !r->spo2_valid) return 0;
  if (r->ppg_quality < COMPANION_CAL_MIN_PPG) return 0;
  if (r->mlx_state != COMP_OK || !r->temp_valid) return 0;
  if (r->hr < COMPANION_HR_MIN || r->hr > COMPANION_HR_MAX) return 0;
  if (r->spo2 < COMPANION_SPO2_MIN || r->spo2 > COMPANION_SPO2_MAX) return 0;
  if (r->object_temp_c < COMPANION_OBJ_TEMP_MIN || r->object_temp_c > COMPANION_OBJ_TEMP_MAX) return 0;
  if (c->good_samples > 0 && fabsf(r->hr - c->last_hr) > 25.f) return 0;
  return 1;
}

uint8_t companion_cal_feed(companion_calibration_t *c, const companion_reading_t *r, uint32_t now_ms) {
  if (c->phase != CALIBRATING) return c->phase == CAL_READY;
  uint32_t elapsed = now_ms - c->started_ms;

  if (!reading_ok(r, c)) {
    c->rejected++;
    strncpy(c->message, "Adjust finger / hold still", sizeof(c->message) - 1);
    if (elapsed >= COMPANION_CAL_DURATION_MS && c->good_samples < COMPANION_CAL_MIN_SAMPLES) {
      c->phase = CAL_FAILED;
      strncpy(c->message, "Calibration failed", sizeof(c->message) - 1);
    }
    return 0;
  }

  if (c->last_accept_ms && (now_ms - c->last_accept_ms) < COMPANION_CAL_INTERVAL_MS) return 0;

  c->last_accept_ms = now_ms;
  c->good_samples++;
  c->hr_sum += r->hr;
  c->spo2_sum += r->spo2;
  c->temp_sum += r->object_temp_c;
  c->last_hr = r->hr;
  if (r->hr < c->hr_min) c->hr_min = r->hr;
  if (r->hr > c->hr_max) c->hr_max = r->hr;

  if (elapsed >= COMPANION_CAL_DURATION_MS && c->good_samples >= COMPANION_CAL_MIN_SAMPLES) {
    c->phase = CAL_READY;
    strncpy(c->message, "Calibration complete", sizeof(c->message) - 1);
    return 1;
  }
  if (elapsed >= COMPANION_CAL_DURATION_MS) {
    c->phase = CAL_FAILED;
    strncpy(c->message, "Calibration failed", sizeof(c->message) - 1);
  }
  return c->phase == CAL_READY;
}

void companion_cal_apply_baseline(companion_calibration_t *c, companion_baseline_t *b) {
  if (c->phase != CAL_READY || c->good_samples == 0) return;
  float n = (float)c->good_samples;
  b->resting_hr = c->hr_sum / n;
  b->typical_spo2 = c->spo2_sum / n;
  b->typical_temp = c->temp_sum / n;
  float spread = c->hr_max - c->hr_min;
  if (spread < 6.f) spread = 6.f;
  b->hr_range = spread / 2.f;
  b->samples = c->good_samples;
  b->ready = 1;
}
