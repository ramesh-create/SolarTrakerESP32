// SolarTracker 0.8: Standalone-Menue, zusaetzlich per serieller Fernbedienung bedienbar.
#include "Config.h"

#include "LCD_Menu.h"

#include "Joystick.h"

#include "Menu.h"

#include "Motor.h"

#include "SettingsStorage.h"

#include "SoftwareClock.h"

#include "NOAA.h"

LCDMenu lcdMenu;

Joystick joystick;

MotorController motor;

SettingsStorage settingsStorage;

SoftwareClock softwareClock;

MenuSystem menu;

// Serielle Menue-Fernbedienung: Buchstaben loesen Joystick-Aktionen aus.
// u/d/l/r = Richtung, e = ENTER, b = zurueck (ENTER lang). Kehrt JOY_NONE zurueck,
// wenn keine Taste anliegt; dann gilt die echte Joystick-Eingabe.
JoystickAction serielleAktion() {
  while (Serial.available() > 0) {
    char c = char(Serial.read());
    switch (c) {
      case 'u': case 'U': return JOY_UP;
      case 'd': case 'D': return JOY_DOWN;
      case 'l': case 'L': return JOY_LEFT;
      case 'r': case 'R': return JOY_RIGHT;
      case 'e': case 'E': return JOY_ENTER;
      case 'b': case 'B': return JOY_ENTER_LONG;
      default: break;
    }
  }
  return JOY_NONE;
}

void setup() {
  
  Serial.begin(115200);
  Serial.println("Menue-Fernbedienung: u/d/l/r Richtung, e ENTER, b zurueck");

  analogReadResolution(ANALOG_READ_RESOLUTION);
  
  lcdMenu.begin();
  
  joystick.begin();
  
  motor.begin();
  
  settingsStorage.begin();

  
  delay(START_SCREEN_MS);

  
  menu.begin(&lcdMenu, &motor, &settingsStorage, &softwareClock);
}

void loop() {
  
  softwareClock.update();

  
  JoystickAction action = joystick.readAction();

  // Serielle Fernbedienung hat Vorrang, wenn eine Taste gesendet wurde.
  JoystickAction seriell = serielleAktion();
  if (seriell != JOY_NONE) {
    action = seriell;
  }

  
  menu.handle(action);
  
  menu.update();
  
  lcdMenu.update();
}