// Version 0.3.2. Bewaehrte Initialisierung aus tests/LcdTest.
#include "LcdSteuerung.h"
#include "LcdText.h"
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
namespace {
LiquidCrystal_I2C lcd(0x27,16,2);
bool initialisiert=false, vorhanden=false;
bool pruefen() {
  Wire.beginTransmission(0x27);
  vorhanden = Wire.endTransmission()==0;
  if (!vorhanden) initialisiert=false;
  return vorhanden;
}
}
bool lcdErreichbar() { return vorhanden; }
const char* lcdTextSenden(const char* zeile1,const char* zeile2) {
  if (!lcdZeileGueltig(zeile1) || !lcdZeileGueltig(zeile2))
    return "LCD: zwei Hex-Zeilen mit je 16 ASCII-Zeichen erwartet";
  if (!pruefen()) return "LCD 0x27 nicht erreichbar: SDA21/SCL22 pruefen";
  if (!initialisiert) {
    lcd.init(); lcd.backlight(); lcd.display();
    initialisiert=true;
  }
  const char* texte[]={zeile1,zeile2};
  for (int zeile=0;zeile<2;++zeile) {
    lcd.setCursor(0,zeile);
    for (int i=0;i<16;++i) {
      lcd.write(uint8_t(hexZiffer(texte[zeile][2*i])*16+hexZiffer(texte[zeile][2*i+1])));
      if (!pruefen()) return "LCD: I2C-Verbindung beim Schreiben verloren";
    }
  }
  return nullptr; // Text gesendet; sichtbare Zeichen muss der Bediener pruefen.
}
