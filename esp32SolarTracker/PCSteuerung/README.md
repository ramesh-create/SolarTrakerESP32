# ESP32-PCSteuerung 0.7.0

Stand: 24.09.2026. Eigenstaendige Firmware fuer das [Python-Bedienfeld](../pc/README.md).
Kein automatischer Motorstart; die Hauptsoftware bleibt separat erhalten.

## Stand 0.7.0 (24.09.2026)

Neuer Befehl `TZ <minuten>`: fester Zeitzonen-Versatz (z. B. 345 fuer Nepal,
UTC+5:45) im NVS. `sonnenstand` und `kalenderZeit` nutzen diesen Versatz statt
der festen EU-Sommerzeit; ohne `TZ` gilt weiterhin die EU-Regel (MEZ/MESZ).
Status ergaenzt `tz_supported`/`tz_minuten`. Das PC-Bedienfeld sendet `TZ`
zusammen mit `CONF`. Protokoll 3, margin=114 unveraendert.

## Stand 0.6.2 (22.09.2026)

Neuer Befehl `ORT <hex>` (16 ASCII-Zeichen): speichert den Ortsnamen (Stadt,
Land) mit Pruefsumme-frei im NVS und zeigt ihn auf dem LCD als **dritte
Wechselzeile** (Winkel / Status / Ort). Status ergaenzt `ort_supported`. Der PC
sendet `ORT` zusammen mit `CONF`. Protokoll 3, margin=114, Fahrlogik unveraendert.

## Stand 0.6.1 (22.09.2026)

Live-LCD zeigt jetzt **Datum und lokale Zeit**: Zeile 1 `TT.MM.JJ HH:MM`
(lokal, MEZ/MESZ). Zeile 2 wechselt alle 3 s zwischen Winkeln
(`Az### Ng##`) und Status (`Autonom`/`PC-Bereit`/`Bereit`); waehrend einer Fahrt
steht dort die Aktion. Kalenderberechnung ueber `kalenderZeit` in `Sonne`.
Protokoll 3, margin=114, Fahrlogik und Speicher unveraendert.

## Stand 0.6.0 (21.09.2026)

Live-LCD-Anzeige im Normalbetrieb und autonomen Betrieb, sobald das LCD
erreichbar ist (alle 1 s):

- Zeile 1: `HH:MM:SS` (lokal, MEZ/MESZ) und Status/Aktion – `Bereit`, `PC`,
  `Autonom` bzw. `Fahrt`, `SuMIN`, `FMIN`, `SuMAX`, `FMAX`, `Tipp`, `Entl`,
  `TMin`, `TMax`, `TZur`.
- Zeile 2: `Az### Ng##` (Azimut und Panelneigung aus der gezaehlten Position),
  sonst `Az --  Ng --`, wenn die Referenz fehlt.
- Waehrend der Auto Kalibrierung bleibt der Schritt-Text (`autoAnzeige`)
  sichtbar. Nach einem manuellen `LCD ...`-Befehl bleibt der eigene Text 30 s
  stehen.

Protokoll 3, margin=114, Fahrlogik und Speicherformat unveraendert.

## Stand 0.5.1 (21.09.2026)

Status meldet zusaetzlich die gespeicherte Konfiguration (`lat`, `lon`,
`az_null`, `el_neigung`, wenn `conf_ok`) und das berechnete Sonnenziel in
Schritten (`sun_az`, `sun_el`, sonst -1). Damit kann das PC-Bedienfeld die
Konfiguration anzeigen und den autonomen Betrieb einheitlich darstellen.
Keine Aenderung an Fahrlogik, Speicherformat oder Protokoll (3, margin=114).

## Stand 0.5.0 (20.09.2026)

Autonomer Betrieb: Der ESP32 fuehrt die Sonne ohne PC nach.

- Neues Modul `Sonne.h/.cpp` (NOAA-Naeherung und Zielabbildung, aus `pc/sonne.py`
  und `pc/tageslauf.py` portiert). Gegen die PC-Referenz geprueft: 0 Abweichungen.
- Konfiguration (Breite, Laenge, `az_null`, `el_neigung`) und Autonomie-Flag im
  NVS. Befehle: `CONF <lat> <lon> <aznull> <elneigung>`, `AUTOON`, `AUTOOFF`.
- Status ergaenzt `auto_mode` und `conf_ok`; Version jetzt 0.5.0. Protokoll 3,
  `margin`=114 unveraendert.
- Start nur bei bestandenem Gesamttest (`auto_ok`), Referenz, Grenztests,
  gueltiger RTC und vorhandener Konfiguration. Ziel einmal pro Minute; beide
  Achsen nacheinander. Unter dem Horizont Park an sicherer AZ-MIN/EL-MIN
  (Panel senkrecht, windgeschuetzt). Zeitzone automatisch MEZ/MESZ (EU-Regel).
- STOP deaktiviert den autonomen Betrieb wieder. PC-Bedienfeld 0.6.1 sendet
  `CONF` und schaltet `AUTOON`/`AUTOOFF` ueber Einstellungen.

## Stand 0.4.3 (20.09.2026)

Am Modell durchgefuehrt: Firmware 0.4.1 hochgeladen und Auto Kalibrierung
(AUTOCAL) gestartet. Dabei traten zwei reale Fehler auf, die in 0.4.2 und 0.4.3
behoben wurden. Danach lief der vollstaendige Gesamttest erstmals erfolgreich
durch: `auto_ok=true`, beide Achsen an sicherer MIN (114 Schritte), Spannen
AZ=2202 / EL=1258, Referenz und Grenztests gesetzt.

- 0.4.2: Richtungs-Endschalter (MIN/MAX) werden jetzt erst nach 30 ms stabilem
  Low ausgewertet (`Entprellung.h`, Compilezeit-Test). Zuvor loeste ein einzelner
  Prell-/Stoerimpuls eine MIN-Suche bzw. einen Grenztest vorzeitig aus; die
  gemessene AZ-Spanne streute dadurch stark.
- 0.4.3: Schritttakt von 3 ms auf 5 ms erhoeht. Bei 3 ms verlor der belastete
  28BYJ-48 Schritte, sodass die gezaehlte Position driftete und der Grenztest
  den MIN-Schalter bei 114 Schritten noch als gedrueckt meldete. Mit 5 ms sind
  Kalibrierung, Grenztests und Rueckkehr reproduzierbar.
- Protokoll bleibt 3; `margin` bleibt 114. Keine Aenderung an Speicherformat,
  Motorbelegung oder Schutzlogik.

## Historischer Stand 0.4.1 (18.09.2026)

AUTOCAL startet nach HELLO den Gesamttest, auch mit vorhandenen Kalibrierdaten:
LCD schreiben, RTC ueber 2,1 Sekunden auf Zeitfortschritt pruefen, AZ und EL
jeweils an MIN/MAX kalibrieren/entlasten/speichern, beide Grenztests und Rueckkehr
zu sicherer MIN. Nur eine Achse faehrt gleichzeitig. Displaymeldungen wechseln
an den Zustandsgrenzen. STOP, Watchdog, Kontakt-, RTC-, LCD- und Speicherfehler
brechen ab. Das LCD kann seine eigene optische Lesbarkeit nicht messen.

Status ergaenzt `auto_supported`, `auto_testing`, `auto_ok`, `auto_message`,
`device_id`, `position_storage`, `storage_ok`, je Achse `calibration_id`.
Protokoll bleibt 3. AUTO fordert auch bestandenen Gesamttest, RTC und LCD.
Kein automatischer Motorstart nach Boot/HELLO oder nach bestandenem Gesamttest.

NVS `pc-tracker-v1`: `az_state`/`el_state` enthalten pruefsummengeschuetzte
Spanne, Position, Motorphase, Referenz, Grenztest und Kalibriergeneration.
Vor Fahrtbeginn wird die Fahrt markiert, nach STOP/Fahrtabschluss der Stand
atomar gespeichert. `auto_ok` merkt den Gesamttest; neue Kalibrierung loescht ihn.
Stromverlust waehrend Fahrt verwirft die Positionsreferenz, nicht die Spanne.
HOME AZ/EL sucht nur MIN und entlastet 114 Schritte; bestandene Grenztests bleiben.
SWTEST misst nur fehlende Spannen. AUTOCAL misst dagegen ausdruecklich alles neu.
Boot migriert alte Spannen, erfindet aber keine vorher ungespeicherte Position.
Sichere Start-/Stoppositionen sind 114 und Spanne-114 Schritte, MIN ist Null.

Validierung: 102 Python-/GUI-Tests bestanden; Firmware kompiliert:
328780 Byte Programm, 24036 Byte globale Variablen. Bekannte AVR-Warnung der
LiquidCrystal-I2C-Bibliothek, ESP32-Build erfolgreich.
Deployment 0.4.1: Uploadversuch auf COM3 mit Wrong boot mode (0x13) abgebrochen.
Manueller BOOT/EN-Downloadmodus erforderlich; auf dem ESP32 bleibt 0.3.2.
Echte Auto-Kalibrierfahrt noch ungeprueft.
Vor Upload ausgelesen: 0.3.2, Achsen in Ruhe, alle Kontakte frei,
Spannen AZ=2216 / EL=1241, Position jeweils 114, Grenztests offen.

## Historische Beschreibung bis 0.3.2

Die folgenden Deploymentnotizen beschreiben den alten Stand. Aussagen ueber
verlorene Positionen oder neu erforderliche Tests gelten fuer 0.3.2; oben steht
das aktuelle Verhalten von 0.4.1.

## LCD-Erweiterung 0.3.2

`LCD <hexzeile1> <hexzeile2>` schreibt zwei Zeilen mit je 16 ASCII-Zeichen.
Jede Zeile besteht aus genau 32 Hex-Zeichen; Leerzeichen werden als 20 kodiert.
Steuerzeichen, ungueltige Hexwerte und falsche Laengen werden abgelehnt.
Beispiel: den PC-Testknopf Text ans LCD senden verwenden. Protokoll bleibt 3.
Der Befehl ist nur bei stillstehenden Motoren zulaessig, nach HELLO 3.

`LcdSteuerung.cpp` verwendet LiquidCrystal I2C 1.1.2 mit Adresse 0x27,
16 Spalten/2 Zeilen und GPIO21/22. Initialisierung erfolgt erst beim Testbefehl;
kein LCD-Start darf die Motorkontrolle blockieren. I2C wird vor und waehrend des
Schreibens geprueft. ACK bestaetigt nur die Uebertragung; Sichtpruefung bleibt noetig.
`lcd_supported:true` kennzeichnet die Funktion im Status, `lcd_present` die
Erreichbarkeit beim letzten Schreibversuch (vor dem ersten Test false).

Kalibrierung, gespeicherte Spannen, Motorpins und Freigaben bleiben unveraendert.
Ein Upload startet den ESP32 neu: Spannen bleiben erhalten, Referenz und
Grenztests muessen danach wiederhergestellt werden. Kein Motorstart beim Booten.

Build 0.3.2 am 17.09.2026 erfolgreich: 320980 Byte Programm, 23900 Byte globale
Variablen. Upload auf COM3 nach manueller BOOT/RESET-Betaetigung erfolgreich;
Flash-Pruefsumme verifiziert. Die LiquidCrystal-I2C-Bibliothek meldet wie beim
bewaehrten Einzeltest ihre AVR-Architekturwarnung; der ESP32-Build ist erfolgreich.

**Hardwarepruefung nach Upload (Dokumentation 0.22):** Firmware 0.3.2 ausgelesen,
LCD-Testbefehl ueber die echte PC-Steuerzentrale mit ACK bestaetigt, danach
`lcd_supported=true` und `lcd_present=true`. Gesendete Zeilen: `SolarTracker`
und `LCD Test OK`. Der Bediener hat am 17.09.2026 beide sichtbaren Zeilen bestaetigt
(Dokumentation 0.23); der LCD-Hardwaretest ist damit abgeschlossen.
RTC mit echter PC-Zeit synchronisiert, vorhanden und gueltig. Beide Motoren in
Ruhe, alle vier Kontakte offen. Spannen AZ=2145 und EL=1242 entsprechen exakt
dem vor Upload ausgelesenen Stand. Kein Motorfahrbefehl gesendet.
Nach dem Neustart sind Positionsreferenzen unbekannt und Grenztests offen;
die Kalibrierdaten sind weiterhin gespeichert.

## Verdrahtung

| Verbindung | ESP32-GPIO |
| --- | --- |
| Azimut ULN2003 IN1, IN2, IN3, IN4 | **16, 17, 18, 19** |
| Elevation ULN2003 IN1, IN2, IN3, IN4 | 25, 26, 27, 14 |
| Azimut MIN / MAX | 4 / 5 |
| Elevation MIN / MAX | 15 / 12 |

Belegung aus den aktuellen MotorTestAz/El-Sketchen; Azimut ist gegenueber dem
aelteren Hauptprogramm umgedreht. Schalter schliessen nach GND, aktiv LOW mit
INPUT_PULLUP. GPIO12 nicht gleichzeitig mit dem Joystick-Taster verbinden.
ULN2003/Motoren extern mit 5 V versorgen, gemeinsame Masse mit dem ESP32.

## Build / Upload

Im Ordner `PCSteuerung`:

```powershell
arduino-cli compile --fqbn esp32:esp32:esp32 .
arduino-cli upload -p COM3 --fqbn esp32:esp32:esp32:UploadSpeed=115200 .
```

Dokumentation 0.17: Version 0.3.1 mit Protokoll 3, RTClib und DS3231.
Version 0.3.1: Build erfolgreich (318968 Byte Programm, 23884 Byte globale
Variablen). Upload auf COM3 erfolgreich, Flash-Pruefsumme verifiziert.
Statuscheck: 0.3.1, beide Achsen in Ruhe und unkalibriert/nicht referenziert,
alle vier Kontakte offen, RTC vorhanden und gueltig. Keine Motorfahrt gestartet.
Am Modell wiederholte Abbrueche mit Gegenkontaktfehler gemeldet. Ein Softwarefehler
bei Kontaktprellen wurde korrigiert; physische Drehrichtung, Schalterzuordnung
und tatsaechliche Entlastung bleiben noch zu bestaetigen.

## Fehlerdiagnose 0.3.1

Ein anfangs aktiver Gegenkontakt darf beim Wegfahren prellen, bis er mindestens
25 ms durchgehend offen war. Danach ist erneutes Schliessen ein Fehler. Ein
Kontakt in Fahrtrichtung stoppt weiterhin sofort, ebenso zwei aktive Kontakte.
Nach 114 Entlastungsschritten erfolgt kein weiterer Schritt. Im Stillstand wird
bis zu 100 ms auf stabil offene Kontakte gewartet, sonst Abbruch. Ein klemmender
Gegenkontakt auf einer laengeren Suchfahrt stoppt spaetestens nach 114 Schritten.
`fault` enthaelt zusaetzlich `axis`, `phase`, `direction`, `steps`, `position`,
`min`, `max`; das PC-Protokoll zeigt diese Werte lesbar an.

Endlagen werden erst nach MIN/MAX und erfolgreicher Entlastung gespeichert.
Der Datensatz der neu kalibrierten Achse wird vor Beginn ungueltig gemacht;
ein Abbruch liefert daher keine neue gueltige Endlage. Grenztests koennen erst
nach abgeschlossener Kalibrierung/Referenz durchgefuehrt und bestaetigt werden.

## Automatischer Endschaltertest und RTC (0.3.0)

SWTEST startet ohne Handbetaetigung die komplette Kalibrierung: AZ MIN erreichen,
100 ms stoppen, 114 Schritte entlasten, AZ MAX erreichen, 100 ms stoppen,
114 Schritte entlasten und Spanne speichern. Anschliessend 500 ms Pause,
dann derselbe Ablauf fuer EL. Je Kontakt zaehlt erst die abgeschlossene Entlastung;
MAX zaehlt erst nach erfolgreichem Speichern. Am Ende switch_test=4 und Motoren aus.
Schalterkontakte werden waehrend Fahrt sofort ausgewertet; nach Entlastung
muss der Kontakt nach einer Beruhigungszeit von 25 ms offen sein.

STOP, Kommunikationsverlust, Suchwegueberschreitung, klemmender Kontakt oder
Speicherfehler brechen ab. Die zweite Achse startet nur nach erfolgreicher erster
Achse. Eine bereits erfolgreich gespeicherte Achse bleibt bei einem spaeteren
Fehler der anderen Achse erhalten. Zu Beginn jeder Achsenkalibrierung wird nur
deren vorheriger Datensatz ungueltig. Bei anfangs aktivem MIN wird direkt entlastet;
bei aktivem MAX darf in MIN-Richtung weggefahren werden, der Kontakt muss binnen
114 Schritten oeffnen. Beide Schalter einer Achse gleichzeitig verhindern den Start.

Geltende Kalibrierspannen werden nach Neustart/HELLO anerkannt: kein unnoetiges
Anfahren der Schalter. Die Positionsreferenz ist nach Neustart unbekannt und
muss an der echten markierten Stellung bestaetigt werden. Grenztests bleiben
vor Automatik erforderlich. Erneutes SWTEST misst beide Achsen bewusst neu ein.

RTC unveraendert: DS3231 an SDA21/SCL22, Adresse 0x68; TIME schreibt echte UTC,
niemals Simulationszeit. Mit Batterie laeuft die Uhr ohne PC weiter. Ohne PC
stoppt weiterhin der Watchdog die Motorsteuerung.

## Bewegungsregeln

- 4096 Halbschritte/Umdrehung, 5 ms Schritttakt (0.4.3; zuvor 3 ms), Motoren nach Fahrt aus.
- Beide Schalter gleichzeitig: sofortiger Stopp. Ein unerwarteter Gegenkontakt
  stoppt ebenfalls. Normale Fahrt wird vor jedem Schritt ueberwacht.
- Ein erreichter Endschalter bei normaler Fahrt/Tippfahrt loest eine einmalige
  Entlastung um 114 Halbschritte aus. Danach ist die Position nicht referenziert.
  STOPP oder Verbindungsverlust haben Vorrang vor dieser Entlastung.
- Kalibrierung sucht maximal eine Umdrehung zu MIN, definiert dort Null,
  entlastet 114 Schritte, sucht MAX innerhalb einer Umdrehung ab MIN und
  entlastet erneut. Klemmt ein Schalter oder ist der Weg unplausibel, Abbruch.
- Kalibrierung ersetzt nur die ausgewaehlte Achse. Vor Beginn wird deren alter
  Datensatz ungueltig. Erst nach beiden erfolgreich entlasteten Endlagen wird
  die gemessene Spanne gespeichert. MIN ist definitionsgemaess 0.
- Keine automatische Referenzfahrt beim Start. Gespeicherte Grenzen beweisen
  keine aktuelle Position; REF bestaetigt ausschliesslich die tatsaechlich
  eingenommene markierte Stellung bei 114 Schritten ab MIN.
- Normale Ziele liegen zwischen 114 und Spanne minus 114 Schritten. Ausserhalb
  liegende Ziele werden abgelehnt. Ohne Referenz sind nur Tippfahrt und CAL erlaubt.
- Es bewegt sich jeweils eine Achse. PC-Verlust nach 2000 ms ohne PING stoppt
  alle Motoren und verwirft die Referenz einer gerade bewegten Achse.

## Protokoll 3

115200 Baud, 8N1, ASCII-Befehle, Abschluss LF. Jede Zeile beginnt mit einer
positiven ganzzahligen Kennung (maximal 1000000000); Antworten sind JSON-Zeilen.
Dezimalzahlen verwenden einen Punkt. Winkel sind relativ zum mechanischen MIN.

| Beispiel | Bedeutung |
| --- | --- |
| `1 HELLO 3` | Verbindung starten, laufende Fahrt stoppen, Status liefern |
| `2 PING` | Lebenszeichen; PC sendet alle 500 ms |
| `3 STATUS` | Aktuelle Achsen und Schalter abfragen |
| `4 STOP` | Sofort beide Motoren stoppen; auch ohne HELLO erlaubt |
| `5 JOG AZ -5` | Begrenzte Tippfahrt (-5 bis +5 Grad, Betrag mindestens 0.1) |
| `6 CAL AZ` | Azimut neu kalibrieren; fuer Elevation EL |
| `7 REF EL` | Markierte sichere MIN-Stellung manuell bestaetigen |
| `8 MOVE AZ 45` | Referenzierte Achse auf 45 Grad ab mechanischem MIN fahren |

Zusaetzliche Befehle:

| Beispiel | Bedeutung |
| --- | --- |
| `9 TIME 1800000000` | Echte PC-UTC als Unixsekunden in DS3231 schreiben (2000-2099) |
| `10 SWTEST` | Beide Achsen automatisch kalibrieren und Endschalter entlasten |
| `11 LIMIT AZ` | Sichere Grenzen von Azimut abfahren |
| `12 AUTO EL 45` | Automatikziel mit zusaetzlicher Startfreigabe |
| `13 CONF 50.187 8.739 90.00 90.00` | Standort und Ausrichtung dauerhaft speichern |
| `14 AUTOON` | Autonomen Betrieb aktivieren (braucht Gesamttest, `CONF`, RTC) |
| `15 AUTOOFF` | Autonomen Betrieb deaktivieren |
| `16 ORT <hex>` | Ortsname (16 ASCII-Zeichen) dauerhaft speichern (LCD-Wechselzeile) |
| `17 TZ <minuten>` | Zeitzonen-Versatz in Minuten (-720 bis 840) dauerhaft speichern |

Nur HELLO 3 aktiviert die Steuerung. Aeltere Clients werden abgewiesen, damit
der ehemals manuelle SWTEST nicht unerwartet Motoren startet.

Status ergaenzt `switch_test` (0 bis 4), `switch_testing`, `rtc_present`,
`rtc_valid`, `rtc_epoch` (UTC) und je Achse `limits_ok`.
Weitere Zustaende: 8 Grenztest MIN, 9 Grenztest MAX, 10 Rueckkehr nach MIN.
RTC wird nur im Stillstand per I2C abgefragt; waehrend der Fahrt wird die zuletzt
verifizierte Zeit anhand millis fortgeschrieben. TIME wird bei Bewegung abgelehnt.

`ack` enthaelt `id`, `ok` und `message`. OK bestaetigt die Annahme, nicht die
physische Ausfuehrung. `status` kommt alle 500 ms und nach Abschluss, mit
`protocol`, `version` und zwei `axes` (Azimut zuerst). Achsendaten: `position`,
`span`, `margin` in Halbschritten; `calibrated`, `referenced`, `min`, `max` als
Boolean; `state`: 0 Ruhe, 1 Fahrt, 2 Suche MIN, 3 Entlaste MIN, 4 Suche MAX,
5 Entlaste MAX, 6 Tippfahrt, 7 Entlastung nach unerwartetem Kontakt.

`fault` meldet einen Abbruch. `event` meldet die laufende Endschalter-Entlastung:
Der PC pausiert die Automatik, laesst aber die Entlastung fertiglaufen.
Zu lange Befehlszeilen werden verworfen und stoppen die Motoren.
