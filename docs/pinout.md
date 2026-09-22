# Pinbelegung und Hardwarestand (ESP32)

Stand: 20.09.2026. Board: **ESP32-WROOM-32**. Der frueher hier dokumentierte
Arduino-Uno-Stand ist archiviert (`software/`).

## Motoren (ULN2003)

### Azimut-Motor

| ULN2003 Eingang | ESP32-GPIO |
| --- | --- |
| IN1 | 16 |
| IN2 | 17 |
| IN3 | 18 |
| IN4 | 19 |

### Elevations-Motor

| ULN2003 Eingang | ESP32-GPIO |
| --- | --- |
| IN1 | 25 |
| IN2 | 26 |
| IN3 | 27 |
| IN4 | 14 |

4096 Halbschritte pro Umdrehung; 1 Motorumdrehung = 360 Grad Panelbewegung
(kein zusaetzliches Getriebe). Motoren werden nach jeder Fahrt abgeschaltet.

## Endschalter

| Schalter | GPIO |
| --- | --- |
| Azimut MIN | 4 |
| Azimut MAX | 5 |
| Elevation MIN | 15 |
| Elevation MAX | 12 |

Alle `INPUT_PULLUP`: offen = `HIGH`, gegen GND geschlossen = `LOW`.
**Achtung:** GPIO 12 und 15 sind Strapping-Pins; beim Flashen stoeren
angeschlossene Leitungen moeglicherweise den Upload.

## Joystick

| Signal | GPIO |
| --- | --- |
| X | 34 |
| Y | 35 |
| Taster (SW) | 13 |

Hinweis: GPIO 12 ist zugleich Elevation-MAX. Der Joystick-Taster darf im
Standalone-Betrieb nicht gleichzeitig auf GPIO 12 liegen.

## LCD und RTC (I2C)

| Signal | GPIO |
| --- | --- |
| SDA | 21 |
| SCL | 22 |

- 16x2-LCD, `LiquidCrystal I2C`, Adresse `0x27`
- DS3231 RTC, Adresse `0x68`

## Stromversorgung

- Motoren nicht ueber den 5-V-Pin des ESP32 speisen.
- Externes 5-V-Netzteil mit gemeinsamer Masse verwenden.
- Motoren nach Bewegung abschalten (nicht warm werden lassen).

## Schrittberechnung

```cpp
const int STEPS_PER_REV = 4096;
const float STEPS_PER_DEGREE = 4096.0 / 360.0; // ca. 11,38 Schritte/Grad
```

Die Firmware 0.4.3 verwendet einen **5-ms-Schritttakt**. Bei 3 ms verlor der
belastete 28BYJ-48 Schritte.
