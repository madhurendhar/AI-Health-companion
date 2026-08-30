#include "companion/flood_sm.h"
#include "companion/config.h"

static companion_flood_status_t st = FLOOD_LOW;
static uint32_t last_change = 0;

companion_flood_status_t flood_sm_update(float score, uint32_t now_s) {
  if (now_s - last_change < COMPANION_FLOOD_COOLDOWN_S && st != FLOOD_LOW) {
    if (st == FLOOD_WATCH && score >= COMPANION_FLOOD_HIGH) {
      st = FLOOD_HIGH;
      last_change = now_s;
    }
    return st;
  }
  companion_flood_status_t nxt = st;
  if (st == FLOOD_LOW) {
    if (score >= COMPANION_FLOOD_HIGH) nxt = FLOOD_HIGH;
    else if (score >= COMPANION_FLOOD_WATCH) nxt = FLOOD_WATCH;
  } else if (st == FLOOD_WATCH) {
    if (score >= COMPANION_FLOOD_HIGH) nxt = FLOOD_HIGH;
    else if (score < COMPANION_FLOOD_WATCH - COMPANION_FLOOD_HYST) nxt = FLOOD_LOW;
  } else {
    if (score < COMPANION_FLOOD_HIGH - COMPANION_FLOOD_HYST) nxt = FLOOD_WATCH;
  }
  if (nxt != st) {
    st = nxt;
    last_change = now_s;
  }
  return st;
}

uint32_t flood_poll_interval_s(companion_flood_status_t s) {
  if (s == FLOOD_HIGH) return 300;
  if (s == FLOOD_WATCH) return 720;
  return 1800;
}
