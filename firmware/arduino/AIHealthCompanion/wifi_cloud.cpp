#include "companion/network/wifi_cloud.h"

#if defined(ARDUINO)
#if !defined(ARDUINO_ARCH_ESP32) && !defined(CONFIG_IDF_TARGET_ESP32)
#error "Select ESP32 board: Tools -> Board -> ESP32 Dev Module. Install esp32 by Espressif in Boards Manager."
#endif
#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include "companion_secrets.h"

static uint8_t net_ok = 0;

void companion_net_begin() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(COMPANION_WIFI_SSID, COMPANION_WIFI_PASS);
  uint32_t t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < 8000) delay(200);
  net_ok = WiFi.status() == WL_CONNECTED;
  if (net_ok) {
    Serial.print("WiFi OK IP=");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("WiFi FAILED - check SSID/password");
  }
}

void companion_net_reconnect() {
  if (WiFi.status() == WL_CONNECTED) return;
  Serial.println("WiFi reconnecting...");
  WiFi.disconnect();
  WiFi.begin(COMPANION_WIFI_SSID, COMPANION_WIFI_PASS);
  uint32_t t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < 10000) delay(200);
  net_ok = WiFi.status() == WL_CONNECTED;
  if (net_ok) {
    Serial.print("WiFi OK IP=");
    Serial.println(WiFi.localIP());
  }
}

uint8_t companion_net_ok() {
  net_ok = WiFi.status() == WL_CONNECTED;
  return net_ok;
}

uint8_t companion_post_status(const char *json) {
  if (!companion_net_ok()) return 0;
  HTTPClient http;
  String url = String(COMPANION_BACKEND_URL) + "/device/status";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Api-Token", COMPANION_API_TOKEN);
  int code = http.POST(json);
  http.end();
  return code >= 200 && code < 300;
}

uint8_t companion_get_flood(char *out, int outlen, uint8_t demo_mode) {
  if (!companion_net_ok()) return 0;
  HTTPClient http;
  String url = String(COMPANION_BACKEND_URL) + "/flood/status?location=" + String(COMPANION_LOCATION);
  if (demo_mode) url += "&demo=true";
  http.begin(url);
  int code = http.GET();
  if (code != 200) {
    http.end();
    return 0;
  }
  String body = http.getString();
  http.end();
  body.toCharArray(out, outlen);
  return 1;
}
#else
void companion_net_begin() {}
void companion_net_reconnect() {}
uint8_t companion_net_ok() { return 0; }
uint8_t companion_post_status(const char *) { return 0; }
uint8_t companion_get_flood(char *, int, uint8_t) { return 0; }
#endif
