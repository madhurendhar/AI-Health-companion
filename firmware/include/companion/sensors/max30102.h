#ifndef COMPANION_MAX30102_H
#define COMPANION_MAX30102_H

#include "companion/types.h"
#include <stdint.h>

uint8_t max30102_begin();
void max30102_read(companion_reading_t *out);

#endif
