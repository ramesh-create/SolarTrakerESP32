# SolarTracker

Zweiachsiger Solartracker auf Basis eines **ESP32-WROOM-32**. Dokumentationsstand
**0.40 vom 24.09.2026**. PC-Bedienfeld **0.7.3**, Firmware **0.7.0**, Standalone **0.8**.

> Der alte **Arduino-Uno-Stand** unter `software/` ist archiviert und wird nicht
> mehr gepflegt. Aktive Entwicklung liegt ausschliesslich unter
> `esp32SolarTracker/`.

## Aktueller Stand

Am 20.09.2026 wurde Firmware 0.4.3 auf den ESP32 geladen und die Auto
Kalibrierung erstmals vollstaendig **am Modell** bestaetigt: LCD- und RTC-Test,
beide Achsen MIN/MAX mit Entlastung, Speicherung, beide Grenztests und Rueckkehr
zur sicheren MIN. Ergebnis `auto_ok=true`, Spannen **AZ=2202 / EL=1258**.

Dabei wurden zwei reale Fehler gefunden und behoben:

- **0.4.2** – Richtungs-Endschalter erst nach 30 ms stabilem Low auswerten
  (neues Modul `Entprellung.h`). Einzelne Prell-/Stoerimpulse loesten sonst
  MIN-Suche bzw. Grenztest vorzeitig aus.
- **0.4.3** – Schritttakt von 3 ms auf **5 ms** erhoeht. Bei 3 ms verlor der
  belastete 28BYJ-48 Schritte; der Zaehler driftete und der Grenztest meldete den
  MIN-Schalter bei 114 Schritten noch als gedrueckt.

## Aufbau des ESP32-Projekts

```text
esp32SolarTracker/
|- README.md                (ESP32-Uebersicht, Pinbelegung, Hardwaretests)
|- CHANGELOG.md             (Aenderungen am ESP32-Stand)
|- SolarTracker/            (Standalone-Firmware mit LCD-/Joystick-Menue, v0.8)
|- PCSteuerung/             (PC-gesteuerte Firmware 0.4.3, Protokoll 3)
|- pc/                      (PySide6-PC-Bedienfeld 0.6.1)
`- tests/                   (eigenstaendige Hardwaretests)
```

Es gibt zwei Firmware-Linien:

- **`PCSteuerung` (aktiv, 0.4.3):** serielles Protokoll 3, wird vom PC-Bedienfeld
  gesteuert. Sichere Kalibrierung, Grenztests, Positionsspeicher im NVS.
- **`SolarTracker` (v0.8):** eigenstaendiges Geraet mit 16x2-LCD und Joystick
  (zusaetzlich per serieller Fernbedienung bedienbar).
  Aeltere, weniger abgesicherte Linie; dient als Menue-/NOAA-Referenz.

## Hardware

- ESP32-WROOM-32
- 2x 28BYJ-48 Schrittmotor (Azimut und Elevation) mit ULN2003
- 16x2-I2C-LCD (Adresse `0x27`)
- DS3231 RTC (I2C, Adresse `0x68`)
- Analoger Joystick (X, Y, Taster)
- 4 Endschalter als Sicherheitsgrenzen

## Pinbelegung (ESP32)

| GPIO | Signal | Funktion |
| --- | --- | --- |
| 16, 17, 18, 19 | Azimut IN1..IN4 | Azimut-ULN2003 |
| 25, 26, 27, 14 | Elevation IN1..IN4 | Elevations-ULN2003 |
| 4 / 5 | Azimut MIN / MAX | Endschalter |
| 15 / 12 | Elevation MIN / MAX | Endschalter |
| 34 / 35 | Joystick X / Y | analog |
| 13 | Joystick-Taster | `INPUT_PULLUP` |
| 21 / 22 | SDA / SCL | I2C (LCD + RTC) |

Alle Endschalter nutzen `INPUT_PULLUP`: offen = `HIGH`, gegen GND = `LOW`.
Details und Verdrahtung: `esp32SolarTracker/README.md` und `docs/pinout.md`.

## Build / Upload

```powershell
# PC-gesteuerte Firmware
arduino-cli compile --fqbn esp32:esp32:esp32 .
arduino-cli upload  -p COM3 --fqbn esp32:esp32:esp32:UploadSpeed=115200 .

# Standalone-Firmware mit Menue
arduino-cli compile --fqbn esp32:esp32:esp32 .
arduino-cli upload  -p COM3 --fqbn esp32:esp32:esp32 .
```

Bei `Wrong boot mode (0x13)`: ESP32 manuell in den Download-Modus bringen
(BOOT halten, EN/RESET tippen, BOOT loslassen).

## PC-Bedienfeld

Start ueber `esp32SolarTracker/pc/Start.cmd`. Anleitung und Bedienung:
`esp32SolarTracker/pc/README.md`. Die Oberflaeche nutzt Protokoll 3 und
kommuniziert ausschliesslich ueber die serielle Schnittstelle.

## Hardware-Tests

Eigenstaendige Sketche unter `esp32SolarTracker/tests/`. Bestaetigt sind
Endschalter, RTC (DS3231), Joystick und LCD. Uebersicht: `docs/hardware_tests.md`.

## Entwicklungsregeln

Jede Aenderung erhaelt Versionsnummer und Changelog-Eintrag; Doku wird parallel
gepflegt; jede Version ist lauffaehig. Details: `docs/development_rules.md`.
