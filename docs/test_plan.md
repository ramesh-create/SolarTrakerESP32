# Testplan (ESP32)

Stand: 20.09.2026. Gilt fuer die aktive Firmware `PCSteuerung` (0.4.3) mit dem
PC-Bedienfeld 0.6.2 und fuer die Standalone-Firmware `SolarTracker` (v0.8).

## 1. Build- und Protokolltest

- `arduino-cli compile --fqbn esp32:esp32:esp32 .` im jeweiligen Sketchordner.
- Upload auf COM3; bei `Wrong boot mode (0x13)` manuell in den Download-Modus.
- Serielle Verbindung: `HELLO 3`, danach `STATUS`. Erwartet: `protocol:3`,
  `version:0.4.3`, genau zwei Achsen, `margin:114`.

## 2. Schaltertest (Pflicht vor Automatik)

- Vier Endschalter einzeln pruefen (`switch_test` bis 4).
- Jeder Schalter: offen = `HIGH`, gedrueckt = `LOW`.

## 3. Kalibrierung und Grenztest

- Auto Kalibrierung (`AUTOCAL`) startet den Gesamttest: LCD, RTC-Zeitfortschritt,
  AZ und EL je MIN/MAX mit 114 Schritten Entlastung und Speicherung, beide
  Grenztests, Rueckkehr zur sicheren MIN.
- Erfolg: `auto_ok=true`, beide Achsen bei Position 114, `limits_ok=true`.
- Am Modell am 20.09.2026 bestaetigt (AZ=2202 / EL=1258).

## 4. Referenz und Position

- Nach Neustart ist die Positionsreferenz unbekannt.
- `HOME`/`REF` stellt die Referenz an der sicheren MIN wieder her.
- Stromausfall waehrend einer Fahrt verwirft nur die Referenz, nicht die Spanne.

## 5. Fahrbefehle

- `JOG AZ/EL` mit 0,1 bis 5 Grad; Grenzen werden eingehalten.
- `MOVE`/`AUTO` nur bei referenzierter, kalibrierter Achse und freigegebenen
  Bedingungen.
- Endschalter loesen eine einmalige 114-Schritt-Entlastung aus; danach ist die
  Position nicht mehr referenziert.

## 6. Simulation und Normalbetrieb (PC)

- Simulation faehrt zuerst beide sicheren MIN an, laeuft nur ueber die
  Sonnenstunden des aktuellen PC-Datums und kehrt danach zu MIN zurueck.
- Automatik (`AUTO`) erst nach bestandenem Gesamttest, RTC und LCD.

## 7. Regressionstests (PC)

Im Ordner `esp32SolarTracker/pc`:

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_pc test_gui test_design test_tageslauf
```

Die Tests nutzen einen simulierten seriellen Anschluss; es werden keine echten
Motoren bewegt.

## Erfolgreich bestanden, wenn

- Build und Upload fehlerfrei.
- Schaltertest 4/4.
- Auto Kalibrierung `auto_ok=true`.
- Grenzen und Entlastung eingehalten.
- PC-Testsuite gruen.
