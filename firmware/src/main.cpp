/**
 * AI Health Companion — ESP32 firmware
 * Sensors: MAX30102, MLX90614, DHT22, MQ135
 * Edge ML: compact decision trees (health + optional flood)
 * Flood early-warning via WiFi backend (NWDP)
 *
 * ARDUINO IDE: Board MUST be "ESP32 Dev Module" (not Arduino Uno).
 */

#if defined(ARDUINO) && !defined(ARDUINO_ARCH_ESP32) && !defined(CONFIG_IDF_TARGET_ESP32)
#error "Wrong board selected. Tools -> Board -> ESP32 Dev Module. Install esp32 package in Boards Manager."
#endif

#include "companion/calibration.h"
#include "companion/config.h"
#include "companion/display/oled.h"
#include "companion/features.h"
#include "companion/flood_sm.h"
#include "companion/flood_tree_model.h"
#include "companion/health_engine.h"
#include "companion/health_tree_model.h"
#include "companion/network/wifi_cloud.h"
#include "companion/sensors/dht22.h"
#include "companion/sensors/max30102.h"
#include "companion/sensors/mlx90614.h"
#include "companion/sensors/mq135.h"
#include "companion/storage/sd_manager.h"
#include "companion/tree_infer.h"
#include "companion/types.h"
#include "companion_secrets.h"

#if defined(ARDUINO)
#include <Arduino.h>
#include <Wire.h>
#include <stdio.h>
#include <string.h>

static companion_baseline_t baseline;
static companion_calibration_t calibration;
static companion_feature_state_t feat_state;
static companion_flood_status_t flood = FLOOD_LOW;
static companion_health_status_t health_st = HEALTH_INSUFFICIENT;
static companion_air_status_t air_st = AIR_WARMING_UP;

static float rain24 = 0.f;
static float health_score = 0.f;
static uint8_t flood_stale = 1;
static uint8_t net_offline = 1;
static uint8_t demo = COMPANION_DEMO_MODE;
static uint8_t prev_abnormal = 0;
static uint8_t display_page = 0;

static uint32_t last_health_ms = 0;
static uint32_t last_dht_ms = 0;
static uint32_t last_flood_ms = 0;
static uint32_t last_display_ms = 0;
static uint32_t last_sd_ms = 0;
static uint32_t last_wifi_retry_ms = 0;
static uint32_t last_sensor_dbg_ms = 0;

static companion_reading_t reading;

static void buzz_health(companion_health_status_t st) {
  if (st == HEALTH_ELEVATED) tone(COMPANION_BUZZER_PIN, 880, 300);
  else if (st == HEALTH_RECHECK) tone(COMPANION_BUZZER_PIN, 600, 120);
}

static void buzz_flood(companion_flood_status_t st) {
  if (st == FLOOD_HIGH) tone(COMPANION_BUZZER_PIN, 1000, 400);
  else if (st == FLOOD_WATCH) tone(COMPANION_BUZZER_PIN, 750, 120);
}

static void save_baseline_sd() {
  char buf[160];
  snprintf(buf, sizeof buf,
           "{\"resting_hr\":%.1f,\"hr_range\":%.1f,\"typical_spo2\":%.1f,\"typical_temp\":%.1f,\"samples\":%u,\"ready\":%u}",
           baseline.resting_hr, baseline.hr_range, baseline.typical_spo2, baseline.typical_temp,
           (unsigned)baseline.samples, (unsigned)baseline.ready);
  sd_write_baseline(buf);
}

static void parse_flood_body(const char *body) {
  if (strstr(body, "\"HIGH\"")) flood = FLOOD_HIGH;
  else if (strstr(body, "\"WATCH\"")) flood = FLOOD_WATCH;
  else flood = FLOOD_LOW;
  const char *r = strstr(body, "\"24h\":");
  if (!r) r = strstr(body, "\"rain_24h\":");
  if (r) rain24 = (float)atof(r + 6);
  flood_stale = (strstr(body, "STALE") || strstr(body, "\"stale\":true")) ? 1 : 0;
}

static float combine_health_score(float heuristic, float tree_score) {
  return 0.55f * heuristic + 0.45f * tree_score;
}

static void poll_flood(uint32_t now_ms) {
  uint32_t interval = flood_poll_interval_s(flood) * 1000UL;
  if (now_ms - last_flood_ms < interval) return;
  last_flood_ms = now_ms;
  char body[768];
  if (!companion_get_flood(body, sizeof body, demo)) {
    flood_stale = 1;
    return;
  }
  companion_flood_status_t prev = flood;
  parse_flood_body(body);
  if (flood != prev) buzz_flood(flood);

  float fx[FLOOD_TREE_N_FEATURES];
  companion_flood_vector(rain24, fx, FLOOD_TREE_N_FEATURES);
  float tree = companion_tree_infer(FLOOD_TREE_NODES, FLOOD_TREE_N_NODES, fx, FLOOD_TREE_N_FEATURES);
  (void)tree;
}

static void read_sensors(uint32_t now_ms) {
  if (now_ms - last_dht_ms >= COMPANION_DHT_PERIOD_MS) {
    dht22_read(&reading);
    last_dht_ms = now_ms;
  }
  max30102_read(&reading);
  mlx90614_read(&reading);
  mq135_read(&reading, &air_st);
}

static void run_health_ml(uint32_t now_ms) {
  if (now_ms - last_health_ms < COMPANION_HEALTH_PERIOD_MS) return;
  last_health_ms = now_ms;

  if (calibration.phase == CALIBRATING) {
    companion_cal_feed(&calibration, &reading, now_ms);
    static uint32_t last_dbg = 0;
    if (now_ms - last_dbg > 3000) {
      last_dbg = now_ms;
      Serial.printf("CAL: samples %u/%u | MAX=%d q=%.2f HR=%.0f | MLX=%d | %s\n",
                    (unsigned)calibration.good_samples, (unsigned)COMPANION_CAL_MIN_SAMPLES,
                    (int)reading.max_state, reading.ppg_quality, reading.hr,
                    (int)reading.mlx_state, calibration.message);
    }
    if (calibration.phase == CAL_READY) {
      companion_cal_apply_baseline(&calibration, &baseline);
      save_baseline_sd();
      Serial.println("Baseline calibration complete");
    }
    return;
  }

  companion_features_t feats;
  companion_features_extract(&feat_state, &reading, &baseline, prev_abnormal, &feats);

  float h = companion_heuristic_risk(&feats, &baseline);
  float vec[HEALTH_TREE_N_FEATURES];
  companion_features_vector(&feats, vec, HEALTH_TREE_N_FEATURES);
  float tree = companion_tree_infer(HEALTH_TREE_NODES, HEALTH_TREE_N_NODES, vec, HEALTH_TREE_N_FEATURES);
  health_score = combine_health_score(h, tree);

  companion_health_status_t prev = health_st;
  health_st = companion_health_status(health_score, &feats);
  if (health_st != prev) buzz_health(health_st);

  if (baseline.ready) companion_baseline_update(&baseline, &feats, health_score);
  prev_abnormal = (health_st == HEALTH_RECHECK || health_st == HEALTH_ELEVATED) ? 1 : 0;

  if (now_ms - last_sd_ms >= COMPANION_SD_WRITE_MS && feats.valid) {
    last_sd_ms = now_ms;
    char line[192];
    snprintf(line, sizeof line, "%lu,%.1f,%.1f,%.1f,%.1f,%.1f,%.2f,%.2f,%.2f,%.2f,%.2f,%.3f,%d",
             (unsigned long)(now_ms / 1000UL), feats.hr, feats.spo2, feats.temperature, feats.ambient_temp,
             feats.humidity, feats.mq135_relative, feats.hr_dev, feats.spo2_dev, feats.temp_dev,
             feats.signal_quality, health_score, (int)health_st);
    sd_append_reading(line);
  }
}

static void update_display(uint32_t now_ms) {
  if (now_ms - last_display_ms < COMPANION_DISPLAY_MS) return;
  last_display_ms = now_ms;
  display_page = (display_page + 1) % 3;

  if (calibration.phase == CALIBRATING) {
    oled_show_calibrating(calibration.good_samples, COMPANION_CAL_MIN_SAMPLES, calibration.message);
    return;
  }

  if (display_page == 0) {
    oled_show_health(&reading, health_st, demo);
  } else if (display_page == 1) {
    oled_show_env(&reading, air_st);
  } else {
    oled_show_flood(COMPANION_LOCATION, rain24, flood, flood_stale, net_offline);
  }
}

static void i2c_scan() {
  Serial.printf("I2C scan (SDA=%d SCL=%d):\n", COMPANION_I2C_SDA, COMPANION_I2C_SCL);
  uint8_t found = 0;
  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.printf("  0x%02X", addr);
      if (addr == COMPANION_MAX30102_ADDR) Serial.print(" MAX30102");
      if (addr == COMPANION_MLX90614_ADDR) Serial.print(" MLX90614");
      if (addr == COMPANION_OLED_ADDR) Serial.print(" OLED");
      Serial.println();
      found++;
    }
  }
  if (!found) Serial.println("  (no devices — check wiring/power)");
}

void setup() {
  Serial.begin(115200);
  delay(300);
  Serial.println();
  Serial.println("========== AI HEALTH COMPANION ==========");
  Serial.println("PlatformIO | SparkFun MAX + Adafruit MLX/DHT + MQ135");
  pinMode(COMPANION_LED_PIN, OUTPUT);
  pinMode(COMPANION_BUZZER_PIN, OUTPUT);
  Wire.begin(COMPANION_I2C_SDA, COMPANION_I2C_SCL);
  Wire.setClock(COMPANION_I2C_HZ);
  delay(50);
  i2c_scan();

  memset(&reading, 0, sizeof reading);
  companion_baseline_init(&baseline);
  companion_cal_init(&calibration);
  companion_features_init(&feat_state);

  oled_begin();
  if (!max30102_begin()) {
    Serial.printf("MAX30102 FAILED — SDA=%d SCL=%d 3.3V GND\n", COMPANION_I2C_SDA, COMPANION_I2C_SCL);
  }
  if (!mlx90614_begin()) Serial.println("MLX90614 FAILED");
  if (!dht22_begin()) Serial.println("DHT22 FAILED");
  mq135_begin();
  if (!sd_begin()) Serial.println("SD card not detected (optional)");

  companion_net_begin();
  net_offline = !companion_net_ok();

  Serial.println("Ready. Place finger on MAX30102.");
  Serial.println("Pages: HEALTH -> ENVIRONMENT -> FLOOD every 3s");
  Serial.println("Keys: D=demo flood  L=live  C=calibrate  S=skip cal");
  if (demo) Serial.println("DEMO MODE / SIMULATED DATA");
}

void loop() {
  uint32_t now = millis();

  if (Serial.available()) {
    char c = Serial.read();
    if (c == 'd' || c == 'D') demo = 1;
    if (c == 'l' || c == 'L') demo = 0;
    if (c == 'c' || c == 'C') {
      companion_cal_start(&calibration, now);
      baseline.ready = 0;
    }
    if (c == 's' || c == 'S') {
      baseline.ready = 1;
      calibration.phase = CAL_IDLE;
      Serial.println("Calibration skipped — using default baseline");
    }
  }

  net_offline = !companion_net_ok();
  if (net_offline && now - last_wifi_retry_ms > 30000) {
    last_wifi_retry_ms = now;
    companion_net_reconnect();
    net_offline = !companion_net_ok();
  }
  read_sensors(now);

  if (now - last_sensor_dbg_ms > 4000) {
    last_sensor_dbg_ms = now;
    Serial.printf("SENS: MAX=%d buf=%u tot=%lu IR=%lu q=%.2f HR=%.0f(%d) SpO2=%.0f(%d) | MLX=%.1f | DHT=%d | MQ=%d\n",
                  (int)reading.max_state, (unsigned)reading.ppg_buf_n,
                  (unsigned long)max30102_total_samples(), (unsigned long)reading.ppg_ir_peak,
                  reading.ppg_quality, reading.hr, (int)reading.hr_valid, reading.spo2,
                  (int)reading.spo2_valid, reading.object_temp_c, (int)reading.dht_valid,
                  (int)reading.mq_valid);
  }

  run_health_ml(now);
  poll_flood(now);
  update_display(now);

  if (health_st == HEALTH_ELEVATED || flood == FLOOD_HIGH) digitalWrite(COMPANION_LED_PIN, HIGH);
  else digitalWrite(COMPANION_LED_PIN, LOW);

  delay(5);
}
#else
int main() { return 0; }
#endif
