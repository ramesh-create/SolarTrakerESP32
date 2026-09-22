

#ifndef MENU_H
#define MENU_H

#include <Arduino.h>
#include "Joystick.h"
#include "LCD_Menu.h"
#include "Motor.h"
#include "SettingsStorage.h"
#include "SoftwareClock.h"
#include "NOAA.h"

enum MenuScreen {
  SCREEN_MAIN,
  SCREEN_NORMAL,
  SCREEN_SIMULATION,
  SCREEN_NORMAL_MENU,
  SCREEN_SIMULATION_MENU,
  SCREEN_SETTINGS,
  SCREEN_TEST_MENU,
  SCREEN_START_POSITION_INFO,
  SCREEN_END_POSITION_INFO,
  SCREEN_SWITCH_TEST,
  SCREEN_EDIT
};

enum EditField {
  EDIT_NONE,
  EDIT_MANUAL_AXES,
  EDIT_AZIMUTH,
  EDIT_ELEVATION,
  EDIT_DATE_DAY,
  EDIT_DATE_MONTH,
  EDIT_DATE_YEAR,
  EDIT_TIME_HOUR,
  EDIT_TIME_MINUTE,
  EDIT_START_AZIMUTH,
  EDIT_START_ELEVATION,
  EDIT_LATITUDE,
  EDIT_LONGITUDE,
  EDIT_SIM_SPEED
};

class MenuSystem {
public:
  void begin(LCDMenu* lcd);
  void begin(LCDMenu* lcd, MotorController* motor);
  void begin(LCDMenu* lcd, MotorController* motor, SettingsStorage* storage);
  void begin(LCDMenu* lcd, MotorController* motor, SettingsStorage* storage, SoftwareClock* clock);
  void handle(JoystickAction action);
  void update();

private:
  void render();
  void renderMenuPage(const char* title, const char* const* items, uint8_t count, uint8_t index);
  void enterCurrentItem();
  void goBack();
  void moveUp();
  void moveDown();

  void startEdit(EditField field);
  void renderEdit();
  void increaseEditValue();
  void decreaseEditValue();
  void nextEditFieldOrSave();
  void saveEdit(const char* message);
  void clampValues();
  void formatCoordinate(char* buffer, size_t size, long valueThousandths) const;
  void loadSettingsFromStorage();
  void saveSettingsToStorage();
  void syncFromClock();
  void syncClockFromMenu();
  void syncStartPositionFromHomeSwitch();
  void moveToStartPositionByHomeSwitch();
  void calibrateAxes();
  void startSimulation();
  void runTestEndschalter();
  void runTestRTC();
  void runTestLCD();
  void runTestAzimutMotor();
  void runTestElevationMotor();
  void runTestJoystick();
  void updateNormal();
  void updateSimulation();
  void finishSimulationAndReturnHome();

  LCDMenu* _lcd = nullptr;
  MotorController* _motor = nullptr;
  SettingsStorage* _storage = nullptr;
  SoftwareClock* _clock = nullptr;
  NOAA _noaa;
  MenuScreen _screen = SCREEN_MAIN;
  MenuScreen _returnScreen = SCREEN_MAIN;
  uint8_t _mainIndex = 0;
  uint8_t _normalIndex = 0;
  uint8_t _simulationIndex = 0;
  uint8_t _settingsIndex = 0;
  uint8_t _testIndex = 0;
  bool _dirty = true;

  EditField _editField = EDIT_NONE;

  int _azimuth = 90;
  int _elevation = 0;
  int _startAzimuth = 90;
  int _startElevation = 0;
  int _endAzimuth = 270;
  int _endElevation = 0;
  int _day = 7;
  int _month = 7;
  int _year = 2026;
  int _hour = 12;
  int _minute = 0;
  long _latitudeThousandths = 50187;
  long _longitudeThousandths = 8739;
  int _simulationSpeed = 1;
  bool _normalRunning = false;
  unsigned long _normalLastUpdateMs = 0;
  bool _simulationRunning = false;
  unsigned long _simulationStartMs = 0;
  unsigned long _simulationDurationMs = 60000;
  int _simulationLastStep = -1;
  int _simulationStartAzimuth = 90;
  int _simulationStartElevation = 0;
};

#endif

