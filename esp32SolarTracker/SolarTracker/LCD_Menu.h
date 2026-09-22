

#ifndef LCD_MENU_H
#define LCD_MENU_H


#include <Arduino.h>


class LCDMenu {
public:
  
  void begin();
  
  void show(const char* line1, const char* line2);
  
  void showFlash(const char* line1, const char* line2, unsigned long durationMs);
  
  void update();
  
  void clear();
  
  void setBacklight(bool enabled);

private:
  
  void printPadded(uint8_t row, const char* text);

  
  char _line1[17] = "";
  
  char _line2[17] = "";
  
  bool _flashActive = false;
  
  unsigned long _flashUntil = 0;
};

#endif

