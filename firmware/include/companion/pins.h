#ifndef COMPANION_PINS_H
#define COMPANION_PINS_H

/*
 * AI Health Companion — ESP32 pin map (sensor MODULES)
 *
 *   MAX30102 module     VCC GND SDA SCL        -> 3.3V GND 21 22   (I2C 0x57)
 *   MLX90614 module     VCC GND SDA SCL        -> 3.3V GND 21 22   (I2C 0x5A)
 *   SSD1306 OLED module VCC GND SDA SCL        -> 3.3V GND 21 22   (I2C 0x3C, optional)
 *   DHT22 module        VCC GND DATA           -> 3.3V GND GPIO 4
 *   MQ135 module        VCC GND AO DO          -> 5V GND + 10k/10k divider -> GPIO 34
 *   microSD SPI module  VCC GND CS MOSI MISO SCK -> 3.3V GND 5 23 19 18
 *   Buzzer module       VCC GND SIG            -> 3.3V GND GPIO 15
 *
 * Full diagram: docs/circuit.md
 */

#define COMPANION_I2C_SDA 21
#define COMPANION_I2C_SCL 22
#define COMPANION_I2C_HZ 100000

#define COMPANION_MAX30102_ADDR 0x57
#define COMPANION_MLX90614_ADDR 0x5A
#define COMPANION_OLED_ADDR 0x3C

#define COMPANION_DHT_PIN 4
#define COMPANION_MQ135_PIN 34
#define COMPANION_BUZZER_PIN 15
#define COMPANION_LED_PIN 2

#define COMPANION_SD_SCK 18
#define COMPANION_SD_MISO 19
#define COMPANION_SD_MOSI 23
#define COMPANION_SD_CS 5

#define COMPANION_TB6612_PWMA 25
#define COMPANION_TB6612_AIN1 26
#define COMPANION_TB6612_AIN2 27
#define COMPANION_TB6612_PWMB 14
#define COMPANION_TB6612_BIN1 12
#define COMPANION_TB6612_BIN2 13
#define COMPANION_TB6612_STBY 33
#define COMPANION_SERVO_PIN 32

#endif
