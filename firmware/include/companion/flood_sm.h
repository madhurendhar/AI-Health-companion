#ifndef COMPANION_FLOOD_SM_H
#define COMPANION_FLOOD_SM_H
#include "companion/types.h"
companion_flood_status_t flood_sm_update(float score, uint32_t now_s);
uint32_t flood_poll_interval_s(companion_flood_status_t st);
#endif
