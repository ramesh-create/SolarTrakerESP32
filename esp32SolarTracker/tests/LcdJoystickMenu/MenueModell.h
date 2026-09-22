#pragma once
#include <stdint.h>

// Menue-Test 0.1: vollstaendige Navigation ohne Hardwareaktionen.
namespace MenueDaten {
enum Seite : uint8_t { HAUPT, NORMAL, SIMULATION, TEST, EINSTELLUNGEN };
constexpr const char* HAUPTEINTRAEGE[] = {"Normalbetrieb", "Simulation", "Testbetrieb", "Einstellungen"};
constexpr const char* NORMALEINTRAEGE[] = {"Betrieb starten", "Status anzeigen"};
constexpr const char* SIMULATIONSEINTRAEGE[] = {"Simulation Start", "Geschwindigkeit"};
constexpr const char* TESTEINTRAEGE[] = {
  "Endschalter", "RTC (DS3231)", "LCD", "Azimut-Motor", "Elevation-Motor", "Joystick", "Alles testen"
};
constexpr const char* EINSTELLUNGSEINTRAEGE[] = {
  "Az/El manuell", "Datum", "Uhrzeit", "Breite", "Laenge", "Startpos fahren",
  "Startpos speichern", "Startpos lesen", "Endpos fahren", "Endpos speichern",
  "Endpos lesen", "Schalter-Test", "Kalibrierung starten"
};
constexpr uint8_t anzahl(Seite seite) {
  switch (seite) {
    case HAUPT: return 4;
    case NORMAL: case SIMULATION: return 2;
    case TEST: return 7;
    case EINSTELLUNGEN: return 13;
  }
  return 0;
}
constexpr const char* titel(Seite seite) {
  switch (seite) {
    case HAUPT: return "Hauptmenue";
    case NORMAL: return "Normalbetrieb";
    case SIMULATION: return "Simulation";
    case TEST: return "Testbetrieb";
    case EINSTELLUNGEN: return "Einstellungen";
  }
  return "";
}
constexpr const char* eintrag(Seite seite, uint8_t index) {
  if (index >= anzahl(seite)) return "";
  switch (seite) {
    case HAUPT: return HAUPTEINTRAEGE[index];
    case NORMAL: return NORMALEINTRAEGE[index];
    case SIMULATION: return SIMULATIONSEINTRAEGE[index];
    case TEST: return TESTEINTRAEGE[index];
    case EINSTELLUNGEN: return EINSTELLUNGSEINTRAEGE[index];
  }
  return "";
}
}

class MenueModell {
 public:
  MenueDaten::Seite seite = MenueDaten::HAUPT;
  bool detail = false;
  constexpr uint8_t index() const { return _indizes[seite]; }
  constexpr const char* auswahl() const { return MenueDaten::eintrag(seite, index()); }
  constexpr void hoch() {
    if (!detail) _indizes[seite] = index() == 0 ? MenueDaten::anzahl(seite) - 1 : index() - 1;
  }
  constexpr void runter() {
    if (!detail) _indizes[seite] = (index() + 1) % MenueDaten::anzahl(seite);
  }
  constexpr void waehlen() {
    if (detail) return;
    if (seite == MenueDaten::HAUPT) seite = static_cast<MenueDaten::Seite>(index() + 1);
    else detail = true;
  }
  constexpr void zurueck() {
    if (detail) detail = false;
    else seite = MenueDaten::HAUPT;
  }
 private:
  uint8_t _indizes[5] = {};
};

// Diese Pruefung wird beim Kompilieren ausgefuehrt, nicht auf der Mechanik.
constexpr bool pruefeMenueNavigation() {
  MenueModell haupt;
  haupt.hoch();
  if (haupt.index() != 3) return false;
  haupt.runter(); haupt.zurueck();
  if (haupt.index() != 0 || haupt.seite != MenueDaten::HAUPT) return false;
  for (uint8_t gruppe = 0; gruppe < 4; ++gruppe) {
    MenueModell m;
    for (uint8_t i = 0; i < gruppe; ++i) m.runter();
    m.waehlen();
    const auto untermenue = m.seite;
    if (untermenue != static_cast<MenueDaten::Seite>(gruppe + 1) || m.index() != 0) return false;
    const uint8_t n = MenueDaten::anzahl(untermenue);
    for (uint8_t i = 0; i < n; ++i) {
      if (m.index() != i || m.auswahl()[0] == '\0') return false;
      m.waehlen();
      if (!m.detail) return false;
      m.hoch(); m.runter();
      if (m.index() != i) return false;
      m.zurueck();
      if (m.detail || m.seite != untermenue || m.index() != i) return false;
      m.runter();
    }
    if (m.index() != 0) return false;
    m.hoch(); m.zurueck();
    if (m.seite != MenueDaten::HAUPT || m.index() != gruppe) return false;
    m.waehlen();
    if (m.seite != untermenue || m.index() != n - 1) return false;
  }
  return true;
}
static_assert(pruefeMenueNavigation(), "Menue-Navigation fehlerhaft");
