#pragma once
#include <stdint.h>
// Version 0.3.0: Fortschritt der automatischen Kalibrierung AZ, danach EL.
// Ein Kontakt zaehlt erst nach vollstaendiger Entlastung; MAX erst nach Speichern.
struct SchalterPruefung {
  bool aktiv = false;
  uint8_t index = 0;
  constexpr void starten() { aktiv = true; index = 0; }
  constexpr void loeschen() { aktiv = false; index = 0; }
  constexpr void wiederherstellen(bool az, bool el) { aktiv = false; index = az && el ? 4 : 0; }
  constexpr bool ok() const { return index == 4 && !aktiv; }
  constexpr bool minEntlastet(uint8_t achse) {
    if (!aktiv || index != 2 * achse) return false;
    ++index; return true;
  }
  constexpr bool maxGespeichert(uint8_t achse) {
    if (!aktiv || index != 2 * achse + 1) return false;
    ++index;
    if (index == 4) aktiv = false;
    return true;
  }
};
constexpr bool pruefeAutomatischenAblauf() {
  SchalterPruefung p;
  p.starten();
  if (p.maxGespeichert(0) || p.minEntlastet(1) || p.ok()) return false;
  if (!p.minEntlastet(0) || p.index != 1) return false;
  if (!p.maxGespeichert(0) || p.index != 2 || !p.aktiv) return false;
  if (p.maxGespeichert(1) || !p.minEntlastet(1)) return false;
  if (!p.maxGespeichert(1) || !p.ok()) return false;
  p.starten(); p.minEntlastet(0); p.loeschen();
  if (p.ok() || p.aktiv || p.index != 0) return false;
  p.wiederherstellen(true, false);
  if (p.ok()) return false;
  p.wiederherstellen(true, true);
  return p.ok() && !p.aktiv;
}
static_assert(pruefeAutomatischenAblauf(), "Automatische Endschalterfolge ungueltig");
