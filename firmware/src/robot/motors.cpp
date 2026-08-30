#include "companion/robot/motors.h"
#include "companion/config.h"

#if defined(ARDUINO)
#include <Arduino.h>

void motors_begin() {
  pinMode(COMPANION_TB6612_AIN1, OUTPUT);
  pinMode(COMPANION_TB6612_AIN2, OUTPUT);
  pinMode(COMPANION_TB6612_BIN1, OUTPUT);
  pinMode(COMPANION_TB6612_BIN2, OUTPUT);
  pinMode(COMPANION_TB6612_STBY, OUTPUT);
  pinMode(COMPANION_TB6612_PWMA, OUTPUT);
  pinMode(COMPANION_TB6612_PWMB, OUTPUT);
  digitalWrite(COMPANION_TB6612_STBY, HIGH);
  motors_stop();
}

void motors_stop() {
  digitalWrite(COMPANION_TB6612_AIN1, LOW);
  digitalWrite(COMPANION_TB6612_AIN2, LOW);
  digitalWrite(COMPANION_TB6612_BIN1, LOW);
  digitalWrite(COMPANION_TB6612_BIN2, LOW);
  analogWrite(COMPANION_TB6612_PWMA, 0);
  analogWrite(COMPANION_TB6612_PWMB, 0);
}

static void drive(int a1, int a2, int b1, int b2, uint8_t pwm) {
  digitalWrite(COMPANION_TB6612_AIN1, a1);
  digitalWrite(COMPANION_TB6612_AIN2, a2);
  digitalWrite(COMPANION_TB6612_BIN1, b1);
  digitalWrite(COMPANION_TB6612_BIN2, b2);
  analogWrite(COMPANION_TB6612_PWMA, pwm);
  analogWrite(COMPANION_TB6612_PWMB, pwm);
}

void motors_forward(uint8_t pwm) { drive(HIGH, LOW, HIGH, LOW, pwm); }
void motors_backward(uint8_t pwm) { drive(LOW, HIGH, LOW, HIGH, pwm); }
void motors_left(uint8_t pwm) { drive(LOW, HIGH, HIGH, LOW, pwm); }
void motors_right(uint8_t pwm) { drive(HIGH, LOW, LOW, HIGH, pwm); }
#else
void motors_begin() {}
void motors_stop() {}
void motors_forward(uint8_t) {}
void motors_backward(uint8_t) {}
void motors_left(uint8_t) {}
void motors_right(uint8_t) {}
#endif
