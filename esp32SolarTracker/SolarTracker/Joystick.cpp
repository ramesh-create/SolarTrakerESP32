

#include "Joystick.h"
#include "Config.h"

void Joystick::begin() {
  
  pinMode(PIN_JOYSTICK_X, INPUT);
  
  pinMode(PIN_JOYSTICK_Y, INPUT);
  
  pinMode(PIN_JOYSTICK_SW, INPUT_PULLUP);
}

JoystickAction Joystick::readAction() {
  
  const unsigned long now = millis();
  
  JoystickAction rawAction = readRawAction();

  
  if (rawAction != _lastRawAction) {
    _lastRawAction = rawAction;
    _lastChangeMs = now;
    
    return JOY_NONE;
  }

  
  if (now - _lastChangeMs < JOYSTICK_DEBOUNCE_MS) {
    return JOY_NONE;
  }

  
  if (rawAction == JOY_NONE) {
    _activeAction = JOY_NONE;
    _longEnterSent = false;
    return JOY_NONE;
  }

  
  if (_activeAction != rawAction) {
    _activeAction = rawAction;
    _pressStartMs = now;
    _lastRepeatMs = now;
    _longEnterSent = false;
    return rawAction;
  }

  
  if (rawAction == JOY_ENTER) {
    if (!_longEnterSent && now - _pressStartMs >= JOYSTICK_LONG_PRESS_MS) {
      _longEnterSent = true;
      return JOY_ENTER_LONG;
    }
    return JOY_NONE;
  }

  
  if (now - _pressStartMs >= JOYSTICK_REPEAT_DELAY_MS &&
      now - _lastRepeatMs >= JOYSTICK_REPEAT_INTERVAL_MS) {
    _lastRepeatMs = now;
    return rawAction;
  }

  return JOY_NONE;
}

JoystickAction Joystick::readRawAction() const {
  
  if (isPressed(PIN_JOYSTICK_SW)) {
    return JOY_ENTER;
  }

  
  const int xValue = analogRead(PIN_JOYSTICK_X);
  const int yValue = analogRead(PIN_JOYSTICK_Y);

  
// UP/DOWN ueber die X-Achse (zuverlaessig bei diagonalem Stick)
  // Kalibrierung: OBEN = X hoch (1023), UNTEN = X nieder (0)
  if (xValue > JOYSTICK_HIGH_THRESHOLD) {
    return JOY_UP;
  }

  if (xValue < JOYSTICK_LOW_THRESHOLD) {
    return JOY_DOWN;
  }

  // LEFT/RIGHT ueber die Y-Achse
  if (yValue < JOYSTICK_LOW_THRESHOLD) {
    return JOY_LEFT;
  }

  if (yValue > JOYSTICK_HIGH_THRESHOLD) {
    return JOY_RIGHT;
  }

  return JOY_NONE;
}

bool Joystick::isPressed(uint8_t pin) const {
  
  return digitalRead(pin) == LOW;
}

