#pragma once
#include <stdint.h>
// Version 0.3.1: nur das Oeffnen eines bekannten Gegenkontakts entprellen.
// Ein neuer Kontakt in Fahrtrichtung bleibt in Steuerung.cpp sofort wirksam.
enum class KontaktFehler { KEIN, UNERWARTET, KLEMMT };
struct Gegenkontakt {
  bool erlaubt = false, offen = false;
  uint32_t offenSeit = 0;
  constexpr void starten(bool bekanntAktiv) { erlaubt = bekanntAktiv; offen = false; offenSeit = 0; }
  constexpr bool stabilOffen(uint32_t jetzt) const { return offen && uint32_t(jetzt - offenSeit) >= 25; }
  constexpr KontaktFehler pruefen(bool aktiv, int schritte, uint32_t jetzt, int maximum) {
    if (aktiv) {
      offen = false;
      if (!erlaubt) return KontaktFehler::UNERWARTET;
      if (schritte >= maximum) return KontaktFehler::KLEMMT;
    } else {
      if (!offen) { offen = true; offenSeit = jetzt; }
      if (stabilOffen(jetzt)) erlaubt = false;
    }
    return KontaktFehler::KEIN;
  }
};
constexpr bool pruefeKontaktprellen() {
  Gegenkontakt k;
  k.starten(true);
  if (k.pruefen(true, 0, 0, 114) != KontaktFehler::KEIN) return false;
  k.pruefen(false, 1, 3, 114);
  if (k.pruefen(true, 2, 6, 114) != KontaktFehler::KEIN) return false;
  k.pruefen(false, 3, 9, 114);
  k.pruefen(false, 10, 33, 114);
  if (k.stabilOffen(33)) return false;
  k.pruefen(false, 11, 34, 114);
  if (!k.stabilOffen(34)) return false;
  if (k.pruefen(true, 12, 35, 114) != KontaktFehler::UNERWARTET) return false;
  k.starten(true);
  if (k.pruefen(true, 114, 400, 114) != KontaktFehler::KLEMMT) return false;
  k.starten(false);
  if (k.pruefen(true, 0, 0, 114) != KontaktFehler::UNERWARTET) return false;
  k.starten(true);
  k.pruefen(false, 0, 0xfffffff0U, 114);
  k.pruefen(false, 1, 9, 114);
  return k.stabilOffen(9);
}
static_assert(pruefeKontaktprellen(), "Gegenkontakt-Entprellung fehlerhaft");
