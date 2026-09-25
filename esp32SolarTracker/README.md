# esp32SolarTracker

Dokumentationsstand: **0.42 vom 24.09.2026**. PC-Bedienfeld: **0.7.5**, Firmware: **0.7.0**, Standalone: **0.8**.

## Live-LCD-Anzeige (0.6.0)

Das LCD zeigt im Normalbetrieb und im autonomen Betrieb laufend Zeit und
Status/Aktion sowie Azimut und Panelneigung. Waehrend der Auto Kalibrierung
bleibt der Schritt-Text sichtbar. Details: `PCSteuerung/README.md`.

## Alles vom PC aus steuern (PC 0.6.2)

Das PC-Bedienfeld steuert jetzt alles: Direktbefehlsfeld fuer beliebige
Protokollbefehle, Konfiguration senden/anzeigen, Einzelachsen-Kalibrierung
(`CAL AZ/EL`) und eine zentrale Nachfuehrung (PC-Betrieb/Simulation oder
Firmware-Autonomie) mit Anzeige des Sonnenziels. Die Standalone-Firmware 0.8
laesst ihr LCD-/Joystick-Menue zusaetzlich per serieller Fernbedienung
(`u/d/l/r/e/b`) bedienen.

## Autonomer Betrieb (0.5.0)

Firmware 0.5.0 fuehrt die Sonne ohne PC nach. Konfiguration (Standort,
Ausrichtung) und Autonomie-Flag liegen im ESP32-NVS; das PC-Bedienfeld
uebertraegt sie ueber `CONF` und schaltet `AUTOON`/`AUTOOFF`. Unter dem
Horizont parkt der Tracker an sicherer AZ-MIN/EL-MIN (Panel senkrecht,
windgeschuetzt). Details in `PCSteuerung/README.md`.

## Auto Kalibrierung am Modell bestaetigt (0.4.3)

Am 20.09.2026 wurde Firmware 0.4.3 auf den ESP32 geladen und die Auto
Kalibrierung erstmals vollstaendig am Modell durchgefuehrt: LCD-, RTC-Test,
beide Achsen MIN/MAX mit Entlastung, Speicherung, beide Grenztests und Rueckkehr
zu sicherer MIN. Ergebnis `auto_ok=true`, Spannen AZ=2202 / EL=1258. Zwei reale
Fehler wurden dabei behoben: Entprellung der Richtungs-Endschalter (0.4.2) und
Schrittverluste bei 3 ms Takt (0.4.3, jetzt 5 ms). Details in
`PCSteuerung/README.md` und `CHANGELOG.md`.


## Auto Kalibrierung und dauerhafte Positionen

Neu in PC 0.6.1 / Firmware 0.4.1: Unter Einstellungen prueft Auto Kalibrierung
LCD, RTC, alle vier Endschalter und die sicheren Start-/Stoppositionen.
Zum Abschluss steht das Panel an sicherer AZ-MIN/EL-MIN. Bei Erfolg werden
Betrieb und Simulation gruen. Ein normaler STOP erhaelt Position und Tests.
Details, Grenzen des LCD-Tests und Uploadstatus stehen in den verlinkten Anleitungen.

## Neue Bedienung am PC

Version 0.5.5: Start an sicherer MIN (AZ=90 Grad/Osten), nur Sonnenstunden,
automatische Rueckkehr beider Achsen nach Sonnenuntergang. EL-MIN steht senkrecht
(Panelneigung 90 Grad). LCD-Hardwaretest ab Firmware 0.3.2. Siehe PC-Anleitung.

[Bedienfeld starten](pc/Start.cmd), [Anleitung](pc/README.md),
[ESP32-Firmware und Deploymentstatus](PCSteuerung/README.md).
Datum und Startzeit kommen vom PC. Die RTC erhaelt echte UTC; Standort und
Simulationsgeschwindigkeit werden vom Bediener eingestellt. Simulation startet
Grafik und Panel erst nach Schalterpruefung, Kalibrierung/Referenz und Grenztests.
Neue PySide6-Oberflaeche aus Design 1, getrennte Statusdiagnose und 46
Python-/GUI-Tests erfolgreich. Die neue Oberflaeche ist noch ohne reale Motorfahrt geprueft. Version 0.3.1 korrigiert Kontaktprellen
beim Entlasten und ergaenzt genaue Fehlerdiagnosen. Endschaltertest startet automatisch AZ und EL,
faehrt beide Endlagen an, entlastet jeweils um 10 Grad und speichert die Kalibrierung.
Protokoll 3 bleibt erhalten. Am Modell trat in 0.3.0 ein Gegenkontaktfehler auf.
Korrektur 0.3.1 erfolgreich hochgeladen und Status geprueft: vier Kontakte offen,
RTC gueltig, Motoren in Ruhe. Mechanischer Ablauf noch zu pruefen.

Die folgende Beschreibung betrifft die bisherige Hauptsoftware. Fuer die neue
PC-Firmware gilt Azimut IN1..IN4 = **16, 17, 18, 19** gemaess aktuellem Motortest.

Zweiachsiger Solartracker auf Basis eines **ESP32-WROOM-32**. Die Projektlogik stammt aus `software/SolarTracker_aktuell`, wurde aber **vollstaendig auf die ESP32-Pinbelegung migriert**. Dieser Ordner enthaelt nur ESP32-kompatible Dateien und die dazugehoerigen Hardware-Tests.

## Hardware

- ESP32-WROOM-32
- 2x 28BYJ-48 Schrittmotor (Azimut und Elevation)
- 2x ULN2003 Treiberplatine
- 16x2-I2C-LCD (Adresse `0x27`)
- DS3231 RTC-Modul (I2C, Adresse `0x68`)
- Analoger Joystick (X, Y, Taster)
- 4 Endschalter als Sicherheitsgrenzen

## Pinbelegung (ESP32)

| GPIO | Signal | Funktion |
| --- | --- | --- |
| 19, 18, 17, 16 | Azimut IN1..IN4 | Azimut-ULN2003 |
| 25, 26, 27, 14 | Elevation IN1..IN4 | Elevations-ULN2003 |
| 4 | Azimut-Minimum | Endschalter |
| 5 | Azimut-Maximum | Endschalter |
| 15 | Elevation-Minimum | Endschalter |
| 12 | Elevation-Maximum | Endschalter |
| 34 | Joystick X | analog, links/rechts |
| 35 | Joystick Y | analog, hoch/runter |
| 13 | Joystick-Taster | `INPUT_PULLUP` |
| 21 | SDA | I2C (LCD + RTC) |
| 22 | SCL | I2C (LCD + RTC) |

Alle Endschalter verwenden `INPUT_PULLUP`. Offen = `HIGH`, gegen GND geschlossen = `LOW`.

### Wichtig beim Flashen

GPIO 12 und GPIO 15 (EL-Endschalter Pins) und GPIO 12 sind Strapping-Pins. Beim Upload koennen angeschlossene Leitungen daran den Flash stoeren. Bei Upload-Problemen alle Module bis auf USB abklemmen.

## Aufbau

```text
esp32SolarTracker/
|- README.md
|- CHANGELOG.md                  (Aenderungen am ESP32-Dokumentationsstand)
|- SolarTracker/                 (vollstaendiges ESP32-Hauptprojekt)
|  |- SolarTracker.ino
|  |- Config.h
|  |- Joystick.h/.cpp
|  |- Motor.h/.cpp
|  |- LCD_Menu.h/.cpp
|  |- Menu.h/.cpp
|  |- SettingsStorage.h/.cpp
|  |- SoftwareClock.h/.cpp
|  `- NOAA.h/.cpp
`- tests/                         (eigenstaendige Hardware-Tests)
   |- LcdJoystickMenu/            (vollstaendige Menue-Navigation mit Joystick)
   |- AchsenTest/                 (gespeicherte Grenzen und 10 Grad Abstand)
   |- AzimutTest/                 (Motor-Einzeltest mit 10 Grad Entlastung)
   |- EndschalterTest/
   |- RtcTest/
   `- LcdTest/
      |- LcdTest.ino
      `- README.md               (Code-Erklaerung und Testanleitung)
```

## Migration und Build

Das Projekt laeuft auf dem ESP32. Wichtige ESP32-seitige Anpassungen:

- `analogReadResolution(10)` in `setup()`, damit die Joystick-Schwellen (`350`/`700`) wie beim Uno gelten.
- `EEPROM.begin(EEPROM_SIZE)` in `SettingsStorage::begin()` (auf ESP32 zwingend).
- Alle Pins in `Config.h` auf die GPIO-Nummern oben.

Kompilieren und hochladen (im Sketch-Ordner `SolarTracker/`):

```powershell
arduino-cli compile --fqbn esp32:esp32:esp32 .
arduino-cli upload -p COM3 --fqbn esp32:esp32:esp32 .
```

Benötigte Bibliotheken: `Wire`, `LiquidCrystal I2C` (fuer das LCD), `RTClib` (fuer RTC), `EEPROM`, `hd44780`.

Falls der Upload "Wrong boot mode" meldet: ESP32 in den Download-Modus bringen (BOOT halten, EN/RESET tippen, BOOT loslassen).

## Hardware-Tests

Die Testsketches liegen unter `tests/`. Jeder ist eigenstaendig und nicht Teil des Hauptprogramms.

### LcdJoystickMenu

Am 14.09.2026 erfolgreich auf COM3 hochgeladen und per Flash-Pruefsumme verifiziert. Sichtbare Anzeige und Joystick-Navigation am Geraet sind noch zu bestaetigen.

Separater Menue-Test nach der vorgegebenen Struktur: Normalbetrieb, Simulation, Testbetrieb und Einstellungen mit allen Unterpunkten. Oben/unten waehlt aus, rechts/kurzer Druck oeffnet, links/langer Druck geht zurueck. Lange Namen werden gescrollt. Funktionsseiten sind als Vorschau gekennzeichnet und starten keine Motoraktionen.

Dieser Test nutzt die aktuell im ESP32-Code eingetragenen Joystick-Pins **X=35, Y=32, SW=12**, sowie LCD SDA=21/SCL=22. Diese Belegung weicht von der aelteren Tabelle oben ab. GPIO 12 ist im Hauptprogramm zugleich Elevation-MAX; vor gemeinsamer Verwendung muessen Taster und Endschalter getrennte Pins erhalten.

[Menuebaum, Anschluesse, Bedienung und Build](tests/LcdJoystickMenu/README.md).

### AchsenTest: aktueller Motortest

**Diagnose-Erweiterung 0.2:** Nach der ersten Prueffahrt wurde keine Motorbewegung und kein Aufleuchten der Treiber-LEDs beobachtet. `u`/`v` dauert jetzt etwa sechs Sekunden, damit die LED-Abfolge geprueft werden kann. Die folgende Upload-Bestaetigung bezieht sich auf Version 0.1.

**Status vom 11.09.2026:** Erfolgreich auf COM3 hochgeladen und Flash-Pruefsumme verifiziert. Serielle Statusabfrage: `Achsen-Test 0.1 | Selbsttest: OK | Speicher: OK`. Beide Achsen sind noch nicht kalibriert, alle vier Schalter melden offen und die Motoren bleiben aus. Es wurde kein Fahrbefehl gesendet.

Dieser Test kalibriert Azimut und Elevation einzeln und speichert alle vier mechanischen Grenzen dauerhaft. Normale Fahrten enden jeweils 10 Grad vor den Endschaltern. Nach einem Neustart bleiben die Grenzen erhalten; die aktuelle Position wird an einer markierten sicheren MIN-Position von Hand eingestellt und mit `b` bestaetigt.

Bedienung bei 115200 Baud: `a`/`e` waehlt die Achse, `u`/`v` prueft vor der Referenzierung die Richtung, `c` kalibriert die gewaehlte Achse, `m`/`p` faehrt zwischen den sicheren Grenzen, `s` stoppt und `?` zeigt den Status. Nach dem Einschalten startet kein Motor automatisch. Die Kalibrierung und Winkelgenauigkeit am realen Aufbau sind noch zu pruefen.

[Anschluesse, Kalibrierung, Speicherformat, Neustart und Befehle](tests/AchsenTest/README.md).

### EndschalterTest

- Zweck: prueft die 4 Endschalter und zeigt sie im Serial-Monitor (115200) als `GEDRUECKT` / `offen`.
- Pins: Azimut 4/5, Elevation 15/12, alle `INPUT_PULLUP`.
- **Status: getestet** – alle 4 Schalter funktionieren.

### AzimutTest

- Separater Test fuer den Azimutmotor an GPIO 19/18/17/16 und die beiden Endschalter an GPIO 4/5.
- Start per Serial-Monitor (115200 Baud): `m` Richtung MIN, `p` Richtung MAX; `l`/`r` fuer kurze 5-Grad-Fahrten und `s` fuer Stopp.
- Endschalter stoppen die Fahrt. Nach 100 ms Pause folgen rund 10 Grad (114 Halbschritte) in Gegenrichtung, danach bleibt der Motor aus.
- Keine automatische Fahrt nach dem Einschalten. Gegenschalter und manueller Stopp brechen auch die Entlastung ab; ein klemmender Schalter fuehrt nach der begrenzten Rueckfahrt zum Fehler.
- **Status: erfolgreich kompiliert; Hardwaretest noch ausstehend.**
- [Vollstaendige Testanleitung, Anschluesse und Code-Erklaerung](tests/AzimutTest/README.md).

### RtcTest

- Zweck: erkennt die DS3231, liest Datum/Uhrzeit und Temperatur aus.
- Pins: I2C 21/22, Adresse `0x68`.
- Bibliothek: `RTClib`.
- **Status: getestet** – z.B. `Datum: 03.09.2026  Uhrzeit: 13:29  Temperatur: 23.8 C`.

### LcdTest

- Zweck: beschreibt das 16x2-LCD mit zwei Zeilen (`SolarTracker` / `LCD Test OK`).
- Pins: I2C 21/22, Adresse `0x27`.
- Bibliothek: `LiquidCrystal I2C`.
- Testversion: **0.2**, mit vollstaendiger Initialisierung und eingeschalteter Hintergrundbeleuchtung.
- I2C-Adresssuche beim Start; alle drei Sekunden Erreichbarkeitsmeldung fuer `0x27` im Serial-Monitor bei 115200 Baud. Eine Antwort bestaetigt noch keine sichtbare Textausgabe.
- **Status am 09.09.2026: LCD funktioniert laut Rueckmeldung des Benutzers.** Die genaue Ursache der zuvor fehlenden Zeichen wurde nicht festgehalten.
- Der gespeicherte Sketch ist Version 0.2 und wurde erfolgreich kompiliert. Sein letzter durch den Assistenten ausgefuehrter Upload scheiterte mit `Wrong boot mode (0x13)`. Welche Testversion beim bestaetigten Erfolg auf dem Board lief, ist nicht eindeutig dokumentiert.
- Bei erreichbarem LCD ohne sichtbare Zeichen den Kontrastregler auf der LCD-Rueckseite langsam einstellen.
- **Ausfuehrliche Beschreibung:** [LCD-Test: Anschluesse, Code, Upload und Diagnose](tests/LcdTest/README.md).

Der Test startet den I2C-Bus mit 100 kHz auf GPIO 21/22, sucht einmal nach angeschlossenen I2C-Geraeten und prueft anschliessend gezielt `0x27`. Bei erreichbarem Adapter initialisiert er das LCD mit `lcd.init()`, schaltet Beleuchtung und Anzeige ein und schreibt:

```text
SolarTracker
LCD Test OK
```

In `loop()` wird die Erreichbarkeit nach jeweils drei Sekunden erneut geprueft. Der Text wird nicht laufend geloescht und neu geschrieben. Nach einem erkannten Verbindungsverlust wird die Initialisierung beim naechsten erfolgreichen Kontakt wiederholt. Der Scan erkennt weitere Adressen, stellt die LCD-Adresse aber nicht automatisch um. Der Test bewegt keine Motoren und veraendert keine gespeicherten Einstellungen.

## Bekannte Grenzen

- Ohne echte Zeit nach einem Stromausfall wird die Software-Uhr nicht automatisch nachgeholt; die RTC kann diese Funktion uebernehmen, sobald sie ins Hauptprogramm integriert ist.
- Die Endschalter melden nur mechanische Grenzen, keine absoluten Winkel.
- Die LCD-Funktion wurde vom Benutzer bestaetigt; die Zuordnung dieses Ergebnisses zur gespeicherten Diagnoseversion 0.2 ist noch offen.

## Datei-Uebersicht (ESP32-Hauptprojekt)

Eine Modul = eine Aufgabe. `SolarTracker.ino` ruft nur Module auf: `Motor`, `Menu`/`LCD_Menu`, `Joystick`, `SoftwareClock`, `SettingsStorage` (EEPROM), `NOAA`.
