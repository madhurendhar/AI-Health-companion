#ifndef COMPANION_MQ135_H
#define COMPANION_MQ135_H
#include "companion/types.h"
#include <stdint.h>
void mq135_begin();
void mq135_read(companion_reading_t *out, companion_air_status_t *air);
#endif
