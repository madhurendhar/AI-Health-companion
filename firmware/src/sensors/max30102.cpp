#include "companion/sensors/max30102.h"
#include "companion/config.h"

#if defined(ARDUINO)
#include <Arduino.h>
#include <Wire.h>
#include <math.h>

#define MAX30102_ADDR 0x57
#define REG_INTR_STATUS_1 0x00
#define REG_FIFO_WR_PTR 0x04
#define REG_FIFO_RD_PTR 0x06
#define REG_FIFO_DATA 0x07
#define REG_FIFO_CONFIG 0x08
#define REG_MODE_CONFIG 0x09
#define REG_SPO2_CONFIG 0x0A
#define REG_LED1_PA 0x0C
#define REG_LED2_PA 0x0D

static uint8_t write_reg(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(MAX30102_ADDR);
  Wire.write(reg);
  Wire.write(val);
  return Wire.endTransmission() == 0;
}

static uint8_t read_reg(uint8_t reg, uint8_t *buf, uint8_t n) {
  Wire.beginTransmission(MAX30102_ADDR);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return 0;
  if (Wire.requestFrom((uint8_t)MAX30102_ADDR, n) != n) return 0;
  for (uint8_t i = 0; i < n; i++) buf[i] = Wire.read();
  return 1;
}

static uint32_t ir_buf[32];
static uint32_t red_buf[32];
static uint8_t buf_n = 0;

uint8_t max30102_begin() {
  uint8_t part[1];
  if (!read_reg(0xFF, part, 1)) return 0;
  write_reg(REG_MODE_CONFIG, 0x40); // reset
  delay(50);
  write_reg(REG_FIFO_CONFIG, 0x4F);
  write_reg(REG_SPO2_CONFIG, 0x27);
  write_reg(REG_LED1_PA, 0x24);
  write_reg(REG_LED2_PA, 0x24);
  write_reg(REG_MODE_CONFIG, 0x03); // SpO2 mode
  buf_n = 0;
  return 1;
}

static float estimate_hr(const uint32_t *ir, uint8_t n) {
  if (n < 16) return NAN;
  uint32_t mn = ir[0], mx = ir[0];
  for (uint8_t i = 1; i < n; i++) {
    if (ir[i] < mn) mn = ir[i];
    if (ir[i] > mx) mx = ir[i];
  }
  if (mx - mn < 200) return NAN;
  float thr = (mn + mx) * 0.5f;
  int peaks = 0;
  for (uint8_t i = 1; i < n - 1; i++) {
    if (ir[i] > thr && ir[i] >= ir[i - 1] && ir[i] >= ir[i + 1]) peaks++;
  }
  /* ~25 Hz window of 32 samples ≈ 1.28 s */
  float hr = (peaks * 60.f) / (n / 25.f);
  if (hr < COMPANION_HR_MIN || hr > COMPANION_HR_MAX) return NAN;
  return hr;
}

static float estimate_spo2(const uint32_t *red, const uint32_t *ir, uint8_t n) {
  if (n < 16) return NAN;
  double r_ac = 0, i_ac = 0, r_dc = 0, i_dc = 0;
  for (uint8_t i = 0; i < n; i++) {
    r_dc += red[i];
    i_dc += ir[i];
  }
  r_dc /= n;
  i_dc /= n;
  if (r_dc < 1000 || i_dc < 1000) return NAN;
  for (uint8_t i = 0; i < n; i++) {
    double rd = (double)red[i] - r_dc;
    double id = (double)ir[i] - i_dc;
    r_ac += rd * rd;
    i_ac += id * id;
  }
  r_ac = sqrt(r_ac / n);
  i_ac = sqrt(i_ac / n);
  if (i_ac < 1) return NAN;
  float R = (r_ac / r_dc) / (i_ac / i_dc);
  float spo2 = 110.f - 25.f * R;
  if (spo2 < COMPANION_SPO2_MIN || spo2 > COMPANION_SPO2_MAX) return NAN;
  return spo2;
}

void max30102_read(companion_reading_t *out) {
  uint8_t wr, rd;
  if (!read_reg(REG_FIFO_WR_PTR, &wr, 1) || !read_reg(REG_FIFO_RD_PTR, &rd, 1)) {
    out->max_state = COMP_SENSOR_ERROR;
    return;
  }
  uint8_t to_read = (wr - rd) & 0x1F;
  if (to_read == 0) {
    if (buf_n == 0) out->max_state = COMP_NO_SIGNAL;
    return;
  }
  if (to_read > 8) to_read = 8;
  for (uint8_t s = 0; s < to_read; s++) {
    uint8_t raw[6];
    if (!read_reg(REG_FIFO_DATA, raw, 6)) {
      out->max_state = COMP_SENSOR_ERROR;
      return;
    }
    uint32_t red = ((uint32_t)raw[0] << 16 | (uint32_t)raw[1] << 8 | raw[2]) & 0x3FFFF;
    uint32_t ir = ((uint32_t)raw[3] << 16 | (uint32_t)raw[4] << 8 | raw[5]) & 0x3FFFF;
    if (buf_n < 32) {
      red_buf[buf_n] = red;
      ir_buf[buf_n] = ir;
      buf_n++;
    } else {
      for (int i = 0; i < 31; i++) {
        red_buf[i] = red_buf[i + 1];
        ir_buf[i] = ir_buf[i + 1];
      }
      red_buf[31] = red;
      ir_buf[31] = ir;
    }
  }
  uint32_t ir_min = ir_buf[0], ir_max = ir_buf[0];
  for (uint8_t i = 1; i < buf_n; i++) {
    if (ir_buf[i] < ir_min) ir_min = ir_buf[i];
    if (ir_buf[i] > ir_max) ir_max = ir_buf[i];
  }
  if (ir_max < 15000) {
    out->max_state = COMP_NO_FINGER;
    out->ppg_quality = 0.05f;
    out->hr_valid = 0;
    out->spo2_valid = 0;
    return;
  }
  float span = (float)(ir_max - ir_min);
  out->ppg_quality = span / (span + 8000.f);
  if (buf_n < 24 || out->ppg_quality < COMPANION_SIGNAL_Q_MIN) {
    out->max_state = COMP_INVALID_READING;
    out->hr_valid = 0;
    out->spo2_valid = 0;
    return;
  }
  float hr = estimate_hr(ir_buf, buf_n);
  float spo2 = estimate_spo2(red_buf, ir_buf, buf_n);
  if (isnan(hr) || isnan(spo2)) {
    out->max_state = COMP_INVALID_READING;
    out->hr_valid = 0;
    out->spo2_valid = 0;
    return;
  }
  out->hr = hr;
  out->spo2 = spo2;
  out->hr_valid = 1;
  out->spo2_valid = 1;
  out->max_state = COMP_OK;
}

#else
uint8_t max30102_begin() { return 0; }
void max30102_read(companion_reading_t *out) {
  out->max_state = COMP_SENSOR_ERROR;
}
#endif
