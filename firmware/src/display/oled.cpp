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

void oled_show_health(float hr, float spo2, float temp, companion_health_status_t st, uint8_t demo) {
  const char *s = st == HEALTH_ELEVATED ? "ELEVATED" : st == HEALTH_RECHECK ? "RECHECK" : st == HEALTH_NORMAL ? "NORMAL" : "RECHECK";
  char l1[32], l2[32], l3[32], l4[32];
  snprintf(l1, sizeof l1, "HR: %.0f", hr);
  snprintf(l2, sizeof l2, "SpO2: %.0f%%", spo2);
  snprintf(l3, sizeof l3, "TEMP: %.1fC", temp);
  snprintf(l4, sizeof l4, "STATUS: %s", s);
  if (demo) Serial.println("DEMO MODE / SIMULATED DATA");
  oled_text_serial("HEALTH", l1, l2, l3, l4);
  (void)oled_ok;
}

void oled_show_env(float t, float h, companion_air_status_t air) {
  const char *a = air == AIR_HIGH ? "HIGH" : air == AIR_ELEVATED ? "ELEVATED" : air == AIR_NORMAL ? "NORMAL" : "WARMING";
  char l1[32], l2[32], l3[32];
  snprintf(l1, sizeof l1, "TEMP: %.1fC", t);
  snprintf(l2, sizeof l2, "HUM: %.0f%%", h);
  snprintf(l3, sizeof l3, "AIR: %s", a);
  oled_text_serial("ENVIRONMENT", l1, l2, l3, "");
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
void oled_show_health(float, float, float, companion_health_status_t, uint8_t) {}
void oled_show_env(float, float, companion_air_status_t) {}
void oled_show_flood(const char *, float, companion_flood_status_t, uint8_t, uint8_t) {}
#endif
