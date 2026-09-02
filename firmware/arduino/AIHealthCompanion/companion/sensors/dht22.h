#ifndef COMPANION_DHT22_H
#define COMPANION_DHT22_H
#include "../types.h"
#include <stdint.h>
uint8_t dht22_begin();
void dht22_read(companion_reading_t *out);
#endif
