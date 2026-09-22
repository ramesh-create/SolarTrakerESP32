#include "MenueTest.h"
#include <Wire.h>
#include <string.h>

namespace {
constexpr char VERSION[] = "0.1";
// Aktuelle Joystick-Belegung aus dem ESP32-Hauptprojekt vom 14.09.2026.
constexpr uint8_t JOY_X = 35, JOY_Y = 32, JOY_SW = 12;
constexpr uint8_t SDA_PIN = 21, SCL_PIN = 22;
constexpr int TOTZONE = 180;
}

void MenueTest::begin() {
  // Der Menue-Test fuehrt keine Motorfunktionen aus.
  const uint8_t motorPins[] = {16,17,18,19,25,26,27,14};
  for (uint8_t pin : motorPins) { digitalWrite(pin, LOW); pinMode(pin, OUTPUT); }
  Serial.begin(115200);
  analogReadResolution(10);
  pinMode(JOY_X, INPUT); pinMode(JOY_Y, INPUT); pinMode(JOY_SW, INPUT_PULLUP);
  Wire.begin(SDA_PIN, SCL_PIN, 100000);
  Wire.setTimeOut(50);
  const int status = _lcd.begin(16, 2);
  _lcdBereit = status == 0;
  if (_lcdBereit) { _lcd.backlight(); _lcd.print("Stick loslassen"); }
  else { Serial.print("LCD-Initialisierung fehlgeschlagen: "); Serial.println(status); }
  delay(1000);
  long summeX = 0, summeY = 0;
  for (uint8_t i = 0; i < 32; ++i) {
    summeX += analogRead(JOY_X); summeY += analogRead(JOY_Y); delay(5);
  }
  _mitteX = summeX / 32; _mitteY = summeY / 32;
  if (_mitteX < 150 || _mitteX > 873 || _mitteY < 150 || _mitteY > 873) {
    Serial.println("Joystick-Mitte unplausibel: Verdrahtung pruefen, zentrieren und neu starten.");
    _mitteX = 512; _mitteY = 512;
  }
  Serial.print("LCD-Joystick-Menue "); Serial.println(VERSION);
  Serial.println("Navigation und Tasterlogik beim Kompilieren geprueft.");
  Serial.println("Oben/unten: Auswahl; rechts/kurzer Druck: oeffnen; links/langer Druck: zurueck.");
  Serial.print("Joystick-Mitte X/Y: "); Serial.print(_mitteX); Serial.print('/'); Serial.println(_mitteY);
  auswahlGeaendert(); anzeigen();
}

MenueTest::Richtung MenueTest::richtung() const {
  const int x = analogRead(JOY_X) - _mitteX;
  const int y = analogRead(JOY_Y) - _mitteY;
  if (abs(x) < TOTZONE && abs(y) < TOTZONE) return MITTE;
  // Die zuletzt im Hauptprojekt eingestellte Orientierung beibehalten.
  if (abs(x) >= abs(y)) return x > 0 ? OBEN : UNTEN;
  return y > 0 ? RECHTS : LINKS;
}

void MenueTest::navigieren(Richtung r) {
  switch (r) {
    case OBEN: _menue.hoch(); break;
    case UNTEN: _menue.runter(); break;
    case LINKS: _menue.zurueck(); break;
    case RECHTS: _menue.waehlen(); break;
    default: return;
  }
  auswahlGeaendert();
}

void MenueTest::auswahlGeaendert() {
  _auswahlSeit = millis();
  Serial.print(MenueDaten::titel(_menue.seite)); Serial.print(" > "); Serial.print(_menue.auswahl());
  Serial.println(_menue.detail ? " [Menue-Vorschau]" : "");
  anzeigen();
}

void MenueTest::update() {
  const uint32_t jetzt = millis();
  const TasterAktion taste = _taster.lesen(digitalRead(JOY_SW) == LOW, jetzt);
  if (taste == TasterAktion::KURZ) { _menue.waehlen(); auswahlGeaendert(); }
  if (taste == TasterAktion::LANG) { _menue.zurueck(); auswahlGeaendert(); }
  if (_taster.gedrueckt() || taste != TasterAktion::KEINE) {
    _roh = MITTE; _stabil = MITTE; _wechsel = jetzt;
  } else {
    const Richtung r = richtung();
    if (r != _roh) { _roh = r; _wechsel = jetzt; }
    if (jetzt - _wechsel >= 40) {
      if (_stabil != _roh) {
        _stabil = _roh; _gedruecktSeit = jetzt; _wiederholung = jetzt;
        navigieren(_stabil);
      } else if ((_stabil == OBEN || _stabil == UNTEN) &&
                 jetzt - _gedruecktSeit >= 450 && jetzt - _wiederholung >= 180) {
        _wiederholung = jetzt; navigieren(_stabil);
      }
    }
  }
  if (jetzt - _anzeigeZeit >= 100) { _anzeigeZeit = jetzt; anzeigen(); }
  delay(1);
}

void MenueTest::ausschnitt(char* ziel, const char* text, uint8_t breite) const {
  const size_t laenge = strlen(text);
  size_t start = 0;
  const uint32_t zeit = millis() - _auswahlSeit;
  if (laenge > breite && zeit > 1200) {
    const size_t schritte = laenge - breite;
    const size_t phase = ((zeit - 1200) / 350) % (schritte + 5);
    start = phase > schritte ? schritte : phase;
  }
  snprintf(ziel, breite + 1, "%.*s", breite, text + start);
}

void MenueTest::zeile(uint8_t nummer, const char* text) {
  char neu[17];
  memset(neu, ' ', 16); neu[16] = '\0';
  const size_t n = strlen(text) < 16 ? strlen(text) : 16;
  memcpy(neu, text, n);
  if (strcmp(neu, _zeilen[nummer]) == 0) return;
  memcpy(_zeilen[nummer], neu, sizeof(neu));
  if (_lcdBereit) { _lcd.setCursor(0, nummer); _lcd.print(neu); }
}

void MenueTest::anzeigen() {
  char oben[17], unten[17];
  if (_menue.detail) {
    ausschnitt(oben, _menue.auswahl(), 16);
    snprintf(unten, sizeof(unten), "%s", ((millis() - _auswahlSeit) / 2000) % 2
                                            ? "Links: zurueck" : "Menue-Vorschau");
  } else {
    char zaehler[8];
    snprintf(zaehler, sizeof(zaehler), "%u/%u", _menue.index() + 1, MenueDaten::anzahl(_menue.seite));
    const int titelBreite = 15 - strlen(zaehler);
    snprintf(oben, sizeof(oben), "%.*s %s", titelBreite, MenueDaten::titel(_menue.seite), zaehler);
    unten[0] = '>'; ausschnitt(unten + 1, _menue.auswahl(), 15);
  }
  zeile(0, oben); zeile(1, unten);
}
