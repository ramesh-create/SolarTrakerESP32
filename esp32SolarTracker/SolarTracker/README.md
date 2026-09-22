# SolarTracker (ESP32-Variante)

Vollstaendiger Solartracker fuer den **ESP32-WROOM-32**. Dieses Projekt ist die migrierte Fassung von `software/SolarTracker_aktuell`, angepasst auf die ESP32-Pinbelegung.

Ausfuehrlichere Dokumentation (Pinbelegung, Build, Tests) steht in `../README.md`.

Dokumentationsstand: **0.3 vom 09.09.2026**. Die LCD-Funktion wurde vom Benutzer bestaetigt. Der eigenstaendige LCD-Test mit genauer Code-Erklaerung, Verdrahtung und Upload-Anleitung steht unter [tests/LcdTest](../tests/LcdTest/README.md). Er wird separat vom Hauptprogramm kompiliert. Details zum Testnachweis und zur gespeicherten Testversion 0.2 stehen dort ebenfalls.

## Funktionen

- Normalbetrieb mit Sonnenstandsberechnung (NOAA) aus Datum, Uhrzeit und Standort.
- Simulation eines Tages in 60 oder 30 Sekunden.
- Manuelle Bewegung beider Achsen ueber den Joystick.
- LCD-Menue fuer Datum, Uhrzeit, Standort und Positionen.
- Kalibrierung zum Anfahren aller vier Endschalter.
- Sicherheitsabschaltung an jedem Endschalter mit Entlastungsfahrt.
- EEPROM-Speicherung der Einstellungen.
- **Version 0.8:** Serielle Menue-Fernbedienung (115200 Baud): `u`/`d`/`l`/`r`
  Richtung, `e` ENTER, `b` zurueck (ENTER lang). Der Joystick bleibt nutzbar.

## ESP32-Anpassungen

- Joystick analog auf GPIO 34 (`X`) und 35 (`Y`), Taster GPIO 13.
- `analogReadResolution(10)` in `setup()`, damit die Joystick-Schwellen (`350`/`700`) wie beim Uno gelten.
- `EEPROM.begin(EEPROM_SIZE)` in `SettingsStorage::begin()` (auf ESP32 zwingend).
- I2C auf GPIO 21 (SDA) und 22 (SCL).

Alle Pins stehen in `Config.h`. Details: siehe `../README.md`.

## Kompilieren und Hochladen

```powershell
arduino-cli compile --fqbn esp32:esp32:esp32 .
arduino-cli upload -p COM3 --fqbn esp32:esp32:esp32 .
```

Board: `ESP32 Dev Module` (`esp32:esp32:esp32`).
