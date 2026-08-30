#include "companion/audio/voice.h"
#if defined(ARDUINO)
#include <Arduino.h>
void audio_begin() { /* speaker/mic optional — not required */ }
void audio_say_status(int health_status) {
  (void)health_status;
}
#else
void audio_begin() {}
void audio_say_status(int) {}
#endif
