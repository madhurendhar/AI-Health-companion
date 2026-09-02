#include "companion/display/oled.h"
#include "companion/config.h"

#if defined(ARDUINO)
#include <Arduino.h>
#include <Wire.h>
#include <stdio.h>

static void ssd_cmd(uint8_t c) {
  Wire.beginTransmission(COMPANION_OLED_ADDR);
  Wire.write(0x00);
  Wire.write(c);
  Wire.endTransmission();
}

static uint8_t oled_ok = 0;

void oled_begin() {
  Wire.beginTransmission(COMPANION_OLED_ADDR);
  if (Wire.endTransmission() != 0) {
    oled_ok = 0;
    return;
  }
  oled_ok = 1;
  ssd_cmd(0xAE);
  ssd_cmd(0xAF);
}

static void oled_text_serial(const char *title, const char *l1, const char *l2, const char *l3, const char *l4) {
  Serial.println(title);
  Serial.println(l1);
  Serial.println(l2);
  Serial.println(l3);
  Serial.println(l4);
}

static const char *max_hint(const companion_reading_t *r) {
  if (!r) return "";
  if (r->hr_valid) return "";
  switch (r->max_state) {
    case COMP_NO_FINGER: return " (place finger)";
    case COMP_NO_SIGNAL: {
      static char buf[28];
      snprintf(buf, sizeof buf, " (buf %u/%u)", (unsigned)r->ppg_buf_n,
               (unsigned)COMPANION_MAX30102_HR_MIN_SAMPLES);
      return buf;
    }
    case COMP_INVALID_READING: return " (hold still)";
    case COMP_SENSOR_ERROR: return " (check wiring)";
    default: return " (no PPG)";
  }
}

void oled_show_health(const companion_reading_t *r, companion_health_status_t st, uint8_t demo) {
  const char *s = st == HEALTH_ELEVATED ? "ELEVATED" : st == HEALTH_RECHECK ? "RECHECK" : st == HEALTH_NORMAL ? "NORMAL" : "INSUFFICIENT";
  char l1[40], l2[40], l3[32], l4[32], hint[24];
  hint[0] = '\0';
  if (r && !r->hr_valid) {
    strncpy(hint, max_hint(r), sizeof hint - 1);
    hint[sizeof hint - 1] = '\0';
  }
  if (r->hr_valid) {
    snprintf(l1, sizeof l1, "HR: %.0f", r->hr);
  } else {
    snprintf(l1, sizeof l1, "HR: --%s", hint);
  }
  if (r && r->spo2_valid) {
    snprintf(l2, sizeof l2, "SpO2: %.0f%%", r->spo2);
  } else {
    snprintf(l2, sizeof l2, "SpO2: --%s", hint);
  }
  if (r && r->temp_valid) {
    snprintf(l3, sizeof l3, "TEMP: %.1fC", r->object_temp_c);
  } else {
    snprintf(l3, sizeof l3, "TEMP: --");
  }
  snprintf(l4, sizeof l4, "STATUS: %s", s);
  if (r && !r->hr_valid && r->ppg_ir_peak > 0) {
    char dbg[40];
    snprintf(dbg, sizeof dbg, "IR peak: %lu", (unsigned long)r->ppg_ir_peak);
    if (demo) Serial.println("DEMO MODE / SIMULATED DATA");
    oled_text_serial("HEALTH", l1, l2, l3, l4);
    Serial.println(dbg);
    (void)oled_ok;
    return;
  }
  if (demo) Serial.println("DEMO MODE / SIMULATED DATA");
  oled_text_serial("HEALTH", l1, l2, l3, l4);
  (void)oled_ok;
}

void oled_show_env(const companion_reading_t *r, companion_air_status_t air) {
  const char *a = air == AIR_HIGH ? "HIGH" : air == AIR_ELEVATED ? "ELEVATED" : air == AIR_NORMAL ? "NORMAL" : "WARMING";
  char l1[32], l2[32], l3[32], l4[32];
  if (r && r->dht_valid) {
    snprintf(l1, sizeof l1, "TEMP: %.1fC", r->dht_temp_c);
    snprintf(l2, sizeof l2, "HUM: %.0f%%", r->humidity);
  } else if (r && r->temp_valid) {
    snprintf(l1, sizeof l1, "TEMP: %.1fC (MLX)", r->object_temp_c);
    snprintf(l2, sizeof l2, "HUM: -- (no DHT)");
  } else {
    snprintf(l1, sizeof l1, "TEMP: --");
    snprintf(l2, sizeof l2, "HUM: --");
  }
  if (r && r->mq_valid) {
    snprintf(l3, sizeof l3, "AIR: %s (%.2f)", a, r->mq135_relative);
  } else {
    snprintf(l3, sizeof l3, "AIR: %s", a);
  }
  snprintf(l4, sizeof l4, "MQ135: %s", r && r->mq_valid ? "OK" : "warming");
  oled_text_serial("ENVIRONMENT", l1, l2, l3, l4);
}

void oled_show_calibrating(uint16_t good, uint16_t need, const char *msg) {
  char l1[40], l2[32], l3[32];
  snprintf(l1, sizeof l1, "CALIBRATING");
  snprintf(l2, sizeof l2, "samples %u/%u", (unsigned)good, (unsigned)need);
  snprintf(l3, sizeof l3, "%s", msg ? msg : "hold still");
  oled_text_serial("BASELINE", l1, l2, l3, "MAX30102+MLX90614");
}

void oled_show_flood(const char *loc, float rain24, companion_flood_status_t st, uint8_t stale, uint8_t offline) {
  const char *s = st == FLOOD_HIGH ? "HIGH" : st == FLOOD_WATCH ? "WATCH" : "LOW";
  const char *data = offline ? "OFFLINE" : stale ? "STALE" : "LIVE";
  char l1[40], l2[32], l3[32], l4[32];
  snprintf(l1, sizeof l1, "LOC: %s", loc);
  snprintf(l2, sizeof l2, "RAIN24: %.1f mm", rain24);
  snprintf(l3, sizeof l3, "RISK: %s", s);
  snprintf(l4, sizeof l4, "DATA: %s", data);
  oled_text_serial("FLOOD RISK", l1, l2, l3, l4);
}
#else
void oled_begin() {}
void oled_show_health(const companion_reading_t *, companion_health_status_t, uint8_t) {}
void oled_show_env(const companion_reading_t *, companion_air_status_t) {}
void oled_show_calibrating(uint16_t, uint16_t, const char *) {}
void oled_show_flood(const char *, float, companion_flood_status_t, uint8_t, uint8_t) {}
#endif
