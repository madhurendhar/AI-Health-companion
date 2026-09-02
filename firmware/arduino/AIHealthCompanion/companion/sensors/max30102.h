#ifndef COMPANION_MAX30102_H
#define COMPANION_MAX30102_H

#include "../types.h"
#include <stdint.h>

uint8_t max30102_begin();
void max30102_read(companion_reading_t *out);
void max30102_debug(uint8_t *wr, uint8_t *rd, uint8_t *intr);
uint32_t max30102_total_samples();

#endif
