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
#define REG_FIFO_OVF 0x05
#define REG_FIFO_DATA 0x07
#define REG_FIFO_CONFIG 0x08
#define REG_MODE_CONFIG 0x09
#define REG_SPO2_CONFIG 0x0A
#define REG_LED1_PA 0x0C
#define REG_LED2_PA 0x0D
#define REG_PILOT_PA 0x10
#define REG_MULTI_LED_CTRL1 0x11
#define REG_MULTI_LED_CTRL2 0x12
#define REG_PART_ID 0xFF

static uint32_t ir_buf[COMPANION_MAX30102_BUF_SIZE];
static uint32_t red_buf[COMPANION_MAX30102_BUF_SIZE];
static uint16_t buf_n = 0;
static uint32_t total_samples = 0;
static uint8_t sensor_ready = 0;
static uint8_t last_fifo_wr = 0;
static uint8_t last_fifo_rd = 0;
static uint8_t last_intr = 0;
static float ema_hr = 0.f;
static float ema_spo2 = 0.f;
static uint8_t ema_ok = 0;

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

static void push_sample(uint32_t red, uint32_t ir) {
  if (buf_n < COMPANION_MAX30102_BUF_SIZE) {
    red_buf[buf_n] = red;
    ir_buf[buf_n] = ir;
    buf_n++;
  } else {
    for (uint16_t i = 0; i < COMPANION_MAX30102_BUF_SIZE - 1; i++) {
      red_buf[i] = red_buf[i + 1];
      ir_buf[i] = ir_buf[i + 1];
    }
    red_buf[COMPANION_MAX30102_BUF_SIZE - 1] = red;
    ir_buf[COMPANION_MAX30102_BUF_SIZE - 1] = ir;
  }
  total_samples++;
}

static uint8_t read_fifo_sample() {
  uint8_t raw[6];
  if (!read_reg(REG_FIFO_DATA, raw, 6)) return 0;
  uint32_t red = ((uint32_t)raw[0] << 16 | (uint32_t)raw[1] << 8 | raw[2]) & 0x3FFFF;
  uint32_t ir = ((uint32_t)raw[3] << 16 | (uint32_t)raw[4] << 8 | raw[5]) & 0x3FFFF;
  push_sample(red, ir);
  return 1;
}

static void drain_fifo_all() {
  for (;;) {
    uint8_t wr = 0, rd = 0;
    if (!read_reg(REG_FIFO_WR_PTR, &wr, 1) || !read_reg(REG_FIFO_RD_PTR, &rd, 1)) break;
    last_fifo_wr = wr;
    last_fifo_rd = rd;
    uint8_t n = (wr - rd) & 0x1F;
    if (n == 0) break;
    if (!read_fifo_sample()) break;
  }
}

static float estimate_hr(const uint32_t *ir, uint16_t n) {
  if (n < COMPANION_MAX30102_HR_MIN_SAMPLES) return NAN;

  double mean = 0;
  for (uint16_t i = 0; i < n; i++) mean += ir[i];
  mean /= (double)n;

  float best_corr = -1.f;
  int best_lag = 0;
  const int lag_min = (int)((float)COMPANION_MAX30102_SAMPLE_HZ * 60.f / COMPANION_HR_MAX);
  const int lag_max = (int)((float)COMPANION_MAX30102_SAMPLE_HZ * 60.f / COMPANION_HR_MIN);
  if (lag_min < 8) return NAN;
  if (lag_max >= (int)n - 8) return NAN;

  for (int lag = lag_min; lag <= lag_max; lag++) {
    double corr = 0, e1 = 0, e2 = 0;
    for (uint16_t i = 0; i < n - (uint16_t)lag; i++) {
      double a = (double)ir[i] - mean;
      double b = (double)ir[i + lag] - mean;
      corr += a * b;
      e1 += a * a;
      e2 += b * b;
    }
    if (e1 < 1 || e2 < 1) continue;
    float c = (float)(corr / sqrt(e1 * e2));
    if (c > best_corr) {
      best_corr = c;
      best_lag = lag;
    }
  }
  if (best_lag < lag_min || best_corr < 0.25f) return NAN;
  return 60.f * (float)COMPANION_MAX30102_SAMPLE_HZ / (float)best_lag;
}

static float estimate_spo2(const uint32_t *red, const uint32_t *ir, uint16_t n) {
  if (n < 30) return NAN;
  double r_dc = 0, i_dc = 0;
  for (uint16_t i = 0; i < n; i++) {
    r_dc += red[i];
    i_dc += ir[i];
  }
  r_dc /= n;
  i_dc /= n;
  if (r_dc < 300 || i_dc < 300) return NAN;
  double r_ac = 0, i_ac = 0;
  for (uint16_t i = 0; i < n; i++) {
    double rd = (double)red[i] - r_dc;
    double id = (double)ir[i] - i_dc;
    r_ac += rd * rd;
    i_ac += id * id;
  }
  r_ac = sqrt(r_ac / n);
  i_ac = sqrt(i_ac / n);
  if (i_ac < 0.5) return NAN;
  float R = (float)((r_ac / r_dc) / (i_ac / i_dc));
  float spo2 = -45.060f * R * R + 30.354f * R + 94.845f;
  if (spo2 < COMPANION_SPO2_MIN || spo2 > COMPANION_SPO2_MAX) return NAN;
  return spo2;
}

static void configure_sensor() {
  write_reg(REG_MODE_CONFIG, 0x40);
  delay(100);
  write_reg(REG_INTR_STATUS_1, 0xFF);
  write_reg(REG_FIFO_OVF, 0x00);
  write_reg(REG_FIFO_WR_PTR, 0x00);
  write_reg(REG_FIFO_RD_PTR, 0x00);
  write_reg(REG_FIFO_CONFIG, 0x0F);
  write_reg(REG_SPO2_CONFIG, COMPANION_MAX30102_SPO2_CONFIG);
  write_reg(REG_MULTI_LED_CTRL1, 0x21);
  write_reg(REG_MULTI_LED_CTRL2, 0x00);
  write_reg(REG_LED1_PA, COMPANION_MAX30102_LED_PA);
  write_reg(REG_LED2_PA, COMPANION_MAX30102_LED_PA);
  write_reg(REG_PILOT_PA, 0x1F);
  write_reg(REG_MODE_CONFIG, 0x03);
  sensor_ready = 1;
  Serial.printf("MAX30102 ready sr=%dHz led=0x%02X\n", COMPANION_MAX30102_SAMPLE_HZ, COMPANION_MAX30102_LED_PA);
}

static void evaluate_buffer(companion_reading_t *out) {
  out->ppg_buf_n = (uint8_t)(buf_n > 255 ? 255 : buf_n);
  out->hr_valid = 0;
  out->spo2_valid = 0;
  out->ppg_ir_peak = 0;

  if (!sensor_ready) {
    out->max_state = COMP_SENSOR_ERROR;
    return;
  }
  if (buf_n < COMPANION_MAX30102_BUF_MIN) {
    out->max_state = COMP_NO_SIGNAL;
    return;
  }

  uint32_t ir_min = ir_buf[0], ir_max = ir_buf[0];
  for (uint16_t i = 1; i < buf_n; i++) {
    if (ir_buf[i] < ir_min) ir_min = ir_buf[i];
    if (ir_buf[i] > ir_max) ir_max = ir_buf[i];
  }
  out->ppg_ir_peak = ir_max;

  if (ir_max < (uint32_t)COMPANION_MAX30102_FINGER_IR_MIN) {
    out->max_state = COMP_NO_FINGER;
    out->ppg_quality = (float)ir_max / (float)COMPANION_MAX30102_FINGER_IR_MIN * 0.25f;
    ema_ok = 0;
    return;
  }

  float span = (float)(ir_max - ir_min);
  out->ppg_quality = span / (span + 4000.f);
  if (out->ppg_quality < COMPANION_SIGNAL_Q_MIN) {
    out->max_state = COMP_INVALID_READING;
    return;
  }

  if (buf_n < COMPANION_MAX30102_HR_MIN_SAMPLES) {
    out->max_state = COMP_NO_SIGNAL;
    return;
  }

  float hr = estimate_hr(ir_buf, buf_n);
  float spo2 = estimate_spo2(red_buf, ir_buf, buf_n);

  if (!isnan(hr)) {
    ema_hr = ema_ok ? (0.35f * hr + 0.65f * ema_hr) : hr;
    out->hr = ema_hr;
    out->hr_valid = 1;
  } else if (ema_ok) {
    out->hr = ema_hr;
    out->hr_valid = 1;
  }

  if (!isnan(spo2)) {
    ema_spo2 = ema_ok ? (0.35f * spo2 + 0.65f * ema_spo2) : spo2;
    out->spo2 = ema_spo2;
    out->spo2_valid = 1;
  } else if (ema_ok) {
    out->spo2 = ema_spo2;
    out->spo2_valid = 1;
  }

  if (out->hr_valid && out->spo2_valid) ema_ok = 1;

  if (out->hr_valid || out->spo2_valid) {
    out->max_state = COMP_OK;
  } else {
    out->max_state = COMP_INVALID_READING;
  }
}

uint8_t max30102_begin() {
  Wire.beginTransmission(MAX30102_ADDR);
  if (Wire.endTransmission() != 0) return 0;
  uint8_t part[1] = {0};
  if (!read_reg(REG_PART_ID, part, 1)) return 0;
  if (part[0] != 0x15) {
    Serial.printf("MAX30102 part ID 0x%02X\n", part[0]);
  }
  buf_n = 0;
  total_samples = 0;
  ema_ok = 0;
  configure_sensor();
  delay(100);
  for (uint8_t i = 0; i < 60; i++) {
    drain_fifo_all();
    delay(20);
  }
  Serial.printf("MAX30102 warmup buf=%u total=%lu\n", (unsigned)buf_n, (unsigned long)total_samples);
  return 1;
}

void max30102_read(companion_reading_t *out) {
  if (!sensor_ready) {
    out->max_state = COMP_SENSOR_ERROR;
    out->hr_valid = 0;
    out->spo2_valid = 0;
    return;
  }

  uint8_t st[1] = {0};
  read_reg(REG_INTR_STATUS_1, st, 1);
  last_intr = st[0];
  drain_fifo_all();
  evaluate_buffer(out);
}

void max30102_debug(uint8_t *wr, uint8_t *rd, uint8_t *intr) {
  if (wr) *wr = last_fifo_wr;
  if (rd) *rd = last_fifo_rd;
  if (intr) *intr = last_intr;
}

uint32_t max30102_total_samples() { return total_samples; }

#else
uint8_t max30102_begin() { return 0; }
void max30102_read(companion_reading_t *out) { out->max_state = COMP_SENSOR_ERROR; }
void max30102_debug(uint8_t *, uint8_t *, uint8_t *) {}
uint32_t max30102_total_samples() { return 0; }
#endif
