# Changelog

## PC 0.6.7 / Dokumentation 0.36 - 22.09.2026

- Offline-Ortsvorschlag: Button „Ort vorschlagen (aus Koordinaten)" fuellt leere
  Felder Land/Stadt mit dem naechstgelegenen Ort (Natural Earth, `pc/orte.json`,
  Modul `orte.py`). 114 PC-Tests bestanden.

## PC 0.6.6 / Firmware 0.6.2 / Dokumentation 0.35 - 22.09.2026

- Ortsangabe: Felder **Land** und **Stadt** unter den Koordinaten (Einstellungen),
  gespeichert und im Panel angezeigt (Label am Karten-Punkt).
- Firmware 0.6.2: `ORT <hex>` speichert den Ortsnamen im NVS; LCD zeigt ihn als
  dritte Wechselzeile. 111 PC-Tests bestanden.

## PC 0.6.5 / Firmware 0.6.1 / Dokumentation 0.34 - 22.09.2026

- LCD zeigt Datum und lokale Zeit (Zeile 1 `TT.MM.JJ HH:MM`); Zeile 2 wechselt
  alle 3 s zwischen Winkeln und Status/Aktion.
- Simulation laeuft immer: nach Sonnenuntergang automatisch mit dem
  Sonnenfenster des Folgetags (`aktuelles_sonnenfenster`). 108 PC-Tests bestehen.

## PC 0.6.4 / Dokumentation 0.33 - 21.09.2026

- Weltkarte interaktiv: Zoom per Mausrad (bis 16x, cursorzentriert), Karte
  verschieben per Ziehen, Doppelklick = Reset. Standort-Punkt per Drag & Drop
  verschiebbar; beim Loslassen Breite/Laenge speichern, Ausrichtung bestaetigen
  und (wenn verbunden) `CONF` an den ESP32 senden. 107 PC-Tests bestanden.

## PC 0.6.3 / Dokumentation 0.32 - 21.09.2026

- Weltkarte im PC-Bedienfeld: Panel-Standort als Punkt aus Breite/Laenge
  (equirectangular), offline. Kleine Karte rechts unten, grosse Karte auf der
  Simulationsseite. Neues Modul `weltkarte.py`; Bild `pc/weltkarte.png` (vom
  Nutzer bereitgestellte Plexus-Weltkarte). 105 PC-Tests bestanden.

## Firmware 0.6.0 / Dokumentation 0.31 - 21.09.2026

- Live-LCD-Anzeige im Normalbetrieb und autonomen Betrieb: Zeile 1 zeigt lokale
  Zeit und Status/Aktion, Zeile 2 Azimut und Panelneigung. Waehrend der Auto
  Kalibrierung bleibt der Schritt-Text; nach manuellem LCD-Text 30 s Pause.
- Protokoll 3, margin=114, Fahrlogik und Speicher unveraendert.

## PC 0.6.2 / Firmware 0.5.1 / Standalone 0.8 / Dokumentation 0.30 - 21.09.2026

- Alles laesst sich vom PC-Bedienfeld steuern: Direktbefehlsfeld, Konfiguration
  senden/anzeigen, Einzelachsen-Kalibrierung (`CAL AZ/EL`), zentrale
  Nachfuehrung (PC-Betrieb/Simulation oder Firmware-Autonomie) mit
  Sonnenziel-Anzeige.
- Firmware 0.5.1: Status meldet Konfiguration und Sonnenziel (`sun_az`/`sun_el`).
- Standalone-Firmware 0.8: serielle Menue-Fernbedienung (u/d/l/r/e/b).
- 102 PC-Tests bestanden; beide Firmwaren kompilieren. Protokoll 3, margin=114.

## Firmware 0.5.0 / Dokumentation 0.29 - 20.09.2026

- Autonomer Betrieb: Firmware fuehrt die Sonne ohne PC nach. Neues Modul
  `Sonne.h/.cpp` (NOAA und Zielabbildung, aus `pc/sonne.py`/`tageslauf.py`
  portiert; gegen die PC-Referenz geprueft, 0 Abweichungen).
- Konfiguration und Autonomie-Flag im ESP32-NVS; Befehle `CONF`, `AUTOON`,
  `AUTOOFF`; Status ergaenzt `auto_mode`/`conf_ok`. PC-Bedienfeld 0.6.1 sendet
  `CONF` und schaltet die Autonomie ueber Einstellungen.
- Automatik nur nach bestandenem Gesamttest, Referenz, Grenztests, gueltiger RTC
  und Konfiguration. Nachts Park an sicherer AZ-MIN/EL-MIN. Zeitzone automatisch
  MEZ/MESZ. STOP deaktiviert die Autonomie. Protokoll 3, margin=114 unveraendert.
- 102 PC-Tests bestanden; Firmware kompiliert (340340 Byte). Am Modell geprueft:
  `CONF` + `AUTOON`, beide Achsen fuhren zur Sonnenposition (AZ 114->297,
  EL 114->277); `AUTOOFF` beendete den Betrieb, Referenz/Grenztests blieben.

## Firmware 0.4.3 / Dokumentation 0.28 - 20.09.2026

- Am Modell: Firmware 0.4.1 hochgeladen und Auto Kalibrierung ausgefuehrt. Nach
  zwei Korrekturen lief der Gesamttest erstmals vollstaendig durch: auto_ok=true,
  beide Achsen an sicherer MIN (114), Spannen AZ=2202 / EL=1258.
- 0.4.2: Richtungs-Endschalter erst nach 30 ms stabilem Low auswerten
  (Entprellung.h, Compilezeit-Test); verhinderte vorzeitige MIN-/Grenztest-
  Abbrueche durch Prell-/Stoerimpulse.
- 0.4.3: Schritttakt von 3 ms auf 5 ms erhoeht; der belastete 28BYJ-48 verlor bei
  3 ms Schritte und driftete. Protokoll 3 und margin=114 unveraendert.

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

## ESP32-Dokumentation 0.11 – 2026-09-15

- PC-Firmware 0.1.0 auf COM3 erfolgreich hochgeladen, Flash-Pruefsumme verifiziert.
- HELLO/PING, Status und STOP-Quittung mit dem Python-Verbindungsmodul geprueft.
- Beide Achsen in Ruhe, unkalibriert und nicht referenziert; vier Kontakte offen.
- Keine Motorfahrt angefordert. Uploadstatus in den READMEs aktualisiert.

## ESP32-PC-Steuerung 0.1.0 / Dokumentation 0.10 – 2026-09-15

- Python-Bedienfeld unter `esp32SolarTracker/pc` mit serieller Steuerung,
  Tasten, Einstellungen, Kalibrierung, Sonnenfahrt, Simulation und Grafik erstellt.
- Passende Firmware unter `esp32SolarTracker/PCSteuerung`: gespeicherte Endlagen,
  10-Grad-Abstand und Verbindungsueberwachung. Keine automatische Motorfahrt.
- Python eingerichtet und Fenster gestartet; 17 Tests und ESP32-Build erfolgreich.
- Upload auf COM3 wegen Bootmodus 0x13 noch offen; keine Motorbewegung getestet.
- Anleitung und Pruefnachweise in den beiden neuen Ordnern dokumentiert.

Alle wichtigen Änderungen am Projekt werden in dieser Datei dokumentiert.

## ESP32-Dokumentationsversion 0.9 – 2026-09-14

- LCD-/Joystick-Menue 0.1 auf COM3 erfolgreich hochgeladen und verifiziert. Uploadstatus in der ESP32-Dokumentation aktualisiert.

## ESP32-Dokumentationsversion 0.8 / LCD-Joystick-Menue 0.1 – 2026-09-14

- `esp32SolarTracker/tests/LcdJoystickMenu` mit vollstaendigem Menuebaum und Joystick-Navigation erstellt und dokumentiert.
- Scrolltext, kurze/lange Tastendruecke und Compilezeit-Pruefungen fuer Navigation und Entprellung ergaenzt.
- Funktionsseiten als Menue-Vorschau ausgefuehrt; keine Motorfahrten oder Aenderungen am Hauptprogramm.

## ESP32-Dokumentationsversion 0.7 / Achsen-Testversion 0.2 – 2026-09-11

- Richtungspruefung im AchsenTest fuer die Diagnose fehlender Motorbewegung auf etwa sechs Sekunden verlangsamt.
- Schutzfunktionen beibehalten, Software-Selbsttest erweitert und Beobachtung des Benutzers dokumentiert.

## ESP32-Dokumentationsversion 0.6 – 2026-09-11

- Achsen-Test 0.1 auf COM3 erfolgreich hochgeladen und verifiziert.
- Statusabfrage bestaetigt bestandenen Software-Selbsttest und geoeffneten Preferences-Speicher. Hardware-Kalibrierung noch ausstehend; kein Fahrbefehl gesendet.
- ESP32-README und Testnachweis aktualisiert.

## ESP32-Dokumentationsversion 0.5 / Achsen-Testversion 0.1 – 2026-09-11

- ESP32-Build erfolgreich; Upload an COM3 mit `Wrong boot mode (0x13)` fehlgeschlagen. Hardwaretest noch nicht gestartet.

- `esp32SolarTracker/tests/AchsenTest` mit dauerhafter MIN/MAX-Kalibrierung beider Achsen und virtuellen Fahrgrenzen jeweils 10 Grad vor den Schaltern erstellt.
- Neustart mit geladener Kalibrierung und gesperrter Fahrt bis zur manuellen Positionsbestaetigung; Bedienung und Hardwaretest dokumentiert.
- Software-Selbsttest fuer Kalibrierung, Grenzen und Fehlerfaelle hinzugefuegt; Hauptprogramm unveraendert.

## ESP32-Dokumentationsversion 0.4 / Azimut-Testversion 0.1 – 2026-09-11

- Eigenstaendigen Azimut-Test mit beiden Endschaltern und 10 Grad Entlastungsfahrt in `esp32SolarTracker/tests/AzimutTest` erstellt und dokumentiert.
- Serielle Bedienung, Abschalten im Stillstand, Begrenzung der Fahrstrecke und Ablauf-Selbsttest hinzugefuegt.
- Fuer ESP32 erfolgreich kompiliert; mechanischer Test noch ausstehend.

## ESP32-Dokumentationsversion 0.3 – 2026-09-09

- Funktionierendes LCD nach Benutzer-Rueckmeldung dokumentiert.
- Genaue LCD-Testanleitung samt Code-Erklaerung unter `esp32SolarTracker/tests/LcdTest/README.md` gespeichert und beide ESP32-READMEs aktualisiert.
- Eigenes Aenderungsprotokoll unter `esp32SolarTracker/CHANGELOG.md` angelegt, damit der ESP32-Ordner die zugehoerige Dokumentation enthaelt.
- Gespeicherter LCD-Test bleibt Version 0.2. Build erfolgreich; letzter Upload durch den Assistenten mit `Wrong boot mode` fehlgeschlagen. Die auf dem Board funktionierende Version ist nicht eindeutig belegt.

## ESP32-LCD-Test Version 0.2 – 2026-09-09

- LCD-Test um I2C-Adresssuche und wiederkehrende Erreichbarkeitsmeldungen bei 115200 Baud erweitert.
- Vollstaendige Initialisierung mit `lcd.init()`, eingeschalteter Hintergrundbeleuchtung und Textanzeige ergaenzt.
- Upload von Version 0.1 auf COM3 erfolgreich verifiziert; laut Sichtpruefung Beleuchtung vorhanden, aber kein Text.
- Sichtbare Textausgabe von Version 0.2 noch zu bestaetigen.

## Version 0.7 – NOAA-Sonnenberechnung

Status: erstellt

Endschalter-Erweiterung:

- Neuer Azimut-Endschalter an Pin `13` ergänzt
- Wenn der Endschalter auslöst, gilt diese Position als feste Startposition der Azimutachse
- `Startpos fahren` fährt die Azimutachse jetzt bis zum Endschalter zurück, statt nur eine gespeicherte Grad-Differenz anzufahren
- Nach dem simulierten Sonnenuntergang fährt die Azimutachse ebenfalls zurück bis der Endschalter erneut auslöst
- Die Elevationsachse fährt dabei weiterhin auf die gespeicherte Start-Elevation zurück

Endschalter-Korrektur:

- Die Schalterlogik wurde auf `HIGH` als aktives Triggersignal korrigiert
- Wenn an Pin `13` `HIGH` anliegt, stoppt die Azimutachse jetzt sofort
- Diese getriggerte Position wird wieder als feste Startposition mit Azimut `90` und Elevation `0` gespeichert

Sicherheits-Korrektur fuer Fahrbereich:

- `LEFT` bedeutet Osten und damit Richtung Endschalter
- Wenn der Endschalter aktiv ist, wird jede weitere Fahrt nach `LEFT` sofort blockiert
- Ab der Startposition darf die Azimutachse nur noch nach `RIGHT` Richtung Westen fahren
- Die Simulation fährt zuerst sicher zurück auf die Startposition am Endschalter
- Die Simulation begrenzt Azimut jetzt nur noch auf den Bereich zwischen Startposition und Endposition
- Negative Azimut-Fahrten innerhalb der Simulation werden blockiert, damit keine Rückdrehung über die Startposition hinaus mehr möglich ist
- Die Elevationsrichtung wurde an die reale Mechanik angepasst: `UP` bewegt das Panel nach unten, `DOWN` bewegt das Panel nach oben

EEPROM- und Startpositions-Korrektur:

- Gespeicherte `Startposition` und `Endposition` werden jetzt beide vollständig aus dem EEPROM geladen
- Gespeicherte `Endposition` wird jetzt auch wieder vollständig in das EEPROM zurückgeschrieben
- Ursache des Fehlers war, dass `endAzimuth` und `endElevation` zwar in [`TrackerSettings`](SolarTracker/software/SolarTracker/SettingsStorage.h:32) vorhanden waren, aber in [`MenuSystem::loadSettingsFromStorage()`](SolarTracker/software/SolarTracker/Menu.cpp:672) und [`MenuSystem::saveSettingsToStorage()`](SolarTracker/software/SolarTracker/Menu.cpp:700) nicht verarbeitet wurden
- Beim Einschalten wird die aktuelle mechanische Ausgangslage jetzt bewusst als Startreferenz übernommen: Azimut `90` Grad nach Osten und Elevation `0` Grad waagerecht
- Diese Einschaltlogik entspricht der Projektvorgabe, dass das Panel vor dem Start immer manuell nach Osten und waagerecht ausgerichtet wird

Änderungen:

- `NOAA.h` erstellt
- `NOAA.cpp` erstellt
- Simulation verwendet jetzt Datum, Uhrzeit, Breitengrad und Längengrad
- Simulation berechnet realistischere Azimut- und Elevationswerte mit einer kompakten NOAA-Formel
- Simulierter Tag läuft von 06:00 bis 18:00 Uhr
- Sonnenstände unter dem Horizont werden auf Elevation 0 begrenzt
- Zielwerte werden zusätzlich durch gespeicherte Start- und Endposition begrenzt
- LCD-Anzeige zeigt weiterhin Azimut und Elevation

Simulation-Korrektur:

- Die Simulation sucht jetzt mit NOAA den echten Bereich zwischen Sonnenaufgang und Sonnenuntergang
- Diese gesamte Sonnenzeit wird auf 60 Sekunden beziehungsweise 30 Sekunden verteilt
- Azimut wird nur zwischen gespeicherter Startposition und gespeicherter Endposition gefahren
- Elevation kommt aus der NOAA-Berechnung und wird auf einen sicheren Bereich begrenzt

Einschränkungen:

- Zeitzone ist aktuell näherungsweise UTC+2
- Noch keine echte DS3231-Echtzeituhr

Standort-Update:

- Standard-Koordinaten auf Bad Vilbel, Hessen gesetzt
- Breitengrad: `+50.187`
- Laengengrad: `+8.739`
- EEPROM-Version auf `4` erhoeht, damit die neuen Standardwerte beim naechsten Start sicher neu geladen werden

## Version 0.6 – Software-Uhr mit millis()

Status: erstellt

Änderungen:

- `SoftwareClock.h` erstellt
- `SoftwareClock.cpp` erstellt
- einfache Uhr mit `millis()` ergänzt
- Uhr wird beim Start mit EEPROM-Werten initialisiert
- Uhr zählt Sekunden, Minuten, Stunden, Tage, Monate und Jahre weiter
- Menü übernimmt laufende Uhrzeit aus der Software-Uhr
- Datum- und Uhrzeit-Eingaben aktualisieren die Software-Uhr

Korrektur:

- Beim Einstellen von Datum oder Uhrzeit werden die Eingabewerte nicht mehr sofort von der laufenden Software-Uhr ueberschrieben
- Dadurch funktionieren UP/DOWN bei `Datum setzen` und `Uhrzeit setzen` wieder korrekt

Weitere Uhr-Korrektur:

- Beim Öffnen von `Datum setzen` und `Uhrzeit setzen` werden zuerst die aktuellen Werte der laufenden Software-Uhr übernommen
- Wenn die Software-Uhr Minute, Stunde oder Datum ändert, wird die LCD-Anzeige als aktualisierungsbedürftig markiert
- Dadurch bleibt die Anzeige nicht mehr dauerhaft auf dem alten EEPROM-Startwert stehen

Einschränkungen:

- Uhr läuft nur, solange der Arduino Strom hat
- Nach Ausschalten läuft die Zeit nicht weiter
- Für echte Echtzeit ist später DS3231 nötig

Simulation-Erweiterung:

- `Simulation Start` fährt zuerst die gespeicherte Startposition an
- Danach wird ein vereinfachter Sonnentag simuliert
- Geschwindigkeit 1 simuliert den ganzen Sonnentag in 60 Sekunden
- Geschwindigkeit 2 simuliert den ganzen Sonnentag in 30 Sekunden
- Während der Simulation zeigt das LCD oben Azimut und unten Elevation
- Die Motoren fahren schrittweise die berechneten Azimut-/Elevationswerte an

Simulation-Korrektur:

- Simulation startet jetzt exakt an der gespeicherten Startposition
- Simulation läuft nur einen Sonnentag
- Am simulierten Sonnenuntergang wird die Simulation beendet
- Danach fahren beide Achsen automatisch zurück zur gespeicherten Startposition
- Dadurch soll verhindert werden, dass sich Kabel durch endloses Weiterdrehen verwickeln

Weitere Simulation-Korrektur:

- Simulation startet jetzt fest bei Azimut 90 Grad und Elevation 0 Grad
- Simulation laeuft nur von Osten nach Westen: Azimut 90 Grad bis 270 Grad
- Elevation laeuft nur von 0 Grad auf 60 Grad und zurueck auf 0 Grad
- Es wird kein Nordbereich mehr simuliert
- Am Sonnenuntergang ist die Endposition erreicht, danach erfolgt die Rueckfahrt zur gespeicherten Startposition

Simulation-Schrittweite:

- Bei Geschwindigkeit 1 wird die gesamte Sonnenzeit auf 60 Sekunden mit 60 Schritten verteilt
- Bei Geschwindigkeit 2 wird die gesamte Sonnenzeit auf 30 Sekunden mit 30 Schritten verteilt

Kabelschutz-Erweiterung:

- Endposition kann jetzt wie die Startposition gespeichert werden
- Neuer Menuepunkt `Endpos speichern`
- Neuer Menuepunkt `Endpos fahren`
- Simulation laeuft nur von gespeicherter Startposition bis gespeicherter Endposition
- Danach faehrt das Panel zur Startposition zurueck
- Manuelle Bewegung wird auf den Bereich zwischen Startposition und Endposition begrenzt

## Version 0.5 – EEPROM-Speicherung

Status: erstellt

Änderungen:

- `SettingsStorage.h` erstellt
- `SettingsStorage.cpp` erstellt
- EEPROM-Datenstruktur mit Magic, Version und Prüfsumme erstellt
- Menüwerte werden beim Start aus EEPROM geladen
- Menüwerte werden beim Bestätigen gespeichert
- Startposition wird beim Speichern dauerhaft im EEPROM gesichert

Korrektur:

- `Startpos fahren` bewegt jetzt die Motoren physisch zur gespeicherten Startposition
- Bewegung erfolgt über die Differenz zwischen aktueller Position und gespeicherter Startposition
- Nach der Fahrt wird die aktuelle Position auf die gespeicherte Startposition gesetzt und gespeichert

Gespeicherte Werte:

- Azimut
- Elevation
- Startposition Azimut
- Startposition Elevation
- Datum
- Uhrzeit
- Breitengrad
- Längengrad
- Simulationsgeschwindigkeit

Einschränkungen:

- Noch keine Werkseinstellungen über Menü
- Noch keine Anzeige, ob EEPROM neu initialisiert wurde

## Version 0.4 – Manuelle Motorsteuerung

Status: erstellt

Änderungen:

- `Motor.h` erstellt
- `Motor.cpp` erstellt
- Motorsteuerung für zwei 28BYJ-48 mit ULN2003 ergänzt
- Azimutmotor über `Azimut setzen` manuell bewegbar
- Höhenmotor über `Elevation setzen` manuell bewegbar
- UP bewegt Achse positiv
- DOWN bewegt Achse negativ
- Azimut und Elevation wurden in einem Menüpunkt `Az/El manuell` zusammengeführt
- UP/DOWN steuert Elevation
- RIGHT/LEFT steuert Azimut
- Motoren werden nach jeder Bewegung ausgeschaltet
- `SolarTracker.ino` initialisiert das Motor-Modul

Korrektur:

- Manuelle Schrittweite von 6 auf 32 Halbschritte pro Joystick-Aktion erhöht
- Motorsteuerung merkt sich die aktuelle Schrittsequenz pro Achse
- Richtungswechsel funktioniert dadurch zuverlässiger in beide Richtungen

Einschränkungen:

- Noch keine automatische Positionsregelung
- Noch keine EEPROM-Speicherung
- Noch keine NOAA-Berechnung
- Noch keine Endschalter oder Referenzfahrt

## Version 0.3.1 – Vereinfachtes Menü mit analogem Joystick

Status: erstellt

Grund:

- Das Menü war zu umfangreich.
- Nicht alle Einstellungen waren übersichtlich erreichbar.
- Die Eingabe sollte zuerst nur für wenige wichtige Werte funktionieren.

Änderungen:

- Hauptmenü reduziert auf:
  - Normalbetrieb
  - Simulation
  - Einstellungen
- Nicht benötigte Menüs deaktiviert:
  - Motoren
  - Hardwaretest
  - Informationen
- Einstellungen reduziert auf:
  - Azimut setzen
  - Elevation setzen
  - Datum setzen
  - Uhrzeit setzen
  - Startposition manuell anfahren
  - Startposition speichern
- Menüanzeige vereinfacht:
  - Zeile 1 zeigt Bereich und Nummer
  - Zeile 2 zeigt den aktuellen Menüpunkt
- Eingabe vereinfacht:
  - UP erhöht den Wert
  - DOWN verringert den Wert
  - RIGHT öffnet Untermenüs und Funktionen
  - LEFT geht zurück in die übergeordnete Ebene
  - ENTER bestätigt Eingabefelder
- Joystick-Anschluss geändert:
  - VRx an A0
  - VRy an A1
  - SW an D12

Einschränkungen:

- Werte werden nur im RAM gespeichert.
- Noch keine EEPROM-Speicherung.
- Noch keine echte Motorbewegung.
- Noch keine NOAA-Berechnung.

Ergänzung:

- Einstellungen um Breitengrad ergänzt
- Einstellungen um Längengrad ergänzt
- Breiten- und Längengrad werden als Koordinaten mit Vorzeichen und 3 Nachkommastellen angezeigt, zum Beispiel `+52.517` oder `+13.395`
- Normalbetrieb erhält Untermenü mit `Betrieb starten` und `Status anzeigen`
- Simulation erhält Untermenü mit `Simulation Start` und `Geschwindigkeit`
- Simulationsgeschwindigkeit hat drei Stufen

## Version 0.3 – Eingaben über Joystick

Status: erstellt

Änderungen:

- Projektversion auf 0.3 erhöht
- Eingabemodus im Menüsystem ergänzt
- Datumseingabe ergänzt
- Uhrzeiteingabe ergänzt
- Standort-Eingabe für Breite und Länge ergänzt
- Schrittweite-Eingabe ergänzt
- LCD-Licht-Einstellung ergänzt
- ENTER speichert oder wechselt zum nächsten Eingabefeld
- ENTER lang bricht die Eingabe ab

Einschränkungen:

- Werte werden nur im RAM gespeichert
- noch keine EEPROM-Speicherung
- noch keine Motorbewegung
- noch keine RTC-Übernahme
- noch keine NOAA-Berechnung

Testziel:

- Benutzer kann Werte über UP und DOWN verändern
- ENTER springt zum nächsten Feld oder speichert
- ENTER lang bricht ab
- Menü bleibt stabil bedienbar

## Version 0.2 – LCD-Menüsystem mit Joystick-Navigation

Status: erstellt

Änderungen:

- Arduino-Projektordner unter `software/SolarTracker` erstellt
- `SolarTracker.ino` als Hauptprogramm erstellt
- `Config.h` mit Version, Pins, LCD-Konstanten und Menü-Konstanten erstellt
- `LCD_Menu.cpp` und `LCD_Menu.h` für 16x2-I2C-LCD mit `hd44780` erstellt
- `Joystick.cpp` und `Joystick.h` für UP, DOWN, ENTER und ENTER lang erstellt
- `Menu.cpp` und `Menu.h` mit Hauptmenü und Untermenüs erstellt
- Informationsseiten für Version, Hardware, LCD und Pins erstellt
- Platzhalterseiten für spätere Funktionen ergänzt

Einschränkungen:

- keine Motorbewegung
- keine EEPROM-Speicherung
- keine RTC-Funktion
- keine NOAA-Berechnung
- keine automatische Nachführung

Testziel:

- LCD zeigt Startbildschirm und Menü an
- UP/DOWN wechseln Menüpunkte
- ENTER öffnet Menü oder Informationsseite
- ENTER lang kehrt zurück ins Hauptmenü

## Version 0.1 – Projektgrundlage und Menüplanung

Geplanter Inhalt:

- Projektstruktur anlegen
- README anlegen
- Changelog anlegen
- Pinbelegung dokumentieren
- funktionierende Hardwaretests sichern
- Entwicklungsregeln festlegen
- komplettes LCD-Menüsystem planen

Aktueller Stand:

- ✔ Projektziel definiert
- ✔ Hardwarestand übernommen
- ✔ Mechanikstand übernommen
- ✔ bisher funktionierende Ergebnisse übernommen
- ✔ Grundstruktur für Dokumentation begonnen
- ✔ Menü-Hauptstruktur festgelegt

## Geplante Versionen

### Version 0.2 – Menüsystem

- LCD-Menüstruktur programmieren
- Joystick-Navigation integrieren
- Menüzustände sauber verwalten
- noch keine vollständige Motor- oder NOAA-Logik

### Version 0.3 – Einstellungen und EEPROM

- Einstellungen speichern
- Einstellungen laden
- Startposition speichern
- Systemwerte sichern

### Version 0.4 – Motorsteuerung

- Azimutmotor steuern
- Höhenmotor steuern
- manuelles Fahren
- Rückfahrt zur Startposition
- Motoren nach Bewegung abschalten

### Version 0.5 – NOAA-Berechnung

- Sonnenposition berechnen
- Azimut berechnen
- Elevation berechnen
- Standortdaten verwenden
- Datum und Uhrzeit verwenden

### Version 0.6 – Normalbetrieb

- Sonnenposition automatisch verfolgen
- Sonnenuntergang erkennen
- automatische Rückfahrt zur Startposition

### Version 0.7 – Simulation

- Simulationsdatum einstellen
- Simulationszeit einstellen
- Zeitrafferbetrieb
- Bewegung ohne echte Tageszeit testen

### Version 0.8 – Leistungsmessung

- Spannung messen
- Strom messen
- Leistung berechnen
- Messwerte anzeigen

### Version 0.9 – Optimierung und Fehlersuche

- Fehlerzustände verbessern
- Bedienung prüfen
- Grenzwerte prüfen
- Dokumentation vervollständigen

### Version 1.0 – Fertige Unterrichts- und Projektversion

- vollständiger Solartracker
- vollständige Dokumentation
- vollständiges Unterrichtsmaterial
- stabiler Projektstand

