#ifndef COMPANION_SD_MANAGER_H
#define COMPANION_SD_MANAGER_H
#include <stdint.h>
uint8_t sd_begin();
uint8_t sd_ok(void);
void sd_write_baseline(const char *json);
void sd_append_reading(const char *csv_line);
void sd_append_event(const char *csv_line);
#endif
