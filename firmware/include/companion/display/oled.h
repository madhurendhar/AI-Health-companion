#ifndef COMPANION_OLED_H
#define COMPANION_OLED_H
#include "companion/types.h"
void oled_begin();
void oled_show_health(float hr, float spo2, float temp, companion_health_status_t st, uint8_t demo);
void oled_show_env(float t, float h, companion_air_status_t air);
void oled_show_flood(const char *loc, float rain24, companion_flood_status_t st, uint8_t stale, uint8_t offline);
#endif
