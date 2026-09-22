

#include "LCD_Menu.h"
#include "Config.h"

#include <Wire.h>
#include <hd44780.h>
#include <hd44780ioClass/hd44780_I2Cexp.h>


static hd44780_I2Cexp lcd;

void LCDMenu::begin() {
  
  lcd.begin(LCD_COLS, LCD_ROWS);
  
  lcd.backlight();
  
  clear();
  
  show("SolarTracker", "Version 0.3.1");
}

void LCDMenu::show(const char* line1, const char* line2) {
  
  strncpy(_line1, line1, LCD_COLS);
  
  strncpy(_line2, line2, LCD_COLS);
  
  _line1[LCD_COLS] = '\0';
  _line2[LCD_COLS] = '\0';

  
  _flashActive = false;
  
  printPadded(0, _line1);
  printPadded(1, _line2);
}

void LCDMenu::showFlash(const char* line1, const char* line2, unsigned long durationMs) {
  
  _flashActive = true;
  
  _flashUntil = millis() + durationMs;
  
  printPadded(0, line1);
  printPadded(1, line2);
}

void LCDMenu::update() {
  
  if (_flashActive && millis() >= _flashUntil) {
    
    _flashActive = false;
    printPadded(0, _line1);
    printPadded(1, _line2);
  }
}

void LCDMenu::clear() {
  
  lcd.clear();
}

void LCDMenu::setBacklight(bool enabled) {
  
  if (enabled) {
    lcd.backlight();
  } else {
    lcd.noBacklight();
  }
}

void LCDMenu::printPadded(uint8_t row, const char* text) {
  
  lcd.setCursor(0, row);

  
  uint8_t i = 0;
  
  while (text[i] != '\0' && i < LCD_COLS) {
    lcd.print(text[i]);
    i++;
  }

  
  while (i < LCD_COLS) {
    lcd.print(' ');
    i++;
  }
}

