# Bedienkonzept (ESP32)

Stand: 20.09.2026. Es gibt zwei Bedienwege:

- **PC-Bedienfeld** (`esp32SolarTracker/pc`, 0.6.1) steuert die Firmware
  `PCSteuerung` (0.4.3) ueber das serielle Protokoll 3. Das ist der aktuell
  gepflegte, abgesicherte Weg.
- **Standalone-Menue** im 16x2-LCD mit Joystick (`SolarTracker`, v0.8; auch
  per serieller Fernbedienung `u/d/l/r/e/b`).

## Joystick-Bedienung (Standalone)

| Aktion | Wirkung |
| --- | --- |
| UP / DOWN | Menuepunkt wechseln oder Wert aendern |
| RIGHT / ENTER | Menuepunkt oeffnen bzw. Auswahl bestaetigen |
| LEFT / langer Druck | zurueck / abbrechen |

## Hauptmenue (Standalone)

1. Normalbetrieb
2. Simulation
3. Testbetrieb
4. Einstellungen

### Normalbetrieb

- Betrieb starten
- Status anzeigen

### Simulation

- Simulation Start
- Geschwindigkeit (Stufen)

### Testbetrieb

1. Endschalter
2. RTC (DS3231)
3. LCD
4. Azimut-Motor
5. Elevation-Motor
6. Joystick
7. Alles testen

### Einstellungen

1. Az/El manuell
2. Datum setzen
3. Uhrzeit setzen
4. Breite setzen
5. Laenge setzen
6. Startpos fahren
7. Startpos speichern
8. Startpos lesen
9. Endpos fahren
10. Endpos speichern
11. Endpos lesen
12. Schalter-Test
13. Kalibrierung starten

## Sicherheitsregeln

- Motoren werden nach jeder Bewegung abgeschaltet.
- Kritische Aktionen (Kalibrierung, Schaltertest) laufen begrenzt und stoppen
  bei Fehlern.
- Fahrtrichtungs-Endschalter und Gegenkontakt werden entprellt.
- 114 Schritte (mind. 10 Grad) Abstand zu den Endschaltern.

## PC-Bedienfeld (aktiv)

Das PC-Fenster hat vier Bereiche: Betrieb, Simulation, Einstellungen und
Komponententest. STOP/ESC und das Protokoll stehen links unter
Komponententest; rechts zeigt das Panel LIVE POSITION (Azimut/Elevation).
Die Auto Kalibrierung startet den vollstaendigen Gesamttest. Details:
`esp32SolarTracker/pc/README.md`.
