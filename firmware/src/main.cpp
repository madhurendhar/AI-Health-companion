#include "companion/config.h"
#include "companion/types.h"
#include "companion/flood_sm.h"
#include "companion/display/oled.h"
#include "companion/network/wifi_cloud.h"

#if defined(ARDUINO)
#include <Arduino.h>
#include <stdio.h>
#include <string.h>
#include "companion_secrets.h"

static companion_flood_status_t flood = FLOOD_LOW;
static float rain24 = 0;
static uint8_t flood_stale = 1;
static uint8_t net_offline = 1;
static uint32_t last_poll = 0;
static uint8_t demo = COMPANION_DEMO_MODE;

static void buzz_flood(companion_flood_status_t st) {
  if (st == FLOOD_HIGH) tone(COMPANION_BUZZER_PIN, 1000, 400);
  else if (st == FLOOD_WATCH) tone(COMPANION_BUZZER_PIN, 750, 120);
}

static void parse_flood_body(const char *body) {
  if (strstr(body, "\"HIGH\"")) flood = FLOOD_HIGH;
  else if (strstr(body, "\"WATCH\"")) flood = FLOOD_WATCH;
  else flood = FLOOD_LOW;
  const char *r = strstr(body, "\"24h\":");
  if (r) rain24 = (float)atof(r + 6);
  flood_stale = strstr(body, "STALE") ? 1 : 0;
}

void setup() {
  Serial.begin(115200);
  pinMode(COMPANION_LED_PIN, OUTPUT);
  pinMode(COMPANION_BUZZER_PIN, OUTPUT);
  oled_begin();
  companion_net_begin();
  net_offline = !companion_net_ok();
  Serial.println("FLOOD EARLY-WARNING MODE (health subsystem disabled)");
  Serial.println("Not guaranteed flood detection.");
  if (demo) Serial.println("DEMO MODE / SIMULATED DATA");
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    if (c == 'd' || c == 'D') demo = 1;
    if (c == 'l' || c == 'L') demo = 0;
  }

  uint32_t now = millis();
  uint32_t interval = flood_poll_interval_s(flood) * 1000UL;
  if (now - last_poll > interval) {
    last_poll = now;
    char body[640];
    uint8_t ok = companion_get_flood(body, sizeof body, demo);
    net_offline = !companion_net_ok();
    if (ok) {
      companion_flood_status_t prev = flood;
      parse_flood_body(body);
      if (flood != prev) {
        buzz_flood(flood);
        digitalWrite(COMPANION_LED_PIN, flood == FLOOD_LOW ? LOW : HIGH);
      }
      flood_stale = 0;
    } else {
      flood_stale = 1;
      if (!net_offline) flood_stale = 1;
    }
  }

  oled_show_flood(COMPANION_LOCATION, rain24, flood, flood_stale, net_offline);
  delay(500);
}
#else
int main() { return 0; }
#endif
