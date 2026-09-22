# AGENTS.md

Zweiachsiger Solartracker auf **ESP32-WROOM-32** (28BYJ-48-Motoren, I2C-LCD, DS3231-RTC, Joystick, NOAA-Sonnenberechnung). Alle Texte, Kommentare und Doku sind **Deutsch** – neue Beiträge ebenfalls auf Deutsch schreiben.

## Aktive Linie (wichtig)

- **Aktiv und gepflegt: `esp32SolarTracker/`** – PC-Bedienfeld **0.6.1** (`pc/`) und Firmware **`PCSteuerung` 0.4.3** (serielles Protokoll 3).
- **Standalone-Firmware: `esp32SolarTracker/SolarTracker/`** (v0.8, LCD-/Joystick-Menue, serielle Fernbedienung) – aeltere, weniger abgesicherte Linie.
- Der alte **Arduino-Uno-Stand unter `software/`** ist **archiviert** und wird nicht mehr gepflegt.
- Vertraue dem Code und den READMEs unter `esp32SolarTracker/` sowie der Wurzel-Doku ab Dokumentation 0.28.

## Build / Upload

Kein Paketmanager, kein Lint/Test-Framework. Quelle ist `arduino-cli` (oder Arduino IDE 2.x). Im jeweiligen Sketch-Ordner:

```powershell
# PC-gesteuerte Firmware (esp32SolarTracker/PCSteuerung)
arduino-cli compile --fqbn esp32:esp32:esp32 .
arduino-cli upload  -p COM3 --fqbn esp32:esp32:esp32:UploadSpeed=115200 .

# Standalone-Firmware (esp32SolarTracker/SolarTracker)
arduino-cli compile --fqbn esp32:esp32:esp32 .
arduino-cli upload  -p COM3 --fqbn esp32:esp32:esp32 .
```

- Bei `Wrong boot mode (0x13)`: ESP32 manuell in den Download-Modus (BOOT halten, EN/RESET tippen, BOOT loslassen).
- PC-Tests im Ordner `esp32SolarTracker/pc`: `.\.venv\Scripts\python.exe -m unittest -v test_pc test_gui test_design test_tageslauf` (simulierter serieller Anschluss, keine echten Motoren).
- `esp32SolarTracker/tests/` enthaelt eigenstaendige Hardwaretests – separat kompilieren.

## Projektregeln (aus `docs/development_rules.md`)

- Jede Änderung: **Versionsnummer erhöhen + Eintrag in `CHANGELOG.md`**, Doku parallel pflegen.
- Keine halbfertigen Zwischenstände; jede neue Version muss lauffähig sein.
- Vor neuen Modulen wird die betroffene Hardware getestet.
- Protokoll 3: `margin` muss **114** bleiben (PC-Validierung in `pc/verbindung.py`).

## Hardware-/Code-Gotchas (ESP32)

- Endschalter: `INPUT_PULLUP`, gegen GND geschlossen → aktiv ist **LOW**. Azimut MIN D4, Azimut MAX D5, Elevation MIN D15, Elevation MAX D12.
- Richtungs-Endschalter werden in der Firmware **entprellt** (`Entprellung.h`, 30 ms stabil Low); Gegenkontakt 25 ms (`Gegenkontakt.h`).
- Motoren: 28BYJ-48 mit ULN2003, Azimut GPIO 16/17/18/19, Elevation 25/26/27/14, `STEPS_PER_REV = 4096`, **5-ms-Schritttakt** (3 ms verliert Schritte unter Last). Motoren nach Bewegung abschalten.
- Motoren nicht ueber den 5-V-Pin des ESP32 speisen; externe 5-V-Versorgung mit gemeinsamer Masse.
- Joystick: X=34, Y=35, SW=13. **Achtung:** GPIO 12 ist zugleich Elevation-MAX.
- LCD-I2C-Adresse `0x27`, SDA=21, SCL=22; DS3231 `0x68`.

## Architektur

Ein Modul = eine Aufgabe; Details bleiben im Modul, das Hauptprogramm ruft nur Module auf.

- `PCSteuerung`: `Steuerung` (Protokoll/Ablauf), `Pruefung`, `PositionsDaten` (NVS), `Gegenkontakt`, `Entprellung`, `LcdSteuerung`.
- `SolarTracker`: `Motor`, `Menu`, `Joystick`, `LCD_Menu`, `SoftwareClock`, `SettingsStorage` (EEPROM), `NOAA`.
- `pc/`: `bedienfeld_qt`, `design_basis`, `steuerzentrale`, `tageslauf`, `sonne`, `verbindung`, `betriebsspeicher`.
