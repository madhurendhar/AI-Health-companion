#ifndef COMPANION_MOTORS_H
#define COMPANION_MOTORS_H
#include <stdint.h>
void motors_begin();
void motors_stop();
void motors_forward(uint8_t pwm);
void motors_backward(uint8_t pwm);
void motors_left(uint8_t pwm);
void motors_right(uint8_t pwm);
#endif
