#ifndef COMPANION_AUDIO_H
#define COMPANION_AUDIO_H
/* Optional INMP441 / MAX98357A. Health monitoring does not depend on voice.
   No LLM on ESP32. Predefined phrases only. */
void audio_begin();
void audio_say_status(int health_status);
#endif
