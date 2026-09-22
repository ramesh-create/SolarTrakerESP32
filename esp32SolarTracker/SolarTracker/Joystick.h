

#ifndef JOYSTICK_H
#define JOYSTICK_H


#include <Arduino.h>


enum JoystickAction {
  
  JOY_NONE,
  
  JOY_UP,
  
  JOY_DOWN,
  
  JOY_LEFT,
  
  JOY_RIGHT,
  
  JOY_ENTER,
  
  JOY_ENTER_LONG
};


class Joystick {
public:
  
  void begin();
  
  JoystickAction readAction();

private:
  
  JoystickAction readRawAction() const;
  
  bool isPressed(uint8_t pin) const;

  
  JoystickAction _lastRawAction = JOY_NONE;
  
  JoystickAction _activeAction = JOY_NONE;
  
  unsigned long _lastChangeMs = 0;
  
  unsigned long _pressStartMs = 0;
  
  unsigned long _lastRepeatMs = 0;
  
  bool _longEnterSent = false;
};

#endif

