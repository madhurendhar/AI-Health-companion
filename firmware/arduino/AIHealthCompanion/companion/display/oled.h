#ifndef COMPANION_OLED_H
#define COMPANION_OLED_H
#include "../types.h"
void oled_begin();
void oled_show_health(const companion_reading_t *r, companion_health_status_t st, uint8_t demo);
void oled_show_env(const companion_reading_t *r, companion_air_status_t air);
void oled_show_calibrating(uint16_t good, uint16_t need, const char *msg);
void oled_show_flood(const char *loc, float rain24, companion_flood_status_t st, uint8_t stale, uint8_t offline);
#endif
