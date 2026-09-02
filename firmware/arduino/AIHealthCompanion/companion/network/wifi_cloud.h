#ifndef COMPANION_WIFI_CLOUD_H
#define COMPANION_WIFI_CLOUD_H
#include <stdint.h>
void companion_net_begin();
void companion_net_reconnect();
uint8_t companion_net_ok();
uint8_t companion_post_status(const char *json);
uint8_t companion_get_flood(char *out, int outlen, uint8_t demo_mode);
#endif
