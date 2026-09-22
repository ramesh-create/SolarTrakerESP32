# LCD-Menue mit Joystick

Testversion **0.1**, 14.09.2026. Eigenstaendiger ESP32-Menue-Test fuer ein 16x2-I2C-LCD. Die komplette vorgegebene Menuestruktur ist mit dem Joystick erreichbar.

**Build und Upload erfolgreich:** 307620 Byte Programmspeicher, 23740 Byte globale Variablen. Die Compilezeit-Pruefungen fuer Navigation und Tasterlogik sind bestanden. Am 14.09.2026 auf COM3 mit 115200 Baud hochgeladen, Flash-Pruefsumme verifiziert und ESP32 neu gestartet. LCD-Anzeige und Joystick-Bedienung am Geraet sind noch vom Benutzer zu bestaetigen. Dokumentationsstand: 0.9.

## Bedienung und Anzeige

| Joystick | Funktion |
| --- | --- |
| Oben / unten | Vorheriger / naechster Eintrag; am Ende geht es zum Anfang |
| Oben / unten halten | Nach 450 ms automatisch weiterblaettern, alle 180 ms |
| Rechts | Untermenue oder ausgewaehlte Vorschauseite oeffnen |
| Kurz druecken und loslassen | Auswahl oeffnen |
| Links | Eine Ebene zurueck |
| Mindestens 900 ms gedrueckt halten | Eine Ebene zurueck, ohne vorher die Auswahl zu oeffnen |

Beim Start den Stick loslassen: Die Mittelstellung beider Analogachsen wird aus 32 Messungen bestimmt. Eine Totzone von 180 ADC-Schritten und 40 ms Entprellung verhindern unbeabsichtigte Eingaben. Die Aufloesung betraegt 10 Bit. Eine unplausible Mittelstellung wird im Serial-Monitor gemeldet; dann Verdrahtung pruefen, den Stick zentrieren und neu starten.

Die erste Zeile zeigt den Menuebereich und die Position, die zweite den ausgewaehlten Eintrag:

```text
Hauptmenue 1/4
>Normalbetrieb
```

Lange Eintragsnamen werden automatisch gescrollt. Beim Zurueckgehen bleibt die Auswahl im jeweiligen Menue erhalten. Das LCD wird nur bei geaendertem Text beschrieben, ohne staendiges Loeschen.

**Die Funktionsseiten sind Menue-Vorschauen.** Beim Auswaehlen von beispielsweise `Betrieb starten`, `Azimut-Motor` oder `Alles testen` werden keine Motorfahrten oder Hardwaretests gestartet. Das Display zeigt den gewaehlten Namen und abwechselnd `Menue-Vorschau` / `Links: zurueck`. Auch Einstellungen werden hier noch nicht bearbeitet oder gespeichert. Dieser Sketch dient dem Test von LCD, Joystick und Navigation vor der Anbindung der Funktionen.

## Vollstaendige Menuestruktur

```text
Hauptmenue
|- Normalbetrieb
|  |- Betrieb starten
|  `- Status anzeigen
|- Simulation
|  |- Simulation Start
|  `- Geschwindigkeit
|- Testbetrieb
|  |- Endschalter
|  |- RTC (DS3231)
|  |- LCD
|  |- Azimut-Motor
|  |- Elevation-Motor
|  |- Joystick
|  `- Alles testen
`- Einstellungen
   |- Az/El manuell
   |- Datum
   |- Uhrzeit
   |- Breite
   |- Laenge
   |- Startpos fahren
   |- Startpos speichern
   |- Startpos lesen
   |- Endpos fahren
   |- Endpos speichern
   |- Endpos lesen
   |- Schalter-Test
   `- Kalibrierung starten
```

## Anschluesse

Die Joystick-Belegung wurde aus dem aktuellen ESP32-Hauptcode vom 14.09.2026 uebernommen; aeltere Dokumente nennen andere Pins.

| Anschluss | ESP32 |
| --- | --- |
| LCD SDA | GPIO 21 |
| LCD SCL | GPIO 22 |
| Joystick X | GPIO 35 |
| Joystick Y | GPIO 32 |
| Joystick SW | GPIO 12, gedrueckt gegen GND |
| Joystick Versorgung | 3,3 V und GND |

LCD-Adresse `0x27`. LCD und ESP32 benoetigen gemeinsame Masse und passende I2C-Pegel. Die Versorgung des konkreten LCD-Moduls beachten; SDA/SCL duerfen den ESP32 nicht mit 5-V-Pegeln speisen.

Die Orientierung entspricht dem derzeitigen `Joystick.cpp`: X hoch = oben, X niedrig = unten, Y hoch = rechts, Y niedrig = links. Bei abweichender mechanischer Montage laesst sich diese Zuordnung in `MenueTest::richtung()` anpassen.

**GPIO 12 ist im Hauptprogramm derzeit doppelt belegt: Joystick-Taster und Elevation-MAX-Endschalter.** Fuer den Menue-Test darf an diesem Eingang nur der Joystick-Taster angeschlossen sein, sonst kann auch der Endschalter eine Tasteraktion ausloesen. Vor der Zusammenfuehrung mit der Motorsteuerung sind getrennte Pins festzulegen. Der Hauptcode wird durch diesen Test nicht veraendert. Die Motor-Ausgaenge werden im Test auf LOW gehalten.

## Installation und Build

Board: **ESP32 Dev Module** (`esp32:esp32:esp32`). Benoetigt werden die vorhandene Bibliothek **hd44780** von Bill Perry und `Wire` aus dem ESP32-Boardpaket.

Vom Projekt-Wurzelordner aus:

```powershell
Set-Location .\esp32SolarTracker\tests\LcdJoystickMenu
arduino-cli compile --fqbn esp32:esp32:esp32 .
arduino-cli upload -p COM3 --fqbn esp32:esp32:esp32:UploadSpeed=115200 .
```

COM3 gegebenenfalls mit `arduino-cli board list` pruefen. Ein Upload ersetzt das laufende Programm auf dem ESP32 durch den Menue-Test. Bei `Wrong boot mode` BOOT halten, EN/RESET kurz betaetigen und den Upload starten; BOOT nach hergestellter Verbindung loslassen. Fuer Diagnoseausgaben den Serial-Monitor auf 115200 Baud stellen.

## Aufbau und Pruefung

- `LcdJoystickMenu.ino`: ruft nur `begin()` und `update()` des Moduls auf.
- `MenueTest.h/.cpp`: LCD-Ausgabe, Scrollen, Joystick-Einlesen und Mittelstellung.
- `MenueModell.h`: Menuestruktur und Navigation. Ein `static_assert` prueft beim Kompilieren alle Untermenues, Eintraege, Rueckspruenge und das Umlaufen der Auswahl.
- `TasterLogik.h`: entprellter kurzer/langer Tastendruck. Ein weiterer `static_assert` prueft Klick, langen Druck ohne zusaetzlichen Klick und Kontaktprellen.

Am Geraet pruefen: alle vier Hauptpunkte erreichen, alle Untermenues durchblaettern, lange Namen lesen, Eintraege oeffnen, mit Links und langem Druck zurueckgehen. Ein langer Tastendruck darf nicht erst den ausgewaehlten Eintrag oeffnen. Der Hardwaretest und die sichtbare Joystick-Navigation sind noch zu bestaetigen.
