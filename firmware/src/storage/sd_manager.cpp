#include "companion/storage/sd_manager.h"
#include "companion/config.h"

#if defined(ARDUINO)
#include <Arduino.h>
#include <SD.h>
#include <SPI.h>

static uint8_t g_sd = 0;

static void ensure_files() {
  if (!SD.exists("/patient")) SD.mkdir("/patient");
  if (!SD.exists("/patient/profile.json")) {
    File f = SD.open("/patient/profile.json", FILE_WRITE);
    if (f) {
      f.print("{\"note\":\"no personal identifiers stored\"}");
      f.close();
    }
  }
  if (!SD.exists("/patient/readings.csv")) {
    File f = SD.open("/patient/readings.csv", FILE_WRITE);
    if (f) {
      f.println("timestamp_s,hr,spo2,temperature,ambient_temp,humidity,mq135_relative,hr_dev,spo2_dev,temp_dev,signal_quality,risk_score,status");
      f.close();
    }
  }
  if (!SD.exists("/patient/events.csv")) {
    File f = SD.open("/patient/events.csv", FILE_WRITE);
    if (f) {
      f.println("timestamp_s,kind,detail");
      f.close();
    }
  }
}

uint8_t sd_begin() {
  SPI.begin();
  g_sd = SD.begin(COMPANION_SD_CS);
  if (g_sd) ensure_files();
  return g_sd;
}

uint8_t sd_ok(void) { return g_sd; }

void sd_write_baseline(const char *json) {
  if (!g_sd) return;
  File f = SD.open("/patient/baseline.json", FILE_WRITE);
  if (!f) {
    g_sd = 0;
    return;
  }
  f.print(json);
  f.close();
}

void sd_append_reading(const char *csv_line) {
  if (!g_sd) return;
  File f = SD.open("/patient/readings.csv", FILE_APPEND);
  if (!f) {
    g_sd = 0;
    return;
  }
  f.println(csv_line);
  f.close();
}

void sd_append_event(const char *csv_line) {
  if (!g_sd) return;
  File f = SD.open("/patient/events.csv", FILE_APPEND);
  if (!f) {
    g_sd = 0;
    return;
  }
  f.println(csv_line);
  f.close();
}
#else
uint8_t sd_begin() { return 0; }
uint8_t sd_ok(void) { return 0; }
void sd_write_baseline(const char *) {}
void sd_append_reading(const char *) {}
void sd_append_event(const char *) {}
#endif
