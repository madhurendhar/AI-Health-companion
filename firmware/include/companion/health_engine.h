#ifndef COMPANION_HEALTH_ENGINE_H
#define COMPANION_HEALTH_ENGINE_H

#include "companion/types.h"

void companion_baseline_init(companion_baseline_t *b);
void companion_baseline_update(companion_baseline_t *b, const companion_features_t *f, float risk);
float companion_heuristic_risk(const companion_features_t *f, const companion_baseline_t *b);
companion_health_status_t companion_health_status(float score, const companion_features_t *f);
float companion_clip01(float x);

#endif
