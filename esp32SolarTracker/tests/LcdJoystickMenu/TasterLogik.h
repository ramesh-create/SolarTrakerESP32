#pragma once
#include <stdint.h>

enum class TasterAktion { KEINE, KURZ, LANG };
class TasterLogik {
 public:
  constexpr TasterAktion lesen(bool gedrueckt, uint32_t jetzt) {
    if (gedrueckt != _roh) { _roh = gedrueckt; _wechsel = jetzt; }
    if (jetzt - _wechsel >= 40 && _stabil != _roh) {
      _stabil = _roh;
      if (_stabil) { _beginn = jetzt; _langGesendet = false; }
      else if (!_langGesendet) return TasterAktion::KURZ;
    }
    if (_stabil && _roh && !_langGesendet && jetzt - _beginn >= 900) {
      _langGesendet = true;
      return TasterAktion::LANG;
    }
    return TasterAktion::KEINE;
  }
  constexpr bool gedrueckt() const { return _roh || _stabil; }
 private:
  bool _roh = false, _stabil = false, _langGesendet = false;
  uint32_t _wechsel = 0, _beginn = 0;
};
constexpr bool pruefeTaster() {
  TasterLogik kurz;
  if (kurz.lesen(true, 0) != TasterAktion::KEINE || kurz.lesen(true, 40) != TasterAktion::KEINE) return false;
  if (kurz.lesen(false, 200) != TasterAktion::KEINE || kurz.lesen(false, 240) != TasterAktion::KURZ) return false;
  if (kurz.lesen(false, 300) != TasterAktion::KEINE) return false;
  TasterLogik lang;
  lang.lesen(true, 0); lang.lesen(true, 40);
  if (lang.lesen(true, 939) != TasterAktion::KEINE || lang.lesen(true, 940) != TasterAktion::LANG) return false;
  if (lang.lesen(true, 1100) != TasterAktion::KEINE) return false;
  lang.lesen(false, 1200);
  if (lang.lesen(false, 1240) != TasterAktion::KEINE) return false;
  TasterLogik prellen;
  prellen.lesen(true, 0); prellen.lesen(false, 10);
  return prellen.lesen(false, 100) == TasterAktion::KEINE;
}
static_assert(pruefeTaster(), "Tasterauswertung fehlerhaft");
