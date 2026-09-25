// Version 0.7.0. Eingabe: zeilenweise PC-Befehle. Ausgabe: JSON-Zeilen.
// Beispiel: 1 HELLO 3\n, 2 PING\n, 3 STATUS\n. Protokoll siehe README.
#include "Steuerung.h"
#include <Arduino.h>
#include <Preferences.h>
#include <Wire.h>
#include <RTClib.h>
#include "Pruefung.h"
#include "PositionsDaten.h"
#include "Gegenkontakt.h"
#include "Entprellung.h"
#include "Sonne.h"
#include "LcdSteuerung.h"
#include "LcdText.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

namespace {
constexpr int UMDREHUNG = 4096;
constexpr int ABSTAND = 114; // Aufgerundet: mindestens 10 Grad bei 4096 Schritten.
constexpr unsigned long TAKT = 5, WATCHDOG = 2000, ENTPRELL = 30;
const uint8_t FOLGE[8][4] = {{1,0,0,0},{1,1,0,0},{0,1,0,0},{0,1,1,0},
                            {0,0,1,0},{0,0,1,1},{0,0,0,1},{1,0,0,1}};
enum Zustand { RUHE, FAHRT, SUCH_MIN, FREI_MIN, SUCH_MAX, FREI_MAX, TIPP, ENTLASTUNG, TEST_MIN, TEST_MAX, TEST_ZURUECK };
struct Achse {
  uint8_t pins[4], minPin, maxPin;
  const char* schluessel;
  int position = 0, spanne = 0, ziel = 0, phase = 0, schritte = 0;
  Zustand zustand = RUHE;
  bool referenz = false;
  bool nurReferenz = false;
  int richtung = 1;
  Gegenkontakt gegenkontakt;
  Entprellung entMin, entMax;
  bool grenzenOK = false;
  unsigned long takt = 0;
  uint32_t generation = 0;
  PositionsDaten letzterStand;
  bool standVorhanden = false;
};
Achse achsen[2] = {{{16,17,18,19},4,5,"az"}, {{25,26,27,14},15,12,"el"}};
Preferences speicher;
bool speicherOK = false, verbunden = false;
SchalterPruefung schalterTest;
uint8_t autoPhase=0;
bool autoOK=false;
unsigned long autoZeit=0;
uint32_t autoRtc=0;
const char* autoMeldung="Nicht gestartet";
bool autoAnzeige(const char* oben,const char* unten);
void autoAbbruch(const char* meldung);
// Autonomer Betrieb: Konfiguration im NVS, Ziel einmal pro Minute neu berechnet.
bool autoModus=false, confOK=false;
float confBreite=0, confLaenge=0, confAzNull=90, confElNeigung=90;
unsigned long zielZeit=0;
int zielAz=-1, zielEl=-1;
char ortText[17]="";
int tzMinuten=0;
bool tzGesetzt=false;
void autonomAktualisieren();
RTC_DS3231 rtc;
bool rtcVorhanden = false, rtcGueltig = false;
uint32_t rtcSekunden = 0;
unsigned long rtcZeit = 0;
int zeitversatz() { return tzGesetzt ? tzMinuten : tagesversatz(rtcSekunden) * 60; }
unsigned long ping = 0, statusZeit = 0, lcdZeit = 0, lcdManuellBis = 0;
char zeile[100];
size_t laenge = 0;
bool ueberlauf = false;
bool kontakt(uint8_t pin) { return digitalRead(pin) == LOW; }
// Richtungs-Endschalter erst nach stabiler Low-Dauer als gedrueckt werten.
void kontakteEntprellen(Achse& a) {
  unsigned long jetzt = millis();
  a.entMin.aktualisieren(kontakt(a.minPin), jetzt, ENTPRELL);
  a.entMax.aktualisieren(kontakt(a.maxPin), jetzt, ENTPRELL);
}
bool minAktiv(const Achse& a) { return a.entMin.stabil; }
bool maxAktiv(const Achse& a) { return a.entMax.stabil; }
bool aktiv() { return achsen[0].zustand != RUHE || achsen[1].zustand != RUHE; }
void aus(Achse& a) { for (auto pin : a.pins) digitalWrite(pin, LOW); }
bool sichern(Achse& a,bool bewegt=false) {
  if (!speicherOK) return false;
  auto d=positionsDaten(a.spanne,a.position,a.phase,a.referenz,a.grenzenOK,bewegt,a.generation);
  if (a.standVorhanden && memcmp(&a.letzterStand,&d,sizeof(d))==0) return true;
  const char* key=(&a==&achsen[0])?"az_state":"el_state";
  if (speicher.putBytes(key,&d,sizeof(d))!=sizeof(d)) {
    speicherOK=false;
    Serial.println("{\"type\":\"fault\",\"message\":\"Position konnte nicht dauerhaft gespeichert werden\"}");
    return false;
  }
  a.letzterStand=d; a.standVorhanden=true; return true;
}
void halt(Achse& a) {
  // Schrittposition ist auch beim normalen STOP exakt im Zaehler bekannt.
  a.zustand=RUHE; a.nurReferenz=false; aus(a);
}
bool alleHalt() {
  if (autoPhase) autoAbbruch("Abgebrochen");
  for (auto& a:achsen) halt(a);
  if (schalterTest.aktiv) schalterTest.wiederherstellen(achsen[0].spanne>0,achsen[1].spanne>0);
  bool ok=true;
  for (auto& a:achsen) if (!sichern(a)) ok=false;
  return ok;
}
bool freigegeben() {
  if (!speicherOK || !schalterTest.ok()) return false;
  for (auto& a : achsen) if (!a.referenz || !a.spanne || !a.grenzenOK || minAktiv(a) || maxAktiv(a)) return false;
  return true;
}
void rtcLesen() {
  Wire.beginTransmission(0x68);
  rtcVorhanden = Wire.endTransmission() == 0;
  rtcGueltig = rtcVorhanden && !rtc.lostPower();
  if (rtcGueltig) {
    DateTime jetzt = rtc.now();
    rtcGueltig = jetzt.isValid();
    if (rtcGueltig) rtcSekunden = jetzt.unixtime();
  }
  rtcZeit = millis();
}
void fehler(Achse& a, const char* meldung) {
  if (autoPhase) autoAbbruch(meldung);
  int phase = int(a.zustand);
  a.referenz = false; a.grenzenOK = false;
  halt(a); sichern(a);
  if (schalterTest.aktiv) schalterTest.loeschen();
  Serial.printf("{\"type\":\"fault\",\"axis\":\"%s\",\"phase\":%d,\"direction\":%d,\"steps\":%d,\"position\":%d,\"min\":%s,\"max\":%s,\"message\":\"%s\"}\n",
    a.schluessel, phase, a.richtung, a.schritte, a.position,
    minAktiv(a) ? "true" : "false", maxAktiv(a) ? "true" : "false", meldung);
}
void status() {
  char conf[96] = "";
  if (confOK) snprintf(conf, sizeof(conf), ",\"lat\":%.3f,\"lon\":%.3f,\"az_null\":%.2f,\"el_neigung\":%.2f", confBreite, confLaenge, confAzNull, confElNeigung);
  int sunAz = -1, sunEl = -1;
  if (confOK && rtcGueltig && achsen[0].referenz && achsen[0].grenzenOK && achsen[1].referenz && achsen[1].grenzenOK) {
    Sonnenwerte w = sonnenstand(rtcSekunden, zeitversatz(), confBreite, confLaenge);
    if (w.hoehe <= 0) { sunAz = ABSTAND; sunEl = ABSTAND; }
    else { sunAz = zielAzimut(w, confAzNull, achsen[0].spanne, ABSTAND); sunEl = zielElevation(w.hoehe, confElNeigung, achsen[1].spanne, ABSTAND); }
  }
  Serial.printf("{\"type\":\"status\",\"protocol\":3,\"version\":\"0.7.0\",\"switch_test\":%d,\"switch_testing\":%s,\"rtc_present\":%s,\"rtc_valid\":%s,\"rtc_epoch\":%lu,\"axes\":[",
    schalterTest.index, schalterTest.aktiv ? "true" : "false", rtcVorhanden ? "true" : "false", rtcGueltig ? "true" : "false", (unsigned long)(rtcGueltig ? rtcSekunden + (millis()-rtcZeit)/1000 : 0));
  for (int i = 0; i < 2; ++i) {
    auto& a = achsen[i];
    Serial.printf("%s{\"position\":%d,\"span\":%d,\"margin\":114,\"calibrated\":%s,\"referenced\":%s,\"state\":%d,\"min\":%s,\"max\":%s,\"limits_ok\":%s,\"calibration_id\":%lu}",
      i ? "," : "", a.position, a.spanne, a.spanne > 0 ? "true" : "false",
      a.referenz ? "true" : "false", int(a.zustand), minAktiv(a) ? "true" : "false", maxAktiv(a) ? "true" : "false", a.grenzenOK ? "true" : "false", (unsigned long)a.generation);
  }
  Serial.printf("],\"auto_supported\":true,\"auto_testing\":%s,\"auto_ok\":%s,\"auto_message\":\"%s\",\"auto_mode\":%s,\"conf_ok\":%s%s,\"sun_az\":%d,\"sun_el\":%d,\"device_id\":\"%012llx\",\"position_storage\":true,\"storage_ok\":%s,\"lcd_supported\":true,\"lcd_present\":%s,\"ort_supported\":true,\"tz_supported\":true,\"tz_minuten\":%d}\n", autoPhase ? "true" : "false", autoOK && freigegeben() ? "true" : "false", autoMeldung, autoModus ? "true" : "false", confOK ? "true" : "false", conf, sunAz, sunEl, (unsigned long long)ESP.getEfuseMac(), speicherOK ? "true" : "false", lcdErreichbar() ? "true" : "false", int(tzMinuten));
}
// Live-Anzeige: Zeit + Status/Aktion (Zeile 1), Azimut + Panelneigung (Zeile 2).
const char* kurzStatus(const Achse& a) {
  switch (a.zustand) {
    case FAHRT: return "Fahrt";
    case SUCH_MIN: return "SuMIN";
    case FREI_MIN: return "FMIN";
    case SUCH_MAX: return "SuMAX";
    case FREI_MAX: return "FMAX";
    case TIPP: return "Tipp";
    case ENTLASTUNG: return "Entl";
    case TEST_MIN: return "TMin";
    case TEST_MAX: return "TMax";
    case TEST_ZURUECK: return "TZur";
    default: break;
  }
  return autoModus ? "Autonom" : (verbunden ? "PC" : "Bereit");
}
void lcdStatus() {
  if (autoPhase || millis() < lcdManuellBis) return;
  static uint8_t wechsel = 0;
  ++wechsel;
  char oben[17], unten[17];
  if (rtcGueltig) {
    Kalender k = kalenderZeit(rtcSekunden, zeitversatz());
    snprintf(oben, sizeof(oben), "%02d.%02d.%02d %02d:%02d", k.tag, k.monat, k.jahr % 100, k.stunde, k.minute);
  } else {
    snprintf(oben, sizeof(oben), "--.--.-- --:--");
  }
  bool faehrt = achsen[0].zustand != RUHE || achsen[1].zustand != RUHE;
  if (faehrt) {
    snprintf(unten, sizeof(unten), "%s", kurzStatus(achsen[0].zustand != RUHE ? achsen[0] : achsen[1]));
  } else {
    uint8_t schirm = (wechsel / 3) % 3;
    if (schirm == 0 && achsen[0].referenz && achsen[1].referenz && confOK) {
      int az = lroundf(confAzNull + (achsen[0].position - ABSTAND) * 360.0f / 4096.0f);
      az = ((az % 360) + 360) % 360;
      int ng = lroundf(confElNeigung - (achsen[1].position - ABSTAND) * 360.0f / 4096.0f);
      ng = ng < 0 ? 0 : (ng > 90 ? 90 : ng);
      snprintf(unten, sizeof(unten), "Az%3d Ng%2d", az, ng);
    } else if (schirm == 2 && ortText[0]) {
      snprintf(unten, sizeof(unten), "%s", ortText);
    } else {
      snprintf(unten, sizeof(unten), "%s", autoModus ? "Autonom" : (verbunden ? "PC-Bereit" : "Bereit"));
    }
  }
  char hex[2][33];
  const char* texte[] = {oben, unten};
  for (int z = 0; z < 2; ++z) {
    size_t len = strlen(texte[z]);
    for (int i = 0; i < 16; ++i) sprintf(hex[z] + 2 * i, "%02x", i < int(len) ? uint8_t(texte[z][i]) : 32);
  }
  lcdTextSenden(hex[0], hex[1]);
}
bool starten(Achse& a, Zustand zustand, int ziel) {
  // Vor dem ersten Schritt atomar markieren: nach Stromverlust kein alter Istwert.
  if (!sichern(a,true)) { fehler(a,"Fahrt gesperrt: Positionsspeicher nicht bereit"); return false; }
  if (autoPhase) {
    const char* text=zustand==SUCH_MIN?"MIN suchen":zustand==FREI_MIN?"MIN frei 10 Grad":zustand==SUCH_MAX?"MAX suchen":zustand==FREI_MAX?"MAX frei 10 Grad":zustand==TEST_MIN?"Startpos testen":zustand==TEST_MAX?"Stoppos testen":"Startpos fahren";
    if (!autoAnzeige(&a==&achsen[0]?"Azimut":"Elevation",text)) return false;
  }
  a.zustand = zustand; a.ziel = ziel; a.schritte = 0; a.takt = millis();
  a.richtung = ziel > a.position ? 1 : -1;
  bool entlastung = zustand == FREI_MIN || zustand == FREI_MAX || zustand == ENTLASTUNG;
  // Der gerade ausgeloeste Schalter ist bekannt, auch wenn der naechste Read prellt.
  a.gegenkontakt.starten(entlastung || (a.richtung > 0 ? minAktiv(a) : maxAktiv(a)));
  return true;
}
bool kalibrierungStarten(Achse& a) {
  if (!speicherOK) { fehler(a, "Speicher nicht bereit"); return false; }
  if (minAktiv(a) && maxAktiv(a)) { fehler(a, "Beide Endschalter aktiv"); return false; }
  // Alten Datensatz erst unmittelbar vor der Kalibrierung dieser Achse ersetzen.
  if (speicher.putInt(a.schluessel, 0) != sizeof(int)) { fehler(a, "Speichern fehlgeschlagen"); return false; }
  autoOK=false;
  if (!speicher.putBool("auto_ok",false)) { fehler(a,"Speicherfehler"); return false; }
  a.nurReferenz=false;
  ++a.generation;
  a.spanne = 0; a.referenz = false; a.position = 0; a.grenzenOK = false;
  // Ein anfangs aktiver MAX darf in MIN-Richtung verlassen werden; klemmt er,
  // stoppt die bestehende Gegenkontaktpruefung nach hoechstens 114 Schritten.
  return starten(a, SUCH_MIN, -UMDREHUNG);
}
void schritt(Achse& a, int richtung) {
  a.phase = (a.phase + richtung + 8) % 8;
  for (int i = 0; i < 4; ++i) digitalWrite(a.pins[i], FOLGE[a.phase][i]);
  a.position += richtung; ++a.schritte;
}
void aktualisieren(Achse& a) {
  if (a.zustand == RUHE) return;
  bool unten = minAktiv(a), oben = maxAktiv(a);
  if (unten && oben) { fehler(a, "Beide Endschalter aktiv"); return; }
  if (a.zustand == SUCH_MIN && unten) {
    aus(a); a.position = 0; starten(a, FREI_MIN, ABSTAND); a.takt = millis() + 100; return;
  }
  if (a.zustand == SUCH_MAX && oben) {
    aus(a);
    if (a.position <= 2 * ABSTAND || a.position > UMDREHUNG) { fehler(a, "Kalibrierweg ungueltig"); return; }
    starten(a, FREI_MAX, a.position - ABSTAND); a.takt = millis() + 100; return;
  }
  int richtung = a.richtung;
  if (a.position != a.ziel && (richtung > 0 ? oben : unten)) {
    if (a.zustand == FAHRT || a.zustand == TIPP || a.zustand >= TEST_MIN) {
      aus(a); a.referenz = false; a.grenzenOK = false;
      Serial.println("{\"type\":\"event\",\"message\":\"Endschalter: 10 Grad entlasten, danach neu referenzieren\"}");
      starten(a, ENTLASTUNG, a.position - richtung * ABSTAND); a.takt = millis() + 100;
    } else fehler(a, "Unerwarteter Endschalter");
    return;
  }
  bool gegenkontakt = richtung > 0 ? unten : oben;
  KontaktFehler kontaktFehler = a.gegenkontakt.pruefen(gegenkontakt, a.schritte, millis(), ABSTAND);
  if (kontaktFehler == KontaktFehler::UNERWARTET) { fehler(a, "Gegenkontakt unerwartet geschlossen (Richtung/Belegung pruefen)"); return; }
  if (kontaktFehler == KontaktFehler::KLEMMT && a.position != a.ziel) { fehler(a, "Gegenkontakt nach 10 Grad noch geschlossen"); return; }
  if (a.position == a.ziel) {
    // Mechanische Kontakte nach Ende der Entlastung kurz beruhigen lassen.
    if (int32_t(millis() - a.takt) < 25) return;
    aus(a);
    if (a.zustand >= TEST_MIN) {
      if (unten || oben) { fehler(a, "Grenztest: Schalter beruehrt"); return; }
      if (a.zustand == TEST_MIN) { starten(a, TEST_MAX, a.spanne - ABSTAND); return; }
      if (a.zustand == TEST_MAX) { starten(a, TEST_ZURUECK, ABSTAND); return; }
      a.grenzenOK = true;
    }
    if (a.zustand == FREI_MIN || a.zustand == FREI_MAX || a.zustand == ENTLASTUNG || a.zustand == TIPP) {
      // Am Ende nur warten, niemals ueber die 10-Grad-Entlastung hinausfahren.
      if (unten || oben || !a.gegenkontakt.stabilOffen(millis())) {
        if (int32_t(millis() - a.takt) < 100) return;
        fehler(a, "Endschalter nach Entlastung nicht stabil offen"); return;
      }
    }
    if (a.zustand == FREI_MIN) {
      if (a.nurReferenz) {
        a.nurReferenz=false; a.referenz=true; a.zustand=RUHE;
        if (!sichern(a)) fehler(a,"Referenz nicht gespeichert");
        status(); return;
      }
      if (schalterTest.aktiv && !schalterTest.minEntlastet(&a == &achsen[0] ? 0 : 1)) { fehler(a, "Pruefreihenfolge ungueltig"); return; }
      starten(a, SUCH_MAX, UMDREHUNG + 1); return;
    }
    if (a.zustand == FREI_MAX) {
      int spanne = a.position + ABSTAND;
      if (!speicherOK || speicher.putInt(a.schluessel, spanne) != sizeof(int)) { fehler(a, "Speichern fehlgeschlagen"); return; }
      a.spanne = spanne; a.referenz = true;
      if (schalterTest.aktiv) {
        uint8_t achse = &a == &achsen[0] ? 0 : 1;
        if (!schalterTest.maxGespeichert(achse)) { fehler(a, "Pruefreihenfolge ungueltig"); return; }
        a.zustand = RUHE;
        if (!sichern(a)) { fehler(a,"Kalibrierposition nicht gespeichert"); return; }
        if (achse == 0 && achsen[1].spanne>0) {
          schalterTest.wiederherstellen(true,true);
        } else if (achse == 0) {
          // Zweite Achse beginnt erst nach gespeichertem, entlastetem AZ-MAX.
          kalibrierungStarten(achsen[1]);
          // Kurze Pause beim Achsenwechsel; keine weitere User-Eingabe noetig.
          if (achsen[1].zustand != RUHE) achsen[1].takt = millis() + 500;
        }
        status(); return;
      }
    } else if (a.zustand == SUCH_MIN || a.zustand == SUCH_MAX) { fehler(a, "Endschalter im Suchweg nicht gefunden"); return; }
    a.zustand = RUHE;
    if (!sichern(a)) fehler(a,"Endposition nicht gespeichert");
    status(); return;
  }
  if (int32_t(millis() - a.takt) < int32_t(TAKT)) return;
  a.takt = millis();
  schritt(a, richtung);
}
// Gesamttest: Fortschritt nur nach abgeschlossener Fahrt, nie nach ACK allein.
bool autoAnzeige(const char* oben,const char* unten) {
  char hex[2][33]; const char* texte[]={oben,unten};
  for (int z=0;z<2;++z) {
    size_t len=strlen(texte[z]);
    for (int i=0;i<16;++i) sprintf(hex[z]+2*i,"%02x",i<int(len)?uint8_t(texte[z][i]):32);
  }
  if (lcdTextSenden(hex[0],hex[1])) {
    autoAbbruch("LCD nicht bereit"); return false;
  }
  autoMeldung=unten;
  return true;
}
void autoAbbruch(const char* meldung) {
  autoPhase=0; autoOK=false; autoMeldung=meldung;
  for (auto& a:achsen) { halt(a); sichern(a); }
  speicher.putBool("auto_ok",false);
  // LCD-Fehler niemals rekursiv erneut anzeigen.
  char hex[2][33]; const char* texte[]={"Test FEHLER",meldung};
  for (int z=0;z<2;++z) {
    size_t len=strlen(texte[z]);
    for (int i=0;i<16;++i) sprintf(hex[z]+2*i,"%02x",i<int(len)?uint8_t(texte[z][i]):32);
  }
  lcdTextSenden(hex[0],hex[1]);
  Serial.printf("{\"type\":\"fault\",\"message\":\"Auto Kalibrierung: %s\"}\n",meldung);
}
void autoWeiter() {
  if (!autoPhase || aktiv()) return;
  if (autoPhase==1) {
    if (millis()-autoZeit<1500) return;
    rtcLesen();
    if (!rtcGueltig) { autoAbbruch("RTC ungueltig"); return; }
    autoRtc=rtcSekunden; autoZeit=millis(); autoPhase=2;
    autoAnzeige("LCD Test OK","RTC wird getestet"); return;
  }
  if (autoPhase==2) {
    if (millis()-autoZeit<2100) return;
    rtcLesen();
    if (!rtcGueltig || rtcSekunden<=autoRtc || rtcSekunden-autoRtc>4) { autoAbbruch("RTC laeuft nicht"); return; }
    autoPhase=7; autoZeit=millis();
    autoAnzeige("RTC Test OK","Zeit laeuft"); return;
  }
  if (autoPhase==7) {
    if (millis()-autoZeit<1500) return;
    autoPhase=3;
    kalibrierungStarten(achsen[0]); return;
  }
  if (autoPhase==3) {
    if (!achsen[0].referenz) { autoAbbruch("Azimut fehlt"); return; }
    autoPhase=4; kalibrierungStarten(achsen[1]); return;
  }
  if (autoPhase==4) {
    if (!achsen[1].referenz) { autoAbbruch("Elevation fehlt"); return; }
    schalterTest.wiederherstellen(true,true);
    autoPhase=5; starten(achsen[0],TEST_MIN,ABSTAND); return;
  }
  if (autoPhase==5) {
    if (!achsen[0].grenzenOK) { autoAbbruch("AZ Grenztest"); return; }
    autoPhase=6; starten(achsen[1],TEST_MIN,ABSTAND); return;
  }
  if (autoPhase==6) {
    rtcLesen();
    if (!rtcGueltig) { autoAbbruch("RTC ungueltig"); return; }
    if (!freigegeben() || achsen[0].position!=ABSTAND || achsen[1].position!=ABSTAND) { autoAbbruch("Startpos fehlt"); return; }
    if (!autoAnzeige("Alle Tests OK","Normalbetr.bereit")) return;
    if (!speicher.putBool("auto_ok",true)) { autoAbbruch("Speicherfehler"); return; }
    autoOK=true; autoPhase=0; autoMeldung="Alle Tests OK - Startposition erreicht";
    status();
  }
}
// Sonnenziel aus RTC und Konfiguration; unter dem Horizont an sichere MIN parken.
void autonomesZiel() {
  if (!rtcGueltig || !confOK) return;
  Sonnenwerte w = sonnenstand(rtcSekunden, zeitversatz(), confBreite, confLaenge);
  if (w.hoehe <= 0) { zielAz = ABSTAND; zielEl = ABSTAND; }
  else {
    zielAz = zielAzimut(w, confAzNull, achsen[0].spanne, ABSTAND);
    zielEl = zielElevation(w.hoehe, confElNeigung, achsen[1].spanne, ABSTAND);
  }
}
void autonomAktualisieren() {
  if (!autoModus || autoPhase || schalterTest.aktiv) return;
  if (!autoOK || !confOK || !rtcGueltig || !freigegeben()) return;
  if (millis() - zielZeit >= 60000) { zielZeit = millis(); autonomesZiel(); }
  if (aktiv() || zielAz < 0 || zielEl < 0) return;
  if (abs(zielAz - achsen[0].position) > 2) { starten(achsen[0], FAHRT, zielAz); return; }
  if (abs(zielEl - achsen[1].position) > 2) starten(achsen[1], FAHRT, zielEl);
}
bool zahl(const char* text, double& wert) {
  if (!text) return false;
  char* ende; wert = strtod(text, &ende);
  return *text && !*ende && isfinite(wert);
}
void antwort(long id, const char* fehlertext = nullptr) {
  Serial.printf("{\"type\":\"ack\",\"id\":%ld,\"ok\":%s,\"message\":\"%s\"}\n", id, fehlertext ? "false" : "true", fehlertext ? fehlertext : "OK");
}
void befehl() {
  char* rest;
  char* idText = strtok_r(zeile, " \r", &rest);
  char* cmd = strtok_r(nullptr, " \r", &rest);
  double idWert;
  if (!zahl(idText, idWert) || idWert < 1 || idWert > 1000000000 || floor(idWert) != idWert || !cmd) { antwort(0, "Syntax"); return; }
  long id = long(idWert);
  if (!strcmp(cmd, "STOP")) {
    if (speicherOK) speicher.putBool("auto_mode",false);
    autoModus=false;
    bool ok=alleHalt(); antwort(id,ok?nullptr:"STOP ausgefuehrt, Speichern fehlgeschlagen"); status(); return;
  }
  if (!strcmp(cmd, "CONF")) {
    if (!verbunden) { antwort(id, "Zuerst HELLO"); return; }
    if (autoPhase || aktiv()) { antwort(id, "Befehl waehrend Fahrt gesperrt"); return; }
    double w[4]; int n=0; char* r2; char* tok=strtok_r(rest, " \r", &r2);
    while (tok && n<4 && zahl(tok, w[n])) { ++n; tok=strtok_r(nullptr, " \r", &r2); }
    if (n!=4 || tok) { antwort(id, "CONF: Breite Laenge AzNull ElNeigung"); return; }
    if (w[0]<-90||w[0]>90||w[1]<-180||w[1]>180||w[2]<0||w[2]>360||w[3]<0||w[3]>180) { antwort(id, "CONF: Wert ausserhalb"); return; }
    if (!speicherOK) { antwort(id, "Speicher nicht bereit"); return; }
    speicher.putInt("lat", lround(w[0]*1000));
    speicher.putInt("lon", lround(w[1]*1000));
    speicher.putInt("aznull", lround(w[2]*100));
    speicher.putInt("elneig", lround(w[3]*100));
    confBreite=w[0]; confLaenge=w[1]; confAzNull=w[2]; confElNeigung=w[3]; confOK=true;
    antwort(id); status(); return;
  }
  char* arg1 = strtok_r(nullptr, " \r", &rest);
  char* arg2 = strtok_r(nullptr, " \r", &rest);
  char* extra = strtok_r(nullptr, " \r", &rest);
  if (extra) { antwort(id, "Zu viele Argumente"); return; }
  if (!strcmp(cmd, "HELLO")) {
    alleHalt(); verbunden = false;
    if (!arg1 || strcmp(arg1, "3") || arg2) { antwort(id, "Protokoll 3 erforderlich: HELLO 3"); return; }
    schalterTest.wiederherstellen(achsen[0].spanne > 0, achsen[1].spanne > 0);
    verbunden = true; ping = millis(); antwort(id); status(); return;
  }
  if (!strcmp(cmd, "STATUS") && !arg1) { antwort(id); status(); return; }
  if (!verbunden) { antwort(id, "Zuerst HELLO"); return; }
  if (!strcmp(cmd, "PING") && !arg1) { ping = millis(); antwort(id); return; }
  if (millis() - ping > WATCHDOG) { alleHalt(); verbunden = false; antwort(id, "Verbindung abgelaufen"); return; }
  if (autoPhase) { antwort(id,"Auto Kalibrierung laeuft: STOP zum Abbrechen"); return; }
  if (aktiv()) { antwort(id, "Achse bewegt sich noch"); return; }
  if (!strcmp(cmd,"AUTOON") && !arg1) {
    if (!confOK) { antwort(id,"Zuerst CONF setzen"); return; }
    if (!autoOK || !freigegeben()) { antwort(id,"Autonomie gesperrt: Gesamttest/Referenz fehlen"); return; }
    if (!speicherOK || !speicher.putBool("auto_mode",true)) { antwort(id,"Speichern fehlgeschlagen"); return; }
    autoModus=true; zielZeit=0;
    antwort(id); status(); return;
  }
  if (!strcmp(cmd,"AUTOOFF") && !arg1) {
    if (speicherOK) speicher.putBool("auto_mode",false);
    autoModus=false; alleHalt();
    antwort(id); status(); return;
  }
  if (!strcmp(cmd,"AUTOCAL") && !arg1) {
    if (!speicherOK) { antwort(id,"Speicher nicht bereit"); return; }
    for (auto& a:achsen) if (minAktiv(a) && maxAktiv(a)) { antwort(id,"Beide Endschalter aktiv"); return; }
    autoOK=false;
    if (!speicher.putBool("auto_ok",false)) { antwort(id,"Speichern fehlgeschlagen"); return; }
    schalterTest.wiederherstellen(achsen[0].spanne>0,achsen[1].spanne>0);
    autoPhase=1; autoZeit=millis();
    bool ok=autoAnzeige("LCD Test 12345678","Auto Kalibrierung");
    antwort(id,ok?nullptr:"LCD-Test fehlgeschlagen"); status(); return;
  }
  if (!strcmp(cmd, "LCD")) {
    const char* fehlertext = lcdTextSenden(arg1,arg2);
    if (!fehlertext) lcdManuellBis = millis() + 30000;  // 30 s eigene Anzeige vor Live-Status
    antwort(id,fehlertext); status(); return;
  }
  if (!strcmp(cmd, "ORT") && arg1 && !arg2) {
    if (!lcdZeileGueltig(arg1)) { antwort(id, "ORT: 16 Hex-Zeichen erwartet"); return; }
    for (int i = 0; i < 16; ++i) ortText[i] = char(hexZiffer(arg1[2*i]) * 16 + hexZiffer(arg1[2*i+1]));
    ortText[16] = 0;
    if (speicherOK) speicher.putString("ort", ortText);
    antwort(id); status(); return;
  }
  if (!strcmp(cmd, "TZ") && arg1 && !arg2) {
    double minuten;
    if (!zahl(arg1, minuten) || floor(minuten) != minuten || minuten < -720 || minuten > 840) { antwort(id, "TZ: Minuten -720 bis 840 (UTC-12 bis +14)"); return; }
    tzMinuten = int(minuten); tzGesetzt = true;
    if (speicherOK) speicher.putInt("tz", tzMinuten);
    antwort(id); status(); return;
  }
  if (!strcmp(cmd, "TIME") && arg1 && !arg2) {
    double epoch;
    if (!zahl(arg1, epoch) || floor(epoch) != epoch || epoch < 946684800 || epoch > 4102444799.0) { antwort(id, "UTC-Zeit ausserhalb 2000 bis 2099"); return; }
    rtcLesen();
    if (!rtcVorhanden) { antwort(id, "DS3231 nicht erreichbar"); return; }
    rtc.adjust(DateTime(uint32_t(epoch))); rtcLesen();
    if (!rtcGueltig || labs(long(rtcSekunden - uint32_t(epoch))) > 2) { antwort(id, "RTC-Zeit nicht bestaetigt"); return; }
    antwort(id); status(); return;
  }
  if (!strcmp(cmd, "SWTEST") && !arg1) {
    if (!speicherOK) { antwort(id, "Speicher nicht bereit"); return; }
    for (auto& a : achsen) if (minAktiv(a) && maxAktiv(a)) { antwort(id, "Beide Schalter einer Achse aktiv"); return; }
    if (achsen[0].spanne>0 && achsen[1].spanne>0) {
      schalterTest.wiederherstellen(true,true); antwort(id); status(); return;
    }
    schalterTest.starten();
    int fehlend=achsen[0].spanne>0?1:0;
    if (fehlend==1) schalterTest.index=2;
    if (!kalibrierungStarten(achsen[fehlend])) { antwort(id,"Kalibrierung konnte nicht starten"); return; }
    antwort(id); status(); return;
  }
  if (schalterTest.aktiv) { antwort(id, "Zuerst Schaltertest abschliessen oder STOP"); return; }
  if (!arg1 || (strcmp(arg1,"AZ") && strcmp(arg1,"EL"))) { antwort(id, "Achse AZ oder EL erwartet"); return; }
  auto& a = achsen[!strcmp(arg1,"AZ") ? 0 : 1];
  if (minAktiv(a) && maxAktiv(a)) { antwort(id, "Beide Schalter aktiv"); return; }
  if (!strcmp(cmd, "CAL") && !arg2) {
    if (!schalterTest.ok()) { antwort(id, "Zuerst alle vier Endschalter pruefen"); return; }
    if (!kalibrierungStarten(a)) { antwort(id, "Kalibrierung konnte nicht starten"); return; }
    antwort(id); return;
  }
  if (!strcmp(cmd,"HOME") && !arg2) {
    if (!a.spanne) { antwort(id,"Zuerst fehlende Endlagen kalibrieren"); return; }
    if (a.referenz) { antwort(id); status(); return; }
    a.nurReferenz=true;
    bool ok=starten(a,SUCH_MIN,a.position-UMDREHUNG);
    antwort(id,ok?nullptr:"Referenzfahrt nicht gestartet: Speicherfehler"); return;
  }
  if (!strcmp(cmd, "REF") && !arg2) {
    if (!a.spanne || minAktiv(a) || maxAktiv(a)) { antwort(id, "Kalibrierung fehlt oder Schalter aktiv"); return; }
    a.position = ABSTAND; a.referenz = true;
    bool ok=sichern(a); antwort(id,ok?nullptr:"Referenz nicht gespeichert"); status(); return;
  }
  if (!strcmp(cmd, "LIMIT") && !arg2) {
    if (!schalterTest.ok() || !a.referenz || !a.spanne || minAktiv(a) || maxAktiv(a)) { antwort(id, "Schaltertest und Referenz fehlen oder Kontakt aktiv"); return; }
    bool ok=starten(a, TEST_MIN, ABSTAND); antwort(id,ok?nullptr:"Grenztest nicht gestartet: Speicherfehler"); return;
  }
  double grad;
  if (!zahl(arg2, grad)) { antwort(id, "Gueltiger Winkel erwartet"); return; }
  if (!strcmp(cmd, "JOG")) {
    if (abs(grad) > 5 || abs(grad) < 0.1) { antwort(id, "Tippfahrt: 0.1 bis 5 Grad"); return; }
    int ziel = a.position + lround(grad * UMDREHUNG / 360.0);
    if (a.referenz) {
      if (ziel < ABSTAND || ziel > a.spanne - ABSTAND) { antwort(id, "10-Grad-Grenze"); return; }
      starten(a, FAHRT, ziel);
    } else starten(a, TIPP, ziel);
    antwort(id,speicherOK?nullptr:"Tippfahrt nicht gestartet: Speicherfehler"); return;
  }
  if (!strcmp(cmd, "MOVE") || !strcmp(cmd, "AUTO")) {
    if (!strcmp(cmd, "AUTO") && (!freigegeben() || !autoOK || !rtcGueltig || !lcdErreichbar())) { antwort(id, "Automatik gesperrt: Schalter, Kalibrierung oder Grenztest fehlen"); return; }
    if (!a.referenz || !a.spanne) { antwort(id, "Achse zuerst referenzieren"); return; }
    if (grad < 0 || grad > 360) { antwort(id, "Winkel ausserhalb 0 bis 360"); return; }
    int ziel = lround(grad * UMDREHUNG / 360.0);
    if (ziel < ABSTAND || ziel > a.spanne - ABSTAND) { antwort(id, "10-Grad-Grenze"); return; }
    bool ok=starten(a, FAHRT, ziel); antwort(id,ok?nullptr:"Fahrt nicht gestartet: Speicherfehler"); return;
  }
  antwort(id, "Unbekannter Befehl");
}
}
void steuerungStarten() {
  Serial.begin(115200);
  Wire.begin(21, 22); Wire.setTimeOut(20); rtc.begin(&Wire); rtcLesen();
  speicherOK = speicher.begin("pc-tracker-v1", false);
  for (auto& a : achsen) {
    for (auto pin : a.pins) { pinMode(pin, OUTPUT); digitalWrite(pin, LOW); }
    pinMode(a.minPin, INPUT_PULLUP); pinMode(a.maxPin, INPUT_PULLUP);
    a.spanne = speicherOK ? speicher.getInt(a.schluessel, 0) : 0;
    if (a.spanne <= 2 * ABSTAND || a.spanne > UMDREHUNG) a.spanne = 0;
    const char* key=(&a==&achsen[0])?"az_state":"el_state";
    size_t bytes=speicherOK?speicher.getBytesLength(key):0;
    if (bytes) {
      PositionsDaten d;
      bool ok=bytes==sizeof(d) && speicher.getBytes(key,&d,sizeof(d))==sizeof(d) && datenGueltig(d);
      if (ok) {
        a.spanne=d.spanne; a.position=d.position; a.phase=d.phase; a.generation=d.generation;
        a.referenz=referenzLaden(d); a.grenzenOK=testsLaden(d);
        a.letzterStand=d; a.standVorhanden=true;
        if (kontakt(a.minPin) || kontakt(a.maxPin)) { a.referenz=false; a.grenzenOK=false; }
      } else {
        a.spanne=0; a.referenz=false; a.grenzenOK=false;
        Serial.println("{\"type\":\"fault\",\"message\":\"Gespeicherter Achsdatensatz ungueltig\"}");
      }
    } // Alte Firmware: Spanne bleibt erhalten, Position wird nicht erfunden.

  }
  schalterTest.wiederherstellen(achsen[0].spanne > 0, achsen[1].spanne > 0);
  autoOK=speicherOK && speicher.getBool("auto_ok",false);
  confOK = speicherOK && speicher.isKey("lat") && speicher.isKey("lon");
  if (confOK) {
    confBreite = speicher.getInt("lat",0)/1000.0f;
    confLaenge = speicher.getInt("lon",0)/1000.0f;
    confAzNull = speicher.getInt("aznull",9000)/100.0f;
    confElNeigung = speicher.getInt("elneig",9000)/100.0f;
  }
  autoModus = speicherOK && speicher.getBool("auto_mode",false);
  if (speicherOK) {
    String o = speicher.getString("ort", "");
    snprintf(ortText, sizeof(ortText), "%s", o.c_str());
  }
  tzGesetzt = speicherOK && speicher.isKey("tz");
  if (tzGesetzt) tzMinuten = speicher.getInt("tz", 0);
  if (autoOK) autoAnzeige("Tests gespeichert",freigegeben() && rtcGueltig?"Normalbetr.bereit":"Freigabe fehlt");
  status();
}
void steuerungAktualisieren() {
  // Richtungs-Endschalter vor jeder Auswertung entprellen.
  for (auto& a : achsen) kontakteEntprellen(a);
  if (verbunden && millis() - ping > WATCHDOG) {
    alleHalt(); verbunden = false;
    Serial.println("{\"type\":\"fault\",\"message\":\"PC-Verbindung unterbrochen: Motoren aus\"}");
  }
  // Pro Durchlauf begrenzt lesen: Motoren und Kontakte bleiben bedienbar.
  for (int n = 0; n < 32 && Serial.available(); ++n) {
    char c = char(Serial.read());
    if (c == '\n') {
      if (!ueberlauf) { zeile[laenge] = 0; befehl(); }
      else { alleHalt(); antwort(0, "Zeile zu lang"); }
      laenge = 0; ueberlauf = false;
    } else if (laenge < sizeof(zeile) - 1) zeile[laenge++] = c;
    else ueberlauf = true;
  }
  for (auto& a : achsen) aktualisieren(a);
  autoWeiter();
  autonomAktualisieren();
  if (!aktiv() && millis() - rtcZeit >= 1000) rtcLesen();
  if (millis() - lcdZeit >= 1000) { lcdZeit = millis(); lcdStatus(); }
  if (millis() - statusZeit >= 500) { statusZeit = millis(); status(); }
}
