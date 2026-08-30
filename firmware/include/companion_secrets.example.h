#pragma once
/* Copy to companion_secrets.h — never commit real secrets.
   firmware/include/companion_secrets.h is gitignored via pattern? We commit this example only. */

#ifndef COMPANION_SECRETS_H
#define COMPANION_SECRETS_H

#ifndef COMPANION_WIFI_SSID
#define COMPANION_WIFI_SSID "YOUR_WIFI_SSID"
#endif
#ifndef COMPANION_WIFI_PASS
#define COMPANION_WIFI_PASS "YOUR_WIFI_PASSWORD"
#endif
#ifndef COMPANION_BACKEND_URL
#define COMPANION_BACKEND_URL "http://192.168.1.10:8080"
#endif
#ifndef COMPANION_API_TOKEN
#define COMPANION_API_TOKEN "change-me-local-token"
#endif
#ifndef COMPANION_LOCATION
#define COMPANION_LOCATION "Chennai"
#endif

#endif
