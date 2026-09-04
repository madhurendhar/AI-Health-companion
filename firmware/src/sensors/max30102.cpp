#include "companion/sensors/max30102.h"
#include "companion/config.h"

#if defined(ARDUINO)
#include <Arduino.h>
#include <Wire.h>
#include <math.h>
#include <string.h>
#include "MAX30105.h"
#include "heartRate.h"

#define MIN_IR_VALUE 10000L
#define RATE_SIZE 8
#define SPO2_BUFFER_SIZE 100

static MAX30105 particleSensor;
static uint8_t sensor_ready = 0;
static uint32_t total_samples = 0;
static uint8_t last_fifo_wr = 0;
static uint8_t last_fifo_rd = 0;
static uint8_t last_intr = 0;

static byte rates[RATE_SIZE];
static byte rateSpot = 0;
static long lastBeat = 0;
static float heartRate = 0;

static uint32_t irBuffer[SPO2_BUFFER_SIZE];
static uint32_t redBuffer[SPO2_BUFFER_SIZE];
static byte spo2Index = 0;
static float spo2 = 0;
static bool spo2Valid = false;
static uint32_t last_ir = 0;

static float ema_hr = 0.f;
static float ema_spo2 = 0.f;
static uint8_t ema_ok = 0;

static void calculateSpO2() {
  if (spo2Index < SPO2_BUFFER_SIZE) return;

  double irDC = 0, redDC = 0;
  for (int i = 0; i < SPO2_BUFFER_SIZE; i++) {
    irDC += irBuffer[i];
    redDC += redBuffer[i];
  }
  irDC /= SPO2_BUFFER_SIZE;
  redDC /= SPO2_BUFFER_SIZE;
  if (irDC <= 0 || redDC <= 0) {
    spo2Valid = false;
    spo2Index = 0;
    return;
  }

  double irAC = 0, redAC = 0;
  for (int i = 0; i < SPO2_BUFFER_SIZE; i++) {
    double irDiff = irBuffer[i] - irDC;
    double redDiff = redBuffer[i] - redDC;
    irAC += irDiff * irDiff;
    redAC += redDiff * redDiff;
  }
  irAC = sqrt(irAC / SPO2_BUFFER_SIZE);
  redAC = sqrt(redAC / SPO2_BUFFER_SIZE);
  if (irAC <= 0 || redAC <= 0) {
    spo2Valid = false;
    spo2Index = 0;
    return;
  }

  double R = (redAC / redDC) / (irAC / irDC);
  float calculated = (float)(-45.060 * R * R + 30.354 * R + 94.845);
  if (calculated >= COMPANION_SPO2_MIN && calculated <= COMPANION_SPO2_MAX) {
    spo2 = calculated;
    spo2Valid = true;
  } else {
    spo2Valid = false;
  }
  spo2Index = 0;
}

uint8_t max30102_begin() {
  sensor_ready = 0;
  spo2Index = 0;
  spo2Valid = false;
  heartRate = 0;
  ema_ok = 0;
  last_ir = 0;
  total_samples = 0;
  memset(rates, 0, sizeof rates);

  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("MAX30102: begin failed");
    return 0;
  }

  particleSensor.setup(120, 4, 2, 100, 411, 16384);
  particleSensor.setPulseAmplitudeRed(60);
  particleSensor.setPulseAmplitudeIR(60);
  particleSensor.setPulseAmplitudeGreen(0);

  sensor_ready = 1;
  Serial.println("MAX30102: SparkFun library OK");
  return 1;
}

void max30102_read(companion_reading_t *out) {
  out->hr_valid = 0;
  out->spo2_valid = 0;
  out->ppg_buf_n = spo2Index;
  out->ppg_ir_peak = last_ir;
  out->ppg_quality = 0;
  out->max_state = COMP_NO_SIGNAL;

  if (!sensor_ready) {
    out->max_state = COMP_SENSOR_ERROR;
    return;
  }

  uint8_t finger = 0;
  particleSensor.check();
  while (particleSensor.available()) {
    uint32_t currentIR = particleSensor.getIR();
    uint32_t currentRed = particleSensor.getRed();
    total_samples++;
    last_ir = currentIR;
    out->ppg_ir_peak = currentIR;

    if (currentIR > (uint32_t)MIN_IR_VALUE) {
      finger = 1;
      out->ppg_quality = 0.85f;

      if (spo2Index < SPO2_BUFFER_SIZE) {
        irBuffer[spo2Index] = currentIR;
        redBuffer[spo2Index] = currentRed;
        spo2Index++;
      }

      if (checkForBeat(currentIR)) {
        long now = millis();
        long delta = now - lastBeat;
        lastBeat = now;
        if (delta > 250 && delta < 1500) {
          float bpm = 60000.0f / (float)delta;
          if (bpm >= COMPANION_HR_MIN && bpm <= COMPANION_HR_MAX) {
            rates[rateSpot++] = (byte)bpm;
            rateSpot %= RATE_SIZE;
            int total = 0, count = 0;
            for (byte i = 0; i < RATE_SIZE; i++) {
              if (rates[i] > 0) {
                total += rates[i];
                count++;
              }
            }
            if (count > 0) heartRate = (float)(total / count);
          }
        }
      }
    } else {
      heartRate = 0;
      spo2Valid = false;
      spo2Index = 0;
      ema_ok = 0;
      memset(rates, 0, sizeof rates);
    }

    particleSensor.nextSample();
  }

  if (spo2Index >= SPO2_BUFFER_SIZE) calculateSpO2();
  out->ppg_buf_n = spo2Index;
  out->ppg_ir_peak = last_ir;

  if (!finger && last_ir < (uint32_t)MIN_IR_VALUE) {
    out->max_state = COMP_NO_FINGER;
    out->ppg_quality = 0.05f;
    return;
  }

  if (heartRate > 0) {
    ema_hr = ema_ok ? (0.4f * heartRate + 0.6f * ema_hr) : heartRate;
    out->hr = ema_hr;
    out->hr_valid = 1;
  }

  if (spo2Valid) {
    ema_spo2 = ema_ok ? (0.4f * spo2 + 0.6f * ema_spo2) : spo2;
    out->spo2 = ema_spo2;
    out->spo2_valid = 1;
  }

  if (out->hr_valid && out->spo2_valid) ema_ok = 1;

  if (out->hr_valid || out->spo2_valid) {
    out->max_state = COMP_OK;
    out->ppg_quality = 0.85f;
  } else {
    out->max_state = COMP_NO_SIGNAL;
    out->ppg_quality = 0.5f;
  }
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
