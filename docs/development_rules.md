# Entwicklungsregeln

Bezug: aktive Linie **esp32SolarTracker** (PC-Bedienfeld 0.6.1, Firmware
`PCSteuerung` 0.4.3). Build/Test:

```powershell
arduino-cli compile --fqbn esp32:esp32:esp32 .   # im Sketch-Ordner
cd esp32SolarTracker\pc
.\.venv\Scripts\python.exe -m unittest -v test_pc test_gui test_design test_tageslauf
```

## Grundsatz

Der SolarTracker wird wie ein professionelles Softwareprojekt entwickelt. Jede Änderung muss nachvollziehbar, dokumentiert und testbar sein.

## Regeln

1. Keine Schnelllösungen.
2. Jede neue Funktion wird zuerst geplant.
3. Bestehende Funktionen werden nicht unbeabsichtigt geändert.
4. Änderungen erfolgen gezielt und dokumentiert.
5. Jede neue Version muss lauffähig sein.
6. Keine halbfertigen Zwischenstände werden eingebaut.
7. Jede Änderung erhält eine Versionsnummer.
8. Jede Änderung erhält einen Eintrag im Changelog.
9. Die Dokumentation wird parallel gepflegt.
10. Vor jedem neuen Modul wird die betroffene Hardware getestet.

## Entwicklungsreihenfolge

1. Planung
2. Dokumentation
3. Hardwaretest
4. Programmierung eines einzelnen Moduls
5. Test des Moduls
6. Changelog aktualisieren
7. Nächster Entwicklungsschritt

## Hardwaretest vor Modulen

Vor neuen Modulen werden geprüft:

- LCD
- Joystick
- Motoren
- RTC
- EEPROM
- Sensoren, sobald vorhanden

## Dokumentation je Datei

Jede spätere Softwaredatei erhält:

- Beschreibung
- Zweck
- Eingänge
- Ausgänge
- Beispiele
- Änderungsverlauf

