# LCD-Test fuer den ESP32-WROOM-32

Dokumentationsversion **0.3**, Stand **09.09.2026**. Beschriebener Sketch: [LcdTest.ino](LcdTest.ino), Testversion **0.2**.

## Zweck und bestaetigter Stand

Der eigenstaendige Test prueft die I2C-Verbindung zu einem 16x2-LCD und schreibt zwei Testzeilen. Er gehoert nicht zum Hauptprogramm und steuert weder Motoren noch Joystick oder RTC an. Die I2C-Adresssuche kann eine angeschlossene RTC dennoch erkennen.

**Der Benutzer hat am 09.09.2026 bestaetigt, dass das LCD jetzt funktioniert.** Zuvor war die Hintergrundbeleuchtung an, aber kein Text sichtbar. Welche Massnahme die Anzeige hergestellt hat, wurde nicht angegeben.

Der vorherige einfache Test wurde erfolgreich auf COM3 geladen und per Flash-Pruefsumme verifiziert. Die hier gespeicherte Diagnoseversion 0.2 wurde erfolgreich fuer `esp32:esp32:esp32` kompiliert: 295416 Byte Programmspeicher und 23516 Byte globale Variablen. Ihr letzter Upload durch den Assistenten scheiterte an `Wrong boot mode (0x13)`. Daher ist die beim bestaetigten Erfolg laufende Version nicht eindeutig belegt; es liegt auch kein ausgelesenes Diagnoseprotokoll von Version 0.2 vor.

## Anschluesse und Voraussetzungen

| LCD-Anschluss | Verbindung / Bedeutung |
| --- | --- |
| SDA | ESP32 GPIO 21 |
| SCL | ESP32 GPIO 22 |
| GND | Gemeinsame Masse mit dem ESP32 |
| VCC | Zum konkreten LCD-Modul passende Versorgung; die tatsaechlich verwendete Spannung ist nicht dokumentiert |

- LCD: 16 Spalten, 2 Zeilen, I2C-Adapter an Adresse `0x27`.
- I2C-Takt: 100 kHz; Zeitlimit fuer I2C-Transaktionen: 50 ms.
- ESP32-Signale arbeiten mit 3,3-V-Pegeln. Ein mit 5 V versorgter LCD-Adapter darf SDA/SCL nicht direkt auf 5 V ziehen; in diesem Fall ist eine geeignete Pegelanpassung erforderlich.
- Anschluesse nur bei ausgeschalteter Versorgung aendern.
- Der kleine Regler auf der LCD-Rueckseite stellt den Kontrast ein. Beleuchtung und sichtbare Zeichen sind getrennt zu beurteilen.

Verwendete Bibliotheken: `Wire` aus dem ESP32-Boardpaket und **LiquidCrystal I2C 1.1.2** von Frank de Brabander / Marco Schwartz. Die Bibliothek meldet beim Kompilieren eine AVR-Kompatibilitaetswarnung; der ESP32-Build war dennoch erfolgreich. Fuer diesen Einzeltest werden `RTClib` und `hd44780` nicht benoetigt.

## Erklaerung des Codes

### Konfiguration

`I2C_SDA`, `I2C_SCL` und `LCD_ADDR` legen Pins und Adresse fest. `LiquidCrystal_I2C lcd(LCD_ADDR, 16, 2)` beschreibt das Display. `TEST_VERSION` wird ueber die serielle Schnittstelle ausgegeben. `lcdInitialisiert` merkt sich, ob der Initialisierungsablauf seit dem letzten erkannten Verbindungsverlust ausgefuehrt wurde.

### setup(): Start und Adresssuche

1. `Serial.begin(115200)` startet die Diagnoseausgabe; danach wartet der Sketch 500 ms.
2. `Wire.begin(I2C_SDA, I2C_SCL, 100000)` startet I2C auf GPIO 21/22 mit 100 kHz.
3. `Wire.setTimeOut(50)` begrenzt die Wartezeit einzelner I2C-Transaktionen.
4. Die Schleife prueft einmal die Adressen 1 bis 126. Jede antwortende Adresse wird hexadezimal ausgegeben. Ohne Antwort erscheint `Kein I2C-Geraet gefunden: Verkabelung und Versorgung pruefen.`
5. `pruefeLcd()` prueft und initialisiert das konfigurierte LCD.

Der Scan aendert `LCD_ADDR` nicht. Wird der LCD-Adapter beispielsweise unter einer anderen Adresse erkannt, muss die Konstante gezielt angepasst und der Sketch erneut kompiliert und hochgeladen werden. Eine Antwort an einer anderen Adresse identifiziert noch nicht automatisch ein LCD.

### pruefeLcd(): Verbindung und Text

`Wire.beginTransmission(LCD_ADDR)` und `Wire.endTransmission()` pruefen, ob ein I2C-Geraet an `0x27` antwortet. Bei einem Fehler wird dessen Zahlenwert ausgegeben, `lcdInitialisiert` zurueckgesetzt und die Funktion beendet.

Bei erfolgreicher Antwort und noch nicht gesetztem Initialisierungsmerker folgen:

| Aufruf | Aufgabe |
| --- | --- |
| `lcd.init()` | Initialisiert den LCD-Controller und den internen Ausgangszustand der Bibliothek |
| `lcd.backlight()` | Schaltet die Hintergrundbeleuchtung ein |
| `lcd.display()` | Schaltet die Zeichenanzeige ein |
| `lcd.clear()` | Loescht den bisherigen Inhalt |
| `lcd.setCursor(0, 0)` | Waehlt die erste Spalte der ersten Zeile |
| `lcd.print("SolarTracker")` | Schreibt die erste Testzeile |
| `lcd.setCursor(0, 1)` | Waehlt die erste Spalte der zweiten Zeile |
| `lcd.print("LCD Test OK")` | Schreibt die zweite Testzeile |

Anschliessend wird `lcdInitialisiert` gesetzt. Die Bibliotheksaufrufe liefern hier keine ausgewertete Bestaetigung der sichtbaren Zeichen. Auch die Meldung `Text gesendet` bestaetigt deshalb nur den Programmablauf zusammen mit der vorausgehenden I2C-Antwort, keinen bestandenen Sichttest.

### loop(): Wiederholte Kontrolle

Nach jeweils `delay(3000)` wird `pruefeLcd()` erneut aufgerufen. Bei stabiler Verbindung wird nur die Erreichbarkeit kontrolliert und die Statusmeldung ausgegeben; der Text bleibt stehen. Erst nach einem erkannten I2C-Fehler wird beim naechsten erfolgreichen Kontakt erneut initialisiert und geschrieben. Das Intervall betraegt mindestens drei Sekunden zuzueglich der Bearbeitungszeit.

## Kompilieren und hochladen

In PowerShell vom Projekt-Wurzelordner aus:

```powershell
Set-Location .\esp32SolarTracker\tests\LcdTest
arduino-cli compile --fqbn esp32:esp32:esp32 .
arduino-cli upload -p COM3 --fqbn esp32:esp32:esp32:UploadSpeed=115200 .
```

Board: **ESP32 Dev Module**. COM3 war der verwendete Anschluss; bei einem geaenderten Port vorher `arduino-cli board list` ausfuehren. Der Upload ersetzt das auf dem ESP32 laufende Programm durch den LCD-Test.

Falls `Wrong boot mode` erscheint: BOOT gedrueckt halten, EN/RESET kurz betaetigen und den Upload starten. BOOT loslassen, sobald die Verbindung hergestellt ist. Bei Flash-Verbindungsfehlern die Versorgung ausschalten und andere angeschlossene Module fuer den Upload abtrennen. Danach das LCD bei ausgeschalteter Versorgung wieder verbinden und neu starten.

## Anzeige, Diagnose und Testablauf

Erwartete Anzeige:

```text
SolarTracker
LCD Test OK
```

Den Serial-Monitor mit **115200 Baud** oeffnen. Fuer die einmalige Adresssuche nach dem Oeffnen EN/RESET kurz druecken. Beispielausgabe bei erreichbarem Adapter; dies ist eine Sollausgabe, kein aufgezeichnetes Testergebnis:

```text
SolarTracker - LCD-Test Version 0.2
I2C-Suche: SDA GPIO21, SCL GPIO22
I2C-Geraet gefunden: 0x27
I2C 0x27 erreichbar; Text gesendet. Sichtpruefung am LCD erforderlich.
```

1. Verkabelung und Versorgung pruefen und den Test hochladen.
2. Im Serial-Monitor die gefundene Adresse und wiederkehrende Erreichbarkeit kontrollieren.
3. Am LCD beide Zeilen lesen; bei leerer Anzeige den Kontrast langsam einstellen.
4. Einen Neustart durchfuehren und kontrollieren, ob beide Zeilen wieder erscheinen.

| Beobachtung | Naechste Pruefung |
| --- | --- |
| Beleuchtung an, keine Zeichen | Kontrast einstellen und I2C-Diagnose lesen |
| `LCD 0x27 antwortet nicht` | SDA/SCL, gemeinsame Masse, Versorgung und erkannte Adresse pruefen |
| Kein I2C-Geraet gefunden | Busverkabelung und Versorgung pruefen |
| Adapter erreichbar, nur Kaestchen oder keine Zeichen | Kontrast, Versorgung und zum Adapter passende LCD-Ansteuerung pruefen |
| Keine serielle Ausgabe | Richtigen Port, 115200 Baud und laufenden Sketch pruefen; gegebenenfalls EN/RESET druecken |

Ein vollstaendiger Testnachweis umfasst sichtbare Testzeilen, passende Diagnoseausgabe und einen erfolgreichen Neustart. Bisher bestaetigt ist die LCD-Funktion durch den Benutzer; Diagnose und Neustart der gespeicherten Version sind noch nicht separat protokolliert.
