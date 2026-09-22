# SolarTracker PC-Bedienfeld 0.6.6 - Design 1

Dokumentation 0.35, 22.09.2026. Start: `Start.cmd` doppelt anklicken.
Das alte Bedienfenster zuvor schliessen. Fuer die echte LCD-Uebertragung ist Firmware 0.3.2 / Protokoll 3 erforderlich.
Firmware 0.3.1 bleibt fuer Motoren und RTC kompatibel. Python, pyserial und PySide6 sind in `.venv` installiert.

## Simulation: Startposition, Sonnenstunden, Rueckfahrt

1. Vor dem Start muessen beide Achsen kalibriert und referenziert sein sowie
   beide Grenztests und die Beobachtung des 10-Grad-Abstands bestaetigt sein.
   Standort und Ausrichtung unter Einstellungen pruefen und bestaetigen.
2. Simulation starten faehrt zuerst AZ und EL nacheinander an ihre sichere
   MIN-Position (jeweils 114 Schritte, rund 10 Grad nach dem MIN-Endschalter).
   Die Schalter werden dabei nicht erneut angefahren.
3. Der Sonnenlauf beginnt beim Sonnenaufgang des heutigen PC-Datums, auch wenn
   der PC bereits Nachmittag oder Abend anzeigt. Datum/Zeitzone kommen vom PC;
   die Startzeit wird aus Standort und NOAA-Sonnenberechnung ermittelt.
4. Grafik und Panel folgen nur den Sonnenstunden. Die Simulationszeit wartet,
   bis beide Achsen ihr jeweiliges Ziel erreicht haben. Quittung allein gilt
   nicht als Abschluss; der ESP32 muss Stillstand und Zielposition melden.
5. Bei Sonnenuntergang friert die Simulationszeit ein. Erst AZ, dann EL fahren
   zur sicheren MIN zurueck. Erst danach meldet das Fenster den Lauf als beendet.

MIN bedeutet bei Start und Rueckkehr immer die sichere Position mit 10 Grad
Abstand zum Kontakt. STOP/Esc, Kontaktfehler oder Verbindungsverlust brechen
auch eine Rueckfahrt ab; es wird danach nicht automatisch weitergefahren.

Die Vorgaben Sonnentag in 30/60/120 s berechnen den Zeitfaktor aus der gesamten
Tageslichtdauer. Motorfahrzeiten und Start-/Rueckfahrt verlaengern die reale
Laufzeit. Alternativ den Zeitfaktor zwischen 1 und 3600 selbst einstellen.

Die Grafik und ihr CSV-Export enthalten ausschliesslich Sonnenstunden.
Blau: Sonnenazimut (0-360 Grad); Orange: Sonnenhoehe (0-90 Grad); Weiss: Zeit.
Auf- und Untergang entsprechen dem geometrischen Horizont (Sonnenhoehe 0 Grad)
der vorhandenen NOAA-Naeherung, ohne atmosphaerische Refraktion oder Gelaende.
Tage ohne vollstaendigen Auf-/Untergang im lokalen Datum werden mit Meldung
abgelehnt (z.B. Polartag/-nacht); die Grafik zeigt dann keine erfundene Kurve.

## Ausrichtung und Grenzen

Der Startwinkel gilt jetzt an der **sicheren MIN**, nicht am gedrueckten Schalter:

- Azimut: **90 Grad = Osten** an sicherer AZ-MIN. Plusfahrt erhoeht den Winkel.
- Elevation: **Panel senkrecht = 90 Grad Panelneigung** an sicherer EL-MIN,
  vom Bediener bestaetigt. Positive Motorfahrt kippt Richtung waagerecht.
  Fuer die Sonne gilt Panelneigung = 90 Grad minus Sonnenhoehe: bei 30 Grad
  Sonnenhoehe sind es 60 Grad Panelneigung. Rueckkehr zu MIN stellt senkrecht.
  Die blaue/orange Tagesgrafik zeigt weiterhin Sonnenwinkel; die rechte Anzeige
  zeigt ausdruecklich die reale Panelneigung aus der Schrittzaehlung.
- Anzeigen berechnen Weltwinkel aus dieser Ausrichtung und den gezaehlten
  Schritten. Ohne Referenz bleibt die Position unbekannt. Kein Positionssensor.

Sonnenziele ausserhalb des mechanischen Fahrbereichs werden an der jeweiligen
sicheren Grenze begrenzt. Das Fenster meldet Fahrgrenze erreicht; das Panel kann
in diesem Abschnitt die Sonne nicht exakt nachfuehren. Der Tageslauf geht weiter.

`einstellungen.json` verwendet Format 3: `az_null` ist der Kompasswinkel an
sicherer AZ-MIN, `el_neigung` die Panelneigung an sicherer EL-MIN. Altes Format 2
wird mit `el_neigung = 90 - el_null` umgerechnet; bei Format 1 wird zuvor der
Abstand zum mechanischen Kontakt beruecksichtigt. Die lokale Datei ist auf
AZ=90 und Panelneigung=90 gesetzt; vorherige Staende sind in
`einstellungen_vor_0_5*.json` gesichert. Kalibrierdaten im ESP32 bleiben erhalten.

## Normalbetrieb und RTC

Normalbetrieb verwendet die echte PC-Zeit und parkt unterhalb des Horizonts
an beiden sicheren MIN-Positionen. Am naechsten Sonnenaufgang folgt er wieder.
Eine aktive PC-Verbindung ist dafuer erforderlich; autonome Nachfuehrung ohne PC
ist mit dieser Firmware nicht implementiert.

Beim Verbinden erhaelt die DS3231 die echte PC-Zeit als UTC. Die Anzeige erfolgt
in lokaler PC-Zeit. Simulationszeit wird niemals in die RTC geschrieben.

## Auto Kalibrierung (Firmware 0.4.3)

1. Verbinden, Standort und Ausrichtung unter Einstellungen speichern/bestaetigen.
2. **Auto Kalibrierung** anklicken. Dieser ausdrueckliche Auftrag misst beide
   Achsen neu, auch wenn bereits Daten gespeichert sind.
3. LCD-Testbild und RTC-Pruefung laufen zuerst. RTC muss erreichbar sein, eine
   gueltige Zeit besitzen und waehrend der Messung weiterzaehlen.
4. AZ MIN -> 10 Grad entlasten -> AZ MAX -> 10 Grad entlasten -> speichern;
   danach derselbe Ablauf fuer Elevation. Kontakte und Speicherfehler stoppen.
5. Jede Achse faehrt sichere MIN -> sichere MAX -> sichere MIN als Grenztest.
   Mechanische MIN=0/MAX=gespeicherte Spanne; sichere Startposition=114 Schritte,
   sichere Stopposition=Spanne-114. Sie ergeben sich dauerhaft aus der Spanne.
6. Erst nach Abschluss, Speicherung und freiem Kontaktzustand werden Betrieb
   und Simulation gruen. LCD: `Alle Tests OK` / `Normalbetr.bereit`.
   Der Betrieb startet erst durch den Bediener. STOP/ESC bricht jeden Schritt ab.

LCD zeigt pro Schritt Achse und Suche/Entlastung/Grenzfahrt, bei Fehlern
`Test FEHLER` und die auf 16 Zeichen gekuerzte Ursache. PC zeigt die ganze Meldung.
Der LCD-Test prueft I2C-Erreichbarkeit und Schreiben, nicht die optische Lesbarkeit.
Schrittzaehlung ersetzt keinen Encoder: sichtbare Ausgabe und mechanischen
10-Grad-Abstand am Modell kontrollieren. Berechnung setzt 4096 Schritte/Umdrehung voraus.

## Weltkarte (PC 0.6.4)

Der Panel-Standort wird als **Punkt** auf einer **Weltkarte** gezeigt. Kleine
Karte rechts unten im Statusbereich, grosse Karte auf der Simulationsseite.
Der Punkt wird aus Breite/Laenge berechnet (equirectangular:
`x=(lon+180)/360`, `y=(90-lat)/180`) und mit Koordinatentext beschriftet.

- **Grosse Karte interaktiv:** **Mausrad** = Zoom (bis 16x, cursorzentriert),
  **Ziehen** ausserhalb des Markers = Karte verschieben (Pan), **Doppelklick** =
  Ansicht zuruecksetzen.
- **Standort ziehen:** Marker greifen und verschieben. Beim Loslassen werden
  Breite/Laenge gesetzt, gespeichert, die Ausrichtung neu bestaetigt und (wenn
  verbunden) `CONF` an den ESP32 gesendet. Das Ziehen stoppt einen laufenden
  Betrieb. Die kleine Karte rechts unten bleibt reine Anzeige.
- Quelle: `pc/weltkarte.png` – vom Nutzer bereitgestellte **Plexus-Weltkarte**,
  2:1, dunkler Hintergrund, equirectangular. Offline, kein Netz.
- Neues Modul `weltkarte.py` (Projektion, Zoom/Pan, Drag & Drop).

## Ortsangabe (PC 0.6.6 / Firmware 0.6.2)

In den Einstellungen unter den Koordinaten gibt es Felder **Land** und **Stadt**.
Sie werden in `einstellungen.json` gespeichert und im Panel angezeigt – u. a. als
Label am Karten-Punkt (statt der Koordinaten). `konfiguration_senden` schickt
zusaetzlich `ORT <hex>` an den ESP32; das LCD zeigt den Ort als dritte
Wechselzeile (Winkel / Status / Ort). Umlaute werden als ae/oe/ue gesendet.

## Simulation immer (PC 0.6.5)

Die Simulation laeuft immer: Ist es nach Sonnenuntergang (Nacht), verwendet sie
automatisch das Sonnenfenster des **Folgetags** (`aktuelles_sonnenfenster`).
Auch die Tempo-Berechnung nutzt dasselbe Fenster.

## LCD (Firmware 0.6.1)

Das LCD zeigt **Datum und lokale Zeit** (`TT.MM.JJ HH:MM`). Zeile 2 wechselt
alle 3 s zwischen Winkeln (`Az### Ng##`) und Status (`Autonom`/`PC-Bereit`/
`Bereit`); waehrend einer Fahrt steht dort die Aktion.

## Alles steuern (PC 0.6.2)

- **Betriebsseite:** zentrale Nachfuehrung mit Umschaltung PC-Betrieb/Simulation
  oder Firmware-Autonomie, Anzeige des vom ESP32 berechneten Sonnenziels und
  einem **Direktbefehlsfeld** fuer beliebige Protokollbefehle (z.B. `STATUS`,
  `JOG AZ 5`, `MOVE EL 30`, `REF AZ`).
- **Einstellungen:** Konfiguration (Standort/Ausrichtung) senden und die im
  ESP32 gespeicherten Werte anzeigen; Auto Kalibrierung; **Einzelachsen-
  Kalibrierung** `CAL AZ` / `CAL EL` (erfordert Schaltertest 4/4).
- Einzelkalibrierung und Konfigurationsanzeige benoetigen Firmware 0.5.1.

## Autonomer Betrieb (Firmware 0.5.0)

Unter Einstellungen schaltet **Autonomer Betrieb starten** die Nachfuehrung im
ESP32 ein (`AUTOON`); vorher wird `CONF` mit Standort und Ausrichtung gesendet.
Voraussetzung: bestandener Gesamttest, Referenz, Grenztests, gueltige RTC und
bestaetigte Ausrichtung. Der ESP32 rechnet dann selbst (automatische MEZ/MESZ)
und parkt unter dem Horizont an sicherer AZ-MIN/EL-MIN. **Autonomer Betrieb
stoppen** (`AUTOOFF`) oder STOP beendet ihn. Kein PC noetig, solange der
autonome Betrieb laeuft.

## STOP, Speicher und Fortsetzen

Normales STOP, Trennen und Fahrtabschluss speichern die gezaehlte Position,
Kalibrierung und bestandene Grenztests dauerhaft im ESP32. Kein erneuter Test
beim Verbinden. PC-Freigaben und Simulationszeit stehen in `betrieb.json`;
**Simulation fortsetzen** setzt den pausierten Lauf fort. **Neuen Sonnentag starten**
beginnt bewusst von vorn. Einstellungen stehen weiterhin in `einstellungen.json`.

Nach Stromverlust mitten in einer Fahrt bleibt die Spanne erhalten, die Position
ist jedoch unbekannt. **Position ermitteln** faehrt nur MIN an und entlastet 10 Grad;
keine volle Neumessung. Auch verschobene Mechanik oder echte Kontaktfehler brauchen
erneute Referenzierung/Pruefung. Alte Firmware speicherte keine Positionen: Beim
ersten Upgrade sind diese nicht rekonstruierbar; der neue Gesamttest stellt sie her.

Einzeltests bleiben unter Komponententest verfuegbar. Gespeicherte Endlagen und
bestandene Grenztests werden dort nicht staendig wiederholt. Fuer eine absichtliche
vollstaendige Wiederholung den neuen Knopf Auto Kalibrierung verwenden.

## Weitere Bedienung

- Einstellungen: 10-Grad-Schritte innerhalb der Grenzen oder Haltemodus.
  Loslassen stoppt; normales STOP behaelt mit Firmware 0.4.1 die gezaehlte Referenz.
- Komponententest: begrenzte 5-Grad-Richtungstests, RTC und PC-Tasten.
- LCD: Text ans LCD senden uebertraegt zwei Zeilen an das echte 16x2-Display
  (Adresse 0x27, SDA21/SCL22), sofern Firmware 0.3.2 installiert ist. Je Zeile
  maximal 16 druckbare Zeichen; Umlaute werden ae/oe/ue/ss. Die separate Taste
  Nur PC-Vorschau aktualisieren uebertraegt nichts. Erfolgsantwort bedeutet
  I2C-Textuebertragung; sichtbare Zeichen am LCD muss der Bediener kontrollieren.
  Kein LCD-Test waehrend laufender Motorfahrt oder Automatik.
- Motortests zeigen fehlende Verbindung, laufende Fahrt und Fahrgrenze direkt.
  Bei unbekannter Position sind begrenzte 5-Grad-Tests moeglich. An bekannter
  MIN ist nur die Richtung weg von MIN freigegeben. Grenzen bleiben aktiv.
- Abschluss von Kalibrierung und Grenztests wird im Protokoll explizit gemeldet.
  Bestandene Grenztests werden wiederverwendet. Eine vorhandene
  Positionsreferenz wird weiterhin nicht durch unnoetiges REF verworfen.
- Dunkles Design mit vier Menues basiert auf der Nutzervorlage, gesichert unter
  `vorlagen/solartracker_ui_design1.py`; Original im Downloads-Ordner unveraendert.

## Aufbau und Tests

- `bedienfeld_qt.py`: neue Oberflaeche, Grafik und Bedienung.
- `design_basis.py`: Layout und Achsenanzeigen der Vorlage.
- `steuerzentrale.py`: Freigaben, Rueckmeldungen und Bewegungsablauf.
- `tageslauf.py`: Sonnenstunden und Zielabbildung ab sicherer MIN.
- `sonne.py`: bestehende NOAA-Naeherung; `verbindung.py`: serielles Protokoll 3.
- `bedienfeld.py`: bisheriger Tk-Altstand, nicht mehr von Start.cmd gestartet.
- `../PCSteuerung`: Firmware 0.4.3, Kalibrier- und Positionsspeicher und Motorschutz.

Auf einem neuen PC Python installieren (mit Tcl/Tk fuer Altstand-Tests), dann
`Einrichtung.ps1` ausfuehren. Im Ordner pc:

```powershell
.\.venv\Scripts\python.exe bedienfeld_qt.py
.\.venv\Scripts\python.exe -m unittest -v test_pc test_gui test_design test_tageslauf
```

79 Tests bestanden, die neue Tagesgrafik wurde visuell geprueft.
Die Tests verwenden einen simulierten seriellen Anschluss. Der komplette
Tageslauf einschliesslich Start, Grenzen und Rueckkehr wird damit geprueft;
der neue Sonnenlauf muss noch am realen Panel beobachtet werden. Keine echte
Motorfahrt wurde fuer diese Aenderung gestartet. Firmware-Upload und LCD-Status
stehen in `../PCSteuerung/README.md`.

LCD-Hardwaretest am 17.09.2026 erfolgreich: Uebertragung mit Firmware 0.3.2
bestaetigt; Benutzer sieht SolarTracker / LCD Test OK auf dem echten Display.

## Komponententest-Navigation ab 0.5.5

Komponententest in der linken Navigation oeffnet immer die urspruengliche
Auswahl: Azimut-Motor, Elevations-Motor, Endschalter, RTC DS3231, LCD 16x2 und
Bedientasten. Zur Auswahl bleibt oberhalb des Testinhalts erreichbar. Lange
Unterseiten scrollen einzeln; ein neuer Test beginnt am oberen Seitenrand.
Die Funktionen verwenden weiterhin echte ESP32-Rueckmeldungen und Fahrgrenzen.
Graue Motor-Richtungstasten zeigen bei fehlender Verbindung/laufender Fahrt
oder erreichter Grenze einen Grund im Testfeld bzw. als Hinweis beim Zeigen.
Diese Oberflaechenkorrektur benoetigt keinen neuen Firmware-Upload.

## Bedientasten, STOP und Protokoll ab 0.5.5

Bedientasten-Test ist jetzt eine echte Motorbedienung: Links/Rechts fahren
Azimut um -/+5 Grad, Oben/Unten Elevation um +/-5 Grad. Positive EL-Fahrt kippt
das Panel aus der senkrechten Stellung in Richtung waagerecht. Ein Mausklick
startet genau eine Fahrt. Halten loest keinen Dauerlauf aus. STOP/ENTER in der
Mitte, STOPP/ESC links und die Esc-Taste stoppen. Die Pfeiltasten auf der
PC-Tastatur sind nicht mit Motorfahrten belegt.

Ohne Verbindung, waehrend einer Fahrt oder an einer bekannten sicheren Grenze
sind die betroffenen Richtungen gesperrt. Ohne Positionsreferenz bleiben die
begrenzten Richtungstests moeglich; sie ersetzen keine Kalibrierung.
Fahrt angefordert bezeichnet einen gesendeten Befehl, keine bestaetigte Bewegung.

STOPP/ESC und Protokoll stehen links direkt unter der Schaltflaeche
Komponententest. Rechts bleiben die Positionsanzeigen. Die linke Navigation
wird bei kleinen Fenstern kompakter, damit STOP und Protokoll sichtbar bleiben.
Zum Laden der neuen Version das alte Fenster schliessen und Start.cmd erneut
oeffnen. Kein Firmware-Upload erforderlich.
