# Aenderungsprotokoll ESP32

## PC 0.7.4 / Dokumentation 0.41 - 24.09.2026

- **Globus-Doppelklick ohne `pick`** geloest: Die Position wird **analytisch aus
  der Kamera** berechnet (Ray-Sphere), unabhaengig von Renderer/`pick`. Damit
  funktioniert der Klick auf die Kugel zuverlaessig und setzt Standort +
  Land/Stadt (Marker springt).
- Verifiziert: analytischer Klick exakt (Mittelpunkt -> Standort); flache Karte
  korrekt kalibriert. 116 PC-Tests bestanden.

## PC 0.7.3 / Dokumentation 0.40 - 24.09.2026

- **Globus-Doppelklick repariert**: Eingabe laeuft jetzt ueber eine `MouseArea`
  (vorher Konflikt DragHandler/TapHandler) -> Doppelklick auf **Karte oder Kugel**
  setzt die Panel-Position; der rote Punkt springt.
- Doppelklick setzt zusaetzlich **Land/Stadt** auf den naechstgelegenen Ort,
  sodass Name/Breite/Laenge auf **Karte und Globus** angezeigt werden.
- 116 PC-Tests bestanden; QML fehlerfrei geladen.

## PC 0.7.2 / Dokumentation 0.39 - 24.09.2026

- Kugel: **Drehrichtung korrigiert** (natuerliches Greifen), **Mausrad zoomt nur
  die Kugel** (die Seite scrollt nicht mehr), **Doppelklick auf Karte ODER Kugel**
  setzt die Panel-Position (roter Punkt springt, speichern + Ausrichtung +
  `CONF`/`ORT`/`TZ`). Marker-Ziehen auf der Karte bleibt.
- Neuer Button **"Ansicht zuruecksetzen"** unten rechts auf Karte/Globus.
- 116 PC-Tests bestanden.

## PC 0.7.1 / Dokumentation 0.38 - 24.09.2026

- Globus verbessert: **Drehen korrigiert** (absolute Drehung ab Drag-Start statt
  aufsummierender Translation -> ruhig und kontrolliert), **groessere Kugel**
  (Kamera naeher), **geschmeidiger Mausrad-Zoom** (exponentiell, Bereich 0.5-3.2),
  **Doppelklick** auf einen Ort setzt die Panel-Position (statt einfachem Klick).
- 116 PC-Tests bestanden.

## PC 0.7.0 / Firmware 0.7.0 / Dokumentation 0.37 - 24.09.2026

- **Interaktiver 3D-Globus** (QtQuick3D/QML) auf der Simulationsseite:
  Plexus-Textur, Gitter alle 15 Grad, roter Standort-Marker, Beschriftung
  Name/Breite/Laenge/Ortszeit. Ziehen = drehen, Mausrad = Zoom (scharf),
  **Klick auf die Kugel setzt den Standort**. Umschalter Karte <-> Globus;
  die kleine Karte rechts unten bleibt flach.
- **Zeitzone:** neues Feld "Zeitzone (UTC-Versatz)" (Vorschlag aus der Laenge).
  Diagramm und Simulation rechnen in **Ortszeit** statt PC-Zeit (z. B. Nepal).
  Firmware 0.7.0: Befehl `TZ <minuten>` (NVS); `sonnenstand`/`kalenderZeit`
  nutzen den festen Versatz (Fallback EU-Sommerzeit). `CONF` sendet `TZ` mit.
- **"Ort aus Koordinaten uebernehmen"** wandert unter die grosse Karte/den Globus.
- 116 PC-Tests bestanden; Firmware kompiliert (343340 Byte).

## PC 0.6.7 / Dokumentation 0.36 - 22.09.2026

- Offline-Ortsvorschlag: Button **„Ort vorschlagen (aus Koordinaten)"** unter den
  Koordinaten setzt **Land/Stadt** auf den naechstgelegenen Ort (ueberschreibt sie).
  Zusaetzlich **automatisch**: beim Start und bei Koordinatenaenderung werden
  leere Felder gefuellt. Daten: Natural Earth `ne_50m_populated_places`
  (public domain, 1251 Orte) in `pc/orte.json`, Modul `orte.py`. Rein offline.
- 114 PC-Tests bestanden.

## PC 0.6.6 / Firmware 0.6.2 / Dokumentation 0.35 - 22.09.2026

- Ortsangabe: In den Einstellungen unter den Koordinaten neue Felder **Land**
  und **Stadt**. Sie werden in `einstellungen.json` gespeichert und im
  PC-Bedienfeld angezeigt (u. a. als Label am Karten-Punkt statt der Koordinaten).
- Firmware 0.6.2: neuer Befehl `ORT <hex>` (16 ASCII-Zeichen) speichert den
  Ortsnamen im NVS. Das LCD zeigt ihn als dritte Wechselzeile (Winkel / Status /
  Ort). Status ergaenzt `ort_supported`.
- `konfiguration_senden` sendet zusaetzlich `ORT`. 111 PC-Tests bestanden;
  Firmware kompiliert (342948 Byte).

## PC 0.6.5 / Firmware 0.6.1 / Dokumentation 0.34 - 22.09.2026

- LCD zeigt jetzt **Datum und lokale Zeit**: Zeile 1 `TT.MM.JJ HH:MM`. Zeile 2
  wechselt alle 3 s zwischen Winkeln (`Az### Ng##`) und Status (`Autonom`/`PC`/
  `Bereit`); waehrend einer Fahrt wird die Aktion angezeigt. Neues Kalender-
  Hilfsmodul in `Sonne` (`kalenderZeit`).
- **Simulation laeuft immer**: Nach Sonnenuntergang verwendet sie automatisch
  das Sonnenfenster des **Folgetags** (`aktuelles_sonnenfenster`), auch wenn es
  nachts ist. Gilt fuer Simulation und die Tempo-Berechnung im PC.
- 108 PC-Tests bestanden; Firmware kompiliert (341952 Byte).

## PC 0.6.4 / Dokumentation 0.33 - 21.09.2026

- Weltkarte interaktiv (grosse Karte auf der Simulationsseite):
  - **Zoom** per Mausrad, cursorzentriert, bis 16x.
  - **Karte verschieben (Pan)** per Ziehen ausserhalb des Markers.
  - **Doppelklick** setzt die Ansicht auf 1x zurueck.
- **Standort per Drag & Drop**: Marker greifen und verschieben. Beim Loslassen
  werden Breite/Laenge gesetzt, in `einstellungen.json` gespeichert, die
  Ausrichtung neu bestaetigt und (wenn verbunden) per `CONF` an den ESP32
  gesendet. Das Ziehen stoppt einen laufenden Betrieb (Sicherheit).
- Marker-Quelle sind die Einstellungsfelder; externe Status-Updates werden
  waehrend des Ziehens ignoriert. Die kleine Karte rechts unten bleibt Anzeige.
- Umkehrprojektion `ort_aus_bildanteil` ergaenzt; 107 PC-Tests bestanden.

## PC 0.6.3 / Dokumentation 0.32 - 21.09.2026

- Weltkarte im PC-Bedienfeld: Der Panel-Standort wird als Punkt aus Breite/
  Laenge berechnet (equirectangular, `x=(lon+180)/360`, `y=(90-lat)/180`) und
  markiert. Kleine Karte rechts unten, grosse Karte auf der Simulationsseite.
- Neues Modul `weltkarte.py`; Bild `pc/weltkarte.png` (vom Nutzer
  bereitgestellte Plexus-Weltkarte, 2:1, offline). Marker aus ESP32-
  Konfiguration (`lat`/`lon`) bzw. den Einstellungen; Punkt mit Koordinatentext.
- 105 PC-Tests bestanden (3 neue fuer die Projektion); Projektion visuell
  geprueft (Marker ueber Bad Vilbel).

## Firmware 0.6.0 / Dokumentation 0.31 - 21.09.2026

- Live-LCD-Anzeige im Normalbetrieb und autonomen Betrieb:
  - Zeile 1: lokale Zeit (MEZ/MESZ) und Status/Aktion (Bereit / PC / Autonom
    bzw. Fahrt, SuMIN/SuMAX, FMIN/FMAX, Entlastung, Grenztest).
  - Zeile 2: Azimut und Panelneigung aus der gezaehlten Position.
  - Waehrend der Auto Kalibrierung bleibt der Schritt-Text (autoAnzeige) sichtbar.
  - Nach einem manuellen LCD-Text (`LCD ...`) bleibt die eigene Anzeige 30 s
    stehen, danach uebernimmt wieder der Live-Status.
- Protokoll 3, margin=114, Speicherformat und Fahrlogik unveraendert.

## PC 0.6.2 / Firmware 0.5.1 / Standalone 0.8 / Dokumentation 0.30 - 21.09.2026

- Alles laesst sich vom PC-Bedienfeld aus steuern:
  - Direktbefehlsfeld fuer beliebige Protokollbefehle (z.B. STATUS, JOG AZ 5).
  - Konfiguration senden und die im ESP32 gespeicherte Konfiguration anzeigen.
  - Einzelachsen-Kalibrierung (`CAL AZ` / `CAL EL`).
  - Zentrale Nachfuehrung auf der Betriebsseite: PC-Betrieb/Simulation oder
    Firmware-Autonomie, mit Anzeige des Sonnenziels.
- Firmware 0.5.1: Status meldet Konfiguration (`lat`, `lon`, `az_null`,
  `el_neigung`) und Sonnenziel (`sun_az`, `sun_el`) in Schritten.
- Standalone-Firmware 0.8: serielle Menue-Fernbedienung (u/d/l/r/e/b) fuer das
  LCD-/Joystick-Menue; Joystick bleibt unveraendert nutzbar.
- 102 PC-Tests bestanden; beide Firmwaren kompilieren. Protokoll 3, margin=114.

## Firmware 0.5.0 / Dokumentation 0.29 - 20.09.2026

- Autonomer Betrieb: Der ESP32 fuehrt die Sonne ohne PC nach. Neues Modul
  `Sonne.h/.cpp` (NOAA-Naeherung und Zielabbildung, gegen die PC-Referenz
  sonne.py/tageslauf.py geprueft: 0 Abweichungen).
- Konfiguration (Breite, Laenge, az_null, el_neigung) und Autonomie-Flag liegen
  im ESP32-NVS. Neue Befehle: `CONF <lat> <lon> <aznull> <elneigung>`,
  `AUTOON`, `AUTOOFF`. Status ergaenzt `auto_mode` und `conf_ok`.
- Automatik startet nur bei bestandenem Gesamttest (auto_ok), Referenz,
  Grenztests, gueltiger RTC und vorhandener Konfiguration. Ein Ziel wird pro
  Minute aus RTC und Sonnenstand berechnet; beide Achsen nacheinander.
- Unter dem Horizont parkt der Tracker an sicherer AZ-MIN und EL-MIN (Panel
  senkrecht, windgeschuetzt). Zeitzone automatisch MEZ/MESZ (EU-Regel).
- STOP deaktiviert den autonomen Betrieb wieder. Protokoll bleibt 3,
  `margin`=114. Protokollversion der Firmware jetzt 0.5.0.
- Am Modell geprueft: Firmware 0.5.0 geladen, `CONF` gesetzt (conf_ok=true),
  `AUTOON` aktiviert; beide Achsen fuhren selbststaendig zur Sonnenposition
  (AZ 114->297, EL 114->277). `AUTOOFF` beendete den Betrieb; Referenz,
  Grenztests und Spannen blieben erhalten. 102 PC-Tests bestanden.

## Firmware 0.4.3 / Dokumentation 0.28 - 20.09.2026

- Am Modell: Firmware 0.4.1 hochgeladen und Auto Kalibrierung ausgefuehrt. Der
  Gesamttest lief nach zwei Korrekturen erstmals vollstaendig durch: auto_ok=true,
  beide Achsen an sicherer MIN (114), Spannen AZ=2202 / EL=1258, Referenz und
  Grenztests gesetzt.
- 0.4.2: Richtungs-Endschalter werden erst nach 30 ms stabilem Low ausgewertet
  (neues Modul Entprellung.h mit Compilezeit-Test). Einzelne Prell-/Stoerimpulse
  loesten zuvor eine MIN-Suche bzw. einen Grenztest vorzeitig aus; die AZ-Spanne
  streute dadurch stark (2216/2649/2372).
- 0.4.3: Schritttakt von 3 ms auf 5 ms erhoeht. Bei 3 ms verlor der belastete
  28BYJ-48 Schritte, wodurch der Grenztest den MIN-Schalter bei 114 Schritten
  noch als gedrueckt erkannte. Mit 5 ms sind Kalibrierung, Grenztests und
  Rueckkehr reproduzierbar.
- Protokoll 3 und margin=114 unveraendert; Speicherformat, Motorbelegung und
  Schutzlogik unveraendert. Kein autonomer Betrieb.

## PC 0.6.1 / ESP32 0.4.1 / Dokumentation 0.27 - 18.09.2026

- Einstellungen: Auto Kalibrierung startet ausdruecklich einen vollstaendigen
  Test: LCD-Ausgabe, RTC-Zeitfortschritt, AZ/EL MIN/MAX mit je 114 Schritten
  Entlastung, Speicherung, beide sicheren Grenzen und Rueckkehr zur Startposition.
- Einzelne Schritte und Fehler erscheinen auf dem LCD und im PC-Status.
  Betrieb/Simulation werden erst nach bestandenen Tests und bestaetigter
  Ausrichtung gruen. STOP/ESC und Protokoll bleiben links unter Komponententest.
- Normales STOP, Trennen und abgeschlossene Fahrten speichern Position, Phase,
  Kalibrierung und Grenztests im ESP32-NVS mit Pruefsumme. PC speichert
  Freigaben und pausierte Simulation atomar in betrieb.json.
- Stromausfall waehrend einer Fahrt macht nur die Positionsreferenz unbekannt;
  HOME stellt sie ueber MIN mit Entlastung wieder her. Keine erfundene Position.
- 102 PC-/GUI-Tests bestanden. ESP32-Build erfolgreich; echter automatischer
  Motorablauf noch am Modell zu pruefen. Uploadstatus siehe Firmware-README.


## PC-Bedienfeld 0.5.5 / Dokumentation 0.26 - 18.09.2026

- STOPP/ESC und Protokoll gemaess Nutzerkorrektur links direkt unter der
  Schaltflaeche Komponententest angeordnet. Rechts stehen die Positionsanzeigen.
- Linke Leiste bei kleinen Fenstern kompakter; STOP und Protokoll bleiben sichtbar.
- 19 GUI-Tests bestanden, Anordnung visuell geprueft. Motorbefehle/Firmware unveraendert.

## PC-Bedienfeld 0.5.4 / Dokumentation 0.25 - 18.09.2026

- Bedientasten-Test steuert echte begrenzte 5-Grad-Fahrten: Links/Rechts AZ-/AZ+,
  Oben/Unten EL+/EL-. STOP/ENTER sendet STOP; Esc bleibt globaler Stopp.
- Verbindung, laufender Auftrag und sichere Grenzen sperren unzulaessige
  Richtungen. Keine automatische Motorfahrt, kein Dauerlauf durch Gedrueckthalten.
- STOP/ESC und Protokoll bleiben rechts oben sichtbar; Positionsanzeigen
  darunter sind separat scrollbar. Seitenleisten passen sich kleinen Fenstern an.
- Ueberfluessige Beschreibung auf Test-Unterseiten ausgeblendet, damit alle
  Richtungstasten sichtbar bleiben. Auswahl und Ruecknavigation unveraendert.
- 79 Tests bestanden; letzte Layoutanpassungen mit allen 19 GUI-Tests erneut
  geprueft und kleine Fenster visuell kontrolliert. Keine echte Motorfahrt.
- Firmware bleibt 0.3.2; kein Upload erforderlich.

## PC-Bedienfeld 0.5.3 / Dokumentation 0.24 - 17.09.2026

- Komponententest behaelt die sechs Auswahlkarten und ihre urspruengliche Reihenfolge.
- Erneuter Klick auf Komponententest fuehrt zur Auswahl; feste Zur-Auswahl-Taste
  oberhalb der Unterseiten. Jede Unterseite scrollt unabhaengig, beginnt oben
  und vergroessert nicht mehr die anderen Tests oder die Auswahlseite.
- Auswahl kompakt oben angeordnet; keine unnoetigen grossen Leerraeume.
- 75 Tests bestanden, darunter alle sechs Auswahlwege, Ruecknavigation,
  Scrollen sowie Motor- und LCD-Befehle. Darstellung auf kleinerem Fenster geprueft.
- Firmware 0.3.2 und Schutzpruefungen unveraendert; kein Upload/Motorstart.

## Dokumentation 0.23 - 17.09.2026

- Benutzer bestaetigt beide sichtbaren LCD-Zeilen: SolarTracker / LCD Test OK.
- LCD-Hardwaretest mit Firmware 0.3.2 und PC-Steuerung 0.5.2 abgeschlossen:
  Uebertragung, I2C-Erreichbarkeit und sichtbare Ausgabe bestaetigt.
- Keine neue Motorpruefung oder Aenderung der Kalibrierdaten.

## Dokumentation 0.22 - 17.09.2026

- Firmware 0.3.2 erfolgreich auf COM3 hochgeladen, Flash-Pruefsumme verifiziert.
- Echter LCD-Befehl ueber PC-Steuerzentrale bestaetigt: SolarTracker / LCD Test OK.
  ESP32 meldet lcd_supported=true und lcd_present=true; Sichtpruefung ausstehend.
- RTC mit echter PC-Zeit synchronisiert und gueltig. Beide Motoren in Ruhe,
  vier Kontakte offen, gespeicherte Spannen AZ=2145 / EL=1242 unveraendert.
- Keine Motorfahrt gestartet. Referenzen nach Neustart unbekannt, Grenztests offen.

## PC-Bedienfeld 0.5.2 / Firmware 0.3.2 / Dokumentation 0.21 - 17.09.2026

- Bestaetigte Geometrie: EL-MIN senkrecht (Panelneigung 90 Grad), positive Fahrt
  kippt Richtung waagerecht. Panelneigung und Sonnenhoehe getrennt dargestellt.
- Einstellungen Format 3 mit el_neigung; Formate 1/2 werden umgerechnet.
- LCD-Hardwaretest in Firmware und PC ergaenzt: zwei 16-Zeichen-Zeilen per
  ASCII-Hex, bestehende LiquidCrystal-I2C-Initialisierung aus dem Einzeltest.
  Alte Firmware wird als ohne LCD-Unterstuetzung erkannt; keine Scheinerfolge.
- Motor-Komponententests zeigen Sperrgruende; Grenztests bewusst wiederholbar.
  Erfolgreiche Kalibrierung/Grenztests erscheinen als Abschluss im Protokoll.
- 73 Python-/GUI-Tests bestanden; LCD-Parser mit Compilezeit-Tests abgesichert.
- Kalibrierspeicher/Motorbelegung/10-Grad-Schutz unveraendert, keine Motorfahrt.
- Build 0.3.2 erfolgreich (320980 Byte Programm, 23900 Byte globale Variablen).
  Upload noch offen: Wrong boot mode (0x13); LCD-Hardwarepruefung ausstehend.
  Details siehe PCSteuerung/README.md.

## PC-Bedienfeld 0.5.0 / Dokumentation 0.20 - 16.09.2026

- Simulation faehrt zuerst beide sicheren MIN-Positionen an, durchlaeuft nur
  Sonnenaufgang bis Sonnenuntergang des aktuellen PC-Datums und kehrt danach
  automatisch zu AZ-MIN / EL-MIN zurueck. Abstand 114 Schritte bleibt erhalten.
- Tageslichtfenster aus bestehender NOAA-Naeherung (geometrischer Horizont).
  Grafik/CSV enthalten nur Sonnenstunden; 30/60/120-s-Vorgaben gelten dafuer.
- Ausrichtung und Winkelanzeige beziehen sich auf sichere MIN: AZ dort 90 Grad
  Osten. EL bleibt vorlaeufig beim bisherigen Startwinkel 0 Grad.
- Ziele werden innerhalb der sicheren Grenzen begrenzt und als solche gemeldet;
  beide Achsen erreichen jedes Zielpaar, bevor die Simulationszeit weiterlaeuft.
- Normalbetrieb parkt nachts ebenfalls an beiden sicheren MIN-Positionen.
- Einstellungsformat 2; alte mechanische Nullpunkte werden beim Laden umgerechnet.
  Lokale Nutzereinstellung AZ explizit auf 90 Grad gesetzt, alte Datei gesichert.
- Firmware/Flash-Kalibrierung unveraendert. Keine reale Motorfahrt gestartet.
- 60 Tests bestanden; Tagesgrafik und Bedienung visuell geprueft.

## PC-Bedienfeld 0.4.1 / Dokumentation 0.19 - 16.09.2026

- Referenzwiederherstellung bei bereits gueltiger Referenz in Oberflaeche und
  Steuerzentrale gesperrt: versehentliches REF verwirft keine Grenztests mehr.
- Tasten zeigen Referenz OK und bestandene Grenztests direkt an.
- 49 Software-/GUI-Tests bestanden, keine Motorfahrt oder Firmwareaenderung.
- Bereits durch REF geloeschte Grenztestergebnisse werden nicht rekonstruiert.

## PC-Bedienfeld 0.4.0 / Dokumentation 0.18 - 16.09.2026

- PySide6-Oberflaeche aus der bereitgestellten Design-1-Vorlage umgesetzt;
  Vorlage im Projekt gesichert, Start.cmd startet das neue Fenster.
- Echte serielle Steuerung, NOAA-Grafik und Simulation, Einstellungen,
  automatische Endschaltertests, Grenztests und RTC angebunden.
- Kalibrierung, Referenz, Kontakte und Grenztest getrennt dargestellt;
  Diagnose kopierbar. Keine erfundenen Positionen ohne Referenz.
- STOP/Esc, Haltemodus und Freigaben geprueft. LCD ist lokale Vorschau.
- 46 Tests bestanden, alle Seiten gerendert und visuell geprueft.
- Firmware bleibt 0.3.1 / Protokoll 3. Keine reale Motorfahrt oder Upload;
  gemeldete Grenztest-Ablehnung am Geraet weiterhin zu diagnostizieren.

## Dokumentation 0.17 - 15.09.2026

- Korrektur 0.3.1 erfolgreich auf COM3 hochgeladen, Flash-Pruefsumme verifiziert.
- Status ueber Python geprueft: Version 0.3.1, beide Achsen in Ruhe, vier Kontakte
  offen, RTC vorhanden/gueltig. Beide Achsen weiterhin unkalibriert/nicht referenziert.
- Keine Motorfahrt gestartet; Korrektur am mechanischen Ablauf noch zu pruefen.

## PC-Steuerung 0.3.1 / Dokumentation 0.16 - 15.09.2026

- Fehlerquelle in der Gegenkontaktfreigabe korrigiert: einzelner offener Read
  entwaffnet den bekannten Kontakt nicht mehr; 25 ms stabil offen erforderlich.
- Entlastungsphasen erkennen den zuvor ausgeloesten Kontakt auch bei prellendem
  Start-Read. Fahrtrichtung wird fuer die gesamte Phase gespeichert.
- Am Ende der 114-Schritt-Entlastung wird ohne weitere Schritte bis maximal
  100 ms auf einen stabil offenen Kontakt gewartet; echte Fehler stoppen weiter.
- Fehlerdiagnose zeigt Achse, Phase, Richtung, Schrittzahl und MIN/MAX-Signale.
- 26 Python-/GUI-Tests erfolgreich. Compilezeit-Tests fuer Prellen, erneuten
  Kontakt, Klemmen nach 114 Schritten und millis-Ueberlauf ergaenzt.
- Firmware-Build erfolgreich: 318968 Byte Programm, 23884 Byte globale Variablen.
- Upload wegen belegtem COM3 noch offen; Board weiterhin 0.3.0.
- Physische Ursache am Modell noch offen. Ungueltige/abgebrochene Kalibrierung
  wird weiterhin nicht als gueltige Endlage gespeichert. Deployment siehe Firmware-README.

## PC-Steuerung 0.3.0 / Dokumentation 0.15 - 15.09.2026

- Endschaltertest per Knopfdruck automatisch: Azimut, danach Elevation; MIN/MAX
  anfahren, sofort stoppen, jeweils 10 Grad entlasten und Endlagen speichern.
- Fehler/STOP brechen die ganze Sequenz ab; die naechste Achse startet dann nicht.
- Fortschritt und aktive Phase im PC-Fenster, keine Handbetaetigung mehr noetig.
- Protokoll 3 verlangt HELLO 3, damit alte Clients keine unerwartete Fahrt ausloesen.
- Gueltige gespeicherte Kalibrierungen werden nach Neustart wieder anerkannt;
  Positionsreferenz und Grenztests bleiben erforderlich. Speicherformat unveraendert.
- 25 Python-/GUI-Tests erfolgreich; Reihenfolge/Abbruch/Wiederherstellung im
  Firmware-Build geprueft (318556 Byte Programm, 23852 Byte globale Variablen).
- Upload nach Freigabe von COM3 erfolgreich, Flash-Pruefsumme verifiziert.
- Zusaetzlicher serieller Statuscheck danach wegen erneut belegtem COM3 nicht
  moeglich. Kein automatischer Motortest durch den Assistenten gestartet.
- Physischer automatischer Ablauf noch nicht am Modell getestet.

## Dokumentation 0.14 - 15.09.2026

- DS3231 erneut ueber COM3 synchronisiert: TIME bestaetigt, RTC vorhanden und
  gueltig. Rueckgelesen 18:12:10 MESZ, Abweichung zur PC-Zeit 1 Sekunde.
- Beide Motoren in Ruhe; keine Motorfahrt angefordert. Firmware unveraendert 0.2.0.

## Dokumentation 0.13 - 15.09.2026

- PC-Firmware 0.2.0 erfolgreich auf COM3 geladen, Flash-Pruefsumme verifiziert.
- Python-Verbindung mit Protokoll 2 erfolgreich, AUTO ohne bestandene Tests
  erwartungsgemaess gesperrt. Keine Motorbewegung ausgefuehrt.
- RTC-Synchronisierung versucht: DS3231 nicht erreichbar, keine Zeit gesetzt.
- Status: beide Achsen in Ruhe, unkalibriert/nicht referenziert; Elevation-MIN
  aktiv, andere drei Kontakte offen. Physische Kontrolle noch erforderlich.
- Uploadstatus und Hardwarebefund in den READMEs dokumentiert; Code unveraendert.

## PC-Steuerung 0.2.0 / Dokumentation 0.12 - 15.09.2026

- Datum/Startzeit automatisch vom PC; Standort eingeben und Tempo per Dropdown
  oder Zahl einstellen. DS3231 beim Verbinden mit echter PC-UTC synchronisieren.
- Simulation startet Grafik und Panel gemeinsam; die Simulationsuhr wartet bei
  laufender Motorfahrt. Keine beschleunigte Zeit in die RTC schreiben.
- Verbindlicher Schaltertest (vier Kontakte einzeln), Kalibrierung/Referenz und
  Grenztests vor Automatik. Physischer Abstand muss zusaetzlich bestaetigt werden.
- Firmware-Protokoll 2 mit TIME, SWTEST, LIMIT und gesperrtem AUTO-Befehl.
- 23 Python-/GUI-Tests erfolgreich, Schalterfolge per Compilezeit-Test geprueft.
- Firmware-Build erfolgreich: 318276 Byte Programm, 23860 Byte globale Variablen.
- Oberflaeche 0.2.0 geoeffnet. Upload noch nicht erfolgreich (0x7B);
  Board weiterhin 0.1.0. RTC-Hardwaretest und mechanische Tests stehen aus.

## Dokumentationsversion 0.11 – 15.09.2026

- PC-Firmware 0.1.0 erfolgreich auf COM3 geladen, Flash-Pruefsumme verifiziert.
- HELLO/PING, Status und STOP-Quittung mit dem Python-Verbindungsmodul geprueft.
- Beide Achsen in Ruhe, unkalibriert und nicht referenziert; alle vier Kontakte offen.
- Keine Motorfahrt angefordert; physische Schaltertests und Kalibrierung stehen aus.
- Uploadstatus in den READMEs aktualisiert; Programmversionen unveraendert.

## Dokumentationsversion 0.10 / PC-Steuerung 0.1.0 – 15.09.2026

- Python-PC-Bedienfeld mit vier Registerkarten, Richtungstasten, Einstellungen,
  Kalibrierung, Referenzbestaetigung, Normalbetrieb, Simulation und Tagesgrafik erstellt.
- Standort/Ausrichtung lokal speicherbar, Tageskurve als CSV exportierbar.
- Eigene ESP32-Firmware mit seriellem Protokoll, Quittungen, Status und Watchdog;
  Azimutbelegung aus MotorTestAz (16/17/18/19) uebernommen.
- Endlagen je Achse dauerhaft gespeichert, normale Fahrt mit 114 Schritten
  (mindestens nominal 10 Grad) Abstand, keine automatische Fahrt beim Neustart.
- Python 3.13 und lokale Umgebung mit pyserial 3.5 eingerichtet; Bedienfenster gestartet.
- 17 Python-/GUI-Tests erfolgreich. ESP32-Build: 290428 Byte, 22356 Byte RAM.
- Upload auf COM3 scheitert noch am Bootmodus 0x13; Hardware-Verbindungstest,
  Drehrichtung und mechanische Kalibrierung bleiben ausstehend.
- Alte Hauptsketche und bestehende Hardwaretests unveraendert.

## Dokumentationsversion 0.9 – 14.09.2026

- LCD-/Joystick-Menue 0.1 erfolgreich mit 115200 Baud auf COM3 geladen, Flash-Pruefsumme verifiziert und ESP32 neu gestartet.
- Uploadstatus aktualisiert; Anzeige und Bedienung am Geraet noch zu bestaetigen. Testcode unveraendert.

## Dokumentationsversion 0.8 / LCD-Joystick-Menue 0.1 – 14.09.2026

- ESP32-Build erfolgreich (307620 Byte Programm, 23740 Byte globale Variablen), Navigation und Tasterlogik beim Kompilieren geprueft. Kein Upload ausgefuehrt; Hardwaretest noch ausstehend.

- Eigenstaendigen Menue-Test mit vier Hauptpunkten und saemtlichen vorgegebenen Untereintraegen erstellt.
- Joystick-Navigation, entprellter kurzer/langer Tastendruck, Wiederholung beim Blaettern, Mittelstellungsermittlung und Scrolltext ergaenzt.
- Navigation und Tasterverhalten werden durch Compilezeit-Pruefungen abgesichert. Funktionsseiten bleiben ausdrueckliche Menue-Vorschauen ohne Motoraktionen.
- Aktuelle Joystick-Belegung aus dem Code uebernommen (35/32/12); Konflikt zwischen SW und Elevation-MAX im Hauptprogramm dokumentiert. Hauptprogramm unveraendert.

## Dokumentationsversion 0.7 / Achsen-Testversion 0.2 – 11.09.2026

- Build erfolgreich (289348 Byte Programm); Upload von 0.2 wegen `Wrong boot mode (0x13)` noch ausstehend. Versorgung und Signalleitungen vom Benutzer bestaetigt.

- Kurze Richtungspruefung `u`/`v` auf 100 ms pro Halbschritt verlangsamt; etwa sechs Sekunden LED-Beobachtung bei gleicher 5-Grad-Strecke.
- Endschalter und manueller Stopp weiter aktiv; Selbsttest fuer langsamen Takt, beide Richtungen und Abschaltung erweitert.
- Statusmeldung unterscheidet ausgegebene Schrittfolge von echter Motorbewegung. Im ersten Test mit Version 0.1 waren laut Benutzer keine Bewegung und keine LEDs erkennbar.

## Dokumentationsversion 0.6 – 11.09.2026

- Achsen-Test 0.1 erfolgreich auf COM3 mit 115200 Baud hochgeladen; Flash-Pruefsumme verifiziert.
- Software-Selbsttest auf dem ESP32 erfolgreich. Status mit `?` ausgelesen: `Selbsttest: OK | Speicher: OK`.
- Azimut und Elevation noch nicht kalibriert; vier Schalter offen, normale Fahrt gesperrt, Motoren aus. Keine echte Motorbewegung gestartet.
- Upload- und Testnachweis in den READMEs aktualisiert; Testcode unveraendert.

## Dokumentationsversion 0.5 / Achsen-Testversion 0.1 – 11.09.2026

- Endgueltiger Build erfolgreich (288652 Byte Programm, 22236 Byte globale Variablen). Upload an COM3 wegen `Wrong boot mode (0x13)` noch nicht erfolgreich; Selbsttest auf dem Board und Hardware-Kalibrierung ausstehend.

- Separaten `AchsenTest` fuer Azimut und Elevation hinzugefuegt, standardmaessig Azimut ausgewaehlt.
- MIN/MAX je Achse eingemessen, nach Entlastung dauerhaft mit Pruefsumme in Preferences gespeichert; normale Fahrt mit jeweils 10 Grad Abstand zu den Schaltern.
- Keine automatische Fahrt nach Neustart; manuelle Bestaetigung einer markierten sicheren MIN-Position statt erneuter Schalterfahrt.
- Abgebrochene Kalibrierung bleibt ungueltig; Software-Selbsttest prueft Grenzen und Fehlerfaelle ohne GPIO-Zugriffe.
- Vollstaendige Anleitung unter `tests/AchsenTest/README.md`; Hardware-Kalibrierung noch ausstehend.

## Dokumentationsversion 0.4 / Azimut-Testversion 0.1 – 11.09.2026

- Eigenstaendigen Azimut-Motortest unter `tests/AzimutTest` hinzugefuegt.
- Endschalter an GPIO 4/5 stoppen die jeweilige Fahrt; anschliessend 10 Grad Entlastung (nominal 114 Halbschritte) in Gegenrichtung und Motor aus.
- Serielle Fahrbefehle, kurze Richtungspruefung, manueller Stopp, begrenzte Suchfahrt und Pruefung der Schalterfreigabe ergaenzt.
- Ablauf-Selbsttest ohne GPIO-Zugriff sowie ausfuehrliche Testanleitung hinzugefuegt.
- ESP32-Build erfolgreich; Hardwaretest noch ausstehend. Hauptprogramm unveraendert.

## Dokumentationsversion 0.3 – 09.09.2026

- Funktionierendes LCD anhand der Benutzer-Rueckmeldung dokumentiert.
- Ausfuehrliche Beschreibung von `tests/LcdTest/LcdTest.ino` in `tests/LcdTest/README.md` gespeichert: Anschluesse, Bibliotheken, Programmablauf, Diagnose, Upload und Sichttest.
- Projekt-README aktualisiert und Testanleitung verlinkt.
- LCD-Sketch bleibt unveraendert auf Testversion 0.2; dessen Build war erfolgreich, der letzte Upload durch den Assistenten scheiterte an `Wrong boot mode`. Die beim bestaetigten Erfolg laufende Version ist nicht eindeutig belegt.
- Dokumentationsaenderung; kein neuer Upload und keine Aenderung am Hauptprogramm.

## LCD-Testversion 0.2 – 09.09.2026

- I2C-Adresssuche beim Start und wiederkehrende Erreichbarkeitspruefung fuer `0x27` ergaenzt.
- LCD mit `init()`, `backlight()` und `display()` initialisiert; Ausgabe `SolarTracker` / `LCD Test OK`.
- Erfolgreich fuer `esp32:esp32:esp32` kompiliert.
