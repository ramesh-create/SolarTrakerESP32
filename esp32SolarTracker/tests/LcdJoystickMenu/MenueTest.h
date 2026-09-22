#pragma once
#include <Arduino.h>
#include <Wire.h>
#include <hd44780.h>
#include <hd44780ioClass/hd44780_I2Cexp.h>
#include "MenueModell.h"
#include "TasterLogik.h"

class MenueTest {
 public:
  void begin();
  void update();
 private:
  enum Richtung { MITTE, OBEN, UNTEN, LINKS, RECHTS };
  hd44780_I2Cexp _lcd{0x27};
  MenueModell _menue;
  TasterLogik _taster;
  bool _lcdBereit = false;
  int _mitteX = 512, _mitteY = 512;
  Richtung _roh = MITTE, _stabil = MITTE;
  uint32_t _wechsel = 0, _gedruecktSeit = 0, _wiederholung = 0;
  uint32_t _auswahlSeit = 0, _anzeigeZeit = 0;
  char _zeilen[2][17] = {};
  Richtung richtung() const;
  void navigieren(Richtung richtung);
  void auswahlGeaendert();
  void anzeigen();
  void zeile(uint8_t nummer, const char* text);
  void ausschnitt(char* ziel, const char* text, uint8_t breite) const;
};
