# Hardwaretest-Konzept (ESP32)

Vor jedem neuen Softwaremodul wird die betroffene Hardware einzeln getestet.
Eigenstaendige Sketche liegen unter `esp32SolarTracker/tests/`.

## Bestaetigte Tests

### Endschalter

**Stand:** ESP32-WROOM, Testsketch `EndschalterTest`. Alle vier Schalter
funktionieren.

| Schalter | GPIO | Ergebnis |
| --- | --- | --- |
| AZ_MIN | 4 | GEDRUECKT |
| AZ_MAX | 5 | GEDRUECKT |
| EL_MIN | 15 | GEDRUECKT |
| EL_MAX | 12 | GEDRUECKT |

Logik: `INPUT_PULLUP`, offen = `HIGH`, gegen GND = `LOW`.

### RTC (DS3231)

**Stand:** ESP32-WROOM, Testsketch `RtcTest` (RTClib). I2C SDA=21/SCL=22,
Adresse `0x68`. DS3231 erkannt, Datum/Uhrzeit laufen sekundenweise weiter,
Temperatur ca. 23,8 C.

### Joystick

**Stand:** ESP32-WROOM, Testsketch `JoystickTest`.

| Funktion | GPIO | Ergebnis |
| --- | --- | --- |
| X | 34 | 0..1023 |
| Y | 35 | 0..1023 |
| Taster | 13 | GEDRUECKT |

Ruhelage wird beim Start automatisch kalibriert; UP/DOWN/LEFT/RIGHT/ENTER
loesen korrekt aus.

### LCD

**Stand:** ESP32-WROOM, Testsketch `LcdTest`. 16x2-LCD, `LiquidCrystal I2C`,
Adresse `0x27`, Anzeige `SolarTracker` / `LCD Test OK`. Der LCD-Hardwaretest
ueber die PC-Steuerung wurde am 17.09.2026 vom Bediener bestaetigt.

## Auto Kalibrierung am Modell (20.09.2026)

Mit Firmware 0.4.3 vollstaendig am Modell durchgelaufen: LCD-Test,
RTC-Zeitfortschritt, AZ und EL je MIN/MAX mit 114 Schritten Entlastung und
Speicherung, beide Grenztests und Rueckkehr zur sicheren MIN. Ergebnis
`auto_ok=true`, Spannen AZ=2202 / EL=1258.

Dabei aufgetretene und behobene Fehler:

- Richtungs-Endschalter prellten: Einzelimpulse loesten Suche/Grenztest vorzeitig
  aus. Behoben durch 30-ms-Entprellung in Firmware 0.4.2.
- Bei 3 ms Schritttakt verlor der belastete 28BYJ-48 Schritte. Behoben durch
  5 ms Takt in Firmware 0.4.3.

## Testreihenfolge

1. LCD
2. Joystick
3. Endschalter
4. RTC
5. Motoren
6. Auto Kalibrierung (Gesamttest)

## Akzeptanzregel

Ein neues Softwaremodul wird erst begonnen, wenn der zugehoerige Hardwaretest
erfolgreich war.
