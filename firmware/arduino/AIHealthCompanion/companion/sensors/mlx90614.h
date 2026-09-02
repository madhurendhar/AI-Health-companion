#ifndef COMPANION_MLX90614_H
#define COMPANION_MLX90614_H
#include "../types.h"
#include <stdint.h>
uint8_t mlx90614_begin();
void mlx90614_read(companion_reading_t *out);
#endif
