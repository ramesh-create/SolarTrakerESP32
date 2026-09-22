#pragma once
#include <stdint.h>
// Version 0.4.2: Fahrtrichtungs-Endschalter erst nach stabiler Low-Dauer auswerten.
// Ein einzelner Prell-/Stoerimpuls darf eine Suche oder einen Grenztest nicht ausloesen.
struct Entprellung {
  bool roh = false, stabil = false, gestartet = false;
  uint32_t seit = 0;
  constexpr bool aktualisieren(bool lowRoh, uint32_t jetzt, uint32_t dauer) {
    if (!gestartet || lowRoh != roh) { roh = lowRoh; seit = jetzt; gestartet = true; }
    if (!roh) stabil = false;
    else if (uint32_t(jetzt - seit) >= dauer) stabil = true;
    return stabil;
  }
};
constexpr bool pruefeEndschalterEntprellung() {
  Entprellung e;
  // Ein kurzer Impuls gilt nicht als gedrueckt.
  if (e.aktualisieren(true, 0, 30)) return false;
  if (e.aktualisieren(true, 10, 30)) return false;
  if (e.aktualisieren(false, 12, 30)) return false;
  // Erst 30 ms durchgehend Low gelten als gedrueckt.
  if (e.aktualisieren(true, 100, 30)) return false;
  if (e.aktualisieren(true, 125, 30)) return false;
  if (!e.aktualisieren(true, 130, 30)) return false;
  // Kurzes Prellen setzt die stabile Erkennung zurueck.
  if (e.aktualisieren(false, 131, 30)) return false;
  if (e.aktualisieren(true, 132, 30)) return false;
  if (e.aktualisieren(true, 161, 30)) return false;
  if (!e.aktualisieren(true, 162, 30)) return false;
  // millis-Ueberlauf bleibt korrekt.
  Entprellung u;
  u.aktualisieren(true, 0xfffffff0U, 30);
  return u.aktualisieren(true, 20, 30);
}
static_assert(pruefeEndschalterEntprellung(), "Endschalter-Entprellung fehlerhaft");