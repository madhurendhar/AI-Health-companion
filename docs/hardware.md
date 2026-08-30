# Hardware

Target: ESP32-WROOM-32 class, **4 MB flash**, **~520 KB SRAM**, **no PSRAM**.

| Function | Device | Pins (default) |
| --- | --- | --- |
| PPG HR/SpO2 | MAX30102 | I2C SDA 21, SCL 22, addr 0x57 |
| Non-contact temp screening | MLX90614 | same I2C, addr 0x5A |
| Ambient temp/humidity | DHT22 | GPIO 4 |
| Relative air indicator | MQ135 | GPIO 34 ADC |
| SD | SPI module | CS 5 (VSPI MOSI 23 MISO 19 SCK 18 typical) |
| OLED | SSD1306 | I2C 0x3C |
| Buzzer | passive | GPIO 15 |
| LED | status | GPIO 2 |
| Motors | TB6612FNG | PWMA 25 AIN1 26 AIN2 27 PWMB 14 BIN1 12 BIN2 13 STBY 33 |
| Servo (optional) | — | GPIO 32 |

Not used: HC-SR04, water-level sensors.

Voice (INMP441 / MAX98357A) is optional; firmware stub only. No on-device LLM.
