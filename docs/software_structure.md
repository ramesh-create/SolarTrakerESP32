# Softwarestruktur (ESP32)

Stand: 20.09.2026. Ein Modul = eine Aufgabe; das Hauptprogramm ruft nur Module
auf. Es gibt zwei Firmware-Linien und das PC-Bedienfeld.

## PC-gesteuerte Firmware `esp32SolarTracker/PCSteuerung/` (0.4.3)

| Datei | Aufgabe |
| --- | --- |
| `PCSteuerung.ino` | Einstieg: `setup`/`loop` rufen nur `Steuerung` auf |
| `Steuerung.cpp/.h` | Serielles Protokoll 3, Zustandsautomat, Fahrten, Auto-Kalibrierung |
| `Pruefung.h` | Reihenfolge des automatischen Endschaltertests (Compilezeit-Test) |
| `PositionsDaten.h` | Atomarer Achsdatensatz mit Pruefsumme (NVS, Compilezeit-Test) |
| `Gegenkontakt.h` | Entprellung des Gegenkontakts (25 ms stabil offen) |
| `Entprellung.h` | Entprellung der Richtungs-Endschalter (30 ms stabil Low) |
| `LcdSteuerung.cpp/.h` | Zwei 16-Zeichen-Zeilen als ASCII-Hex ans LCD |
| `LcdText.h` | Hex-Kodierung fuer das LCD |

Sicherheitsregeln: 114 Schritte (mind. 10 Grad) Abstand zu den Kontakten,
Motoren nach Fahrt aus, Positionsreferenz nach Stromverlust unbekannt,
Watchdog stoppt bei PC-Verlust.

## Standalone-Firmware `esp32SolarTracker/SolarTracker/` (v0.8)

| Datei | Aufgabe |
| --- | --- |
| `SolarTracker.ino` | Hauptprogramm mit LCD-/Joystick-Menue |
| `Config.h` | Pins, Konstanten, Version, Standardwerte |
| `Motor.cpp/.h` | Motoren, Grad->Schritte, Abschalten nach Bewegung |
| `LCD_Menu.cpp/.h` | LCD-Ausgabe und Statusseiten |
| `Joystick.cpp/.h` | UP/DOWN/LEFT/RIGHT/ENTER, Entprellung |
| `Menu.cpp/.h` | Menuefuehrung, Normalbetrieb, Simulation, Testbetrieb |
| `SettingsStorage.cpp/.h` | EEPROM-Speicherung der Einstellungen |
| `SoftwareClock.cpp/.h` | Software-Uhr mit `millis()` |
| `NOAA.cpp/.h` | Sonnenstandsberechnung (Azimut/Elevation) |

## PC-Bedienfeld `esp32SolarTracker/pc/` (0.6.1)

| Datei | Aufgabe |
| --- | --- |
| `bedienfeld_qt.py` | PySide6-Oberflaeche, Grafik, Bedienung |
| `design_basis.py` | Layout und Achsenanzeigen der Design-1-Vorlage |
| `steuerzentrale.py` | Freigaben, Rueckmeldungen, Bewegungsablauf |
| `tageslauf.py` | Sonnenstunden und Zielabbildung ab sicherer MIN |
| `sonne.py` | NOAA-Naeherung und Motorwinkel-Abbildung |
| `verbindung.py` | Serielles Protokoll 3 (nicht blockierend) |
| `betriebsspeicher.py` | PC-Freigaben/Simulation atomar in `betrieb.json` |
| `bedienfeld.py` | Frueherer Tk-Stand, nicht mehr gestartet |

## Hardwaretests `esp32SolarTracker/tests/`

Eigenstaendige Sketche (Endschalter, RTC, Joystick, LCD, Motoren, Menue), nicht
Teil des Hauptprogramms.

## Architekturregel

Jedes Modul hat genau eine klare Aufgabe. Details bleiben im Modul; das
Hauptprogramm ruft nur auf. Bei Aenderungen pruefen: betroffene Module, Menue,
Dokumentation, Changelog.
