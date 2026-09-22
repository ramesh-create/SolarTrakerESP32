


#include "Menu.h"

#include "Config.h"

#include <RTClib.h>
#include <Wire.h>


static const char* const MAIN_ITEMS[] = {
  "Normalbetrieb",
  "Simulation",
  "Testbetrieb",
  "Einstellungen"
};


static const char* const SETTINGS_ITEMS[] = {
  "Az/El manuell",
  "Datum setzen",
  "Uhrzeit setzen",
  "Breite setzen",
  "Laenge setzen",
  "Startpos fahren",
  "Startpos speichern",
  "Startpos lesen",
  "Endpos fahren",
  "Endpos speichern",
  "Endpos lesen",
  "Schalter-Test",
  "Kalibrierung starten"
};


static const char* const NORMAL_ITEMS[] = {
  "Betrieb starten",
  "Status anzeigen"
};


static const char* const SIMULATION_ITEMS[] = {
  "Simulation Start",
  "Geschwindigkeit"
};

static const char* const TEST_ITEMS[] = {
  "Endschalter",
  "RTC (DS3231)",
  "LCD",
  "Azimut-Motor",
  "Elevation-Motor",
  "Joystick",
  "Alles testen"
};

void MenuSystem::begin(LCDMenu* lcd) {
  begin(lcd, nullptr, nullptr, nullptr);
}

void MenuSystem::begin(LCDMenu* lcd, MotorController* motor) {
  begin(lcd, motor, nullptr, nullptr);
}

void MenuSystem::begin(LCDMenu* lcd, MotorController* motor, SettingsStorage* storage) {
  begin(lcd, motor, storage, nullptr);
}

void MenuSystem::begin(LCDMenu* lcd, MotorController* motor, SettingsStorage* storage, SoftwareClock* clock) {
  
  _lcd = lcd;
  _motor = motor;
  _storage = storage;
  _clock = clock;
  _screen = SCREEN_MAIN;
  _mainIndex = 0;
  _normalIndex = 0;
  _simulationIndex = 0;
  _settingsIndex = 0;
  _dirty = true;
  
  loadSettingsFromStorage();
  syncStartPositionFromHomeSwitch();
  render();
}

void MenuSystem::handle(JoystickAction action) {
  
  if (action == JOY_NONE) {
    return;
  }

  if (_screen == SCREEN_EDIT) {
    if (_editField == EDIT_MANUAL_AXES) {
      if (action == JOY_UP) {
        if (_motor != nullptr) {
          if (_motor->movePanelDegrees(MOTOR_ELEVATION, -1)) {
            _elevation++;
          }
        } else {
          _elevation++;
        }
        clampValues();
        _dirty = true;
      } else if (action == JOY_DOWN) {
        if (_motor != nullptr) {
          if (_motor->movePanelDegrees(MOTOR_ELEVATION, 1)) {
            _elevation--;
          }
        } else {
          _elevation--;
        }
        clampValues();
        _dirty = true;
      } else if (action == JOY_RIGHT) {
        if (_motor != nullptr) {
          if (_motor->moveDegrees(MOTOR_AZIMUTH, 1)) {
            _azimuth++;
          }
        } else {
          _azimuth++;
        }
        clampValues();
        _dirty = true;
      } else if (action == JOY_LEFT) {
        if (_motor != nullptr) {
          if (_motor->moveDegrees(MOTOR_AZIMUTH, -1)) {
            _azimuth--;
          }
        } else {
          _azimuth--;
        }
        clampValues();
        _dirty = true;
      } else if (action == JOY_ENTER || action == JOY_ENTER_LONG) {
        saveEdit("Manuell OK");
        _dirty = true;
      }
      return;
    }

    switch (action) {
      case JOY_UP:
        increaseEditValue();
        _dirty = true;
        break;
      case JOY_DOWN:
        decreaseEditValue();
        _dirty = true;
        break;
      case JOY_ENTER:
      case JOY_RIGHT:
        nextEditFieldOrSave();
        _dirty = true;
        break;
      case JOY_LEFT:
      case JOY_ENTER_LONG:
        goBack();
        _dirty = true;
        break;
      default:
        break;
    }
    return;
  }

  switch (action) {
    case JOY_UP:
      moveUp();
      _dirty = true;
      break;
    case JOY_DOWN:
      moveDown();
      _dirty = true;
      break;
    case JOY_ENTER:
    case JOY_RIGHT:
      enterCurrentItem();
      _dirty = true;
      break;
    case JOY_LEFT:
    case JOY_ENTER_LONG:
      goBack();
      _dirty = true;
      break;
    default:
      break;
  }
}

void MenuSystem::update() {
  
  syncFromClock();
  updateNormal();
  updateSimulation();

  if (_screen == SCREEN_SWITCH_TEST) {
    _dirty = true;
  }

  if (_dirty) {
    render();
    _dirty = false;
  }
}

void MenuSystem::updateNormal() {
  
  if (!_normalRunning || _clock == nullptr || _motor == nullptr) {
    return;
  }

  const unsigned long now = millis();
  if (_normalLastUpdateMs != 0 && now - _normalLastUpdateMs < 60000UL) {
    return;
  }
  _normalLastUpdateMs = now;

  
  const SolarPosition solarPosition = _noaa.calculate(
    _day, _month, _year, _hour, _minute,
    _latitudeThousandths, _longitudeThousandths
  );

  int targetAzimuth = (int)(solarPosition.azimuth + 0.5);
  int targetElevation = (int)(solarPosition.elevation + 0.5);

  if (solarPosition.elevation <= 0.0) {
    
    targetAzimuth = _startAzimuth;
    targetElevation = _startElevation;
  } else {
    
    if (targetAzimuth < _startAzimuth) targetAzimuth = _startAzimuth;
    if (targetAzimuth > _endAzimuth) targetAzimuth = _endAzimuth;
    if (targetElevation < _startElevation) targetElevation = _startElevation;
    if (targetElevation > 90) targetElevation = 90;
  }

  
  const int azimuthDelta = targetAzimuth - _azimuth;
  const int elevationDelta = targetElevation - _elevation;

  if (azimuthDelta != 0 && _motor->moveDegrees(MOTOR_AZIMUTH, azimuthDelta)) {
    _azimuth = targetAzimuth;
  }
  if (elevationDelta != 0 && _motor->movePanelDegrees(MOTOR_ELEVATION, elevationDelta)) {
    _elevation = targetElevation;
  }

  _dirty = true;
}

void MenuSystem::render() {
  
  if (_lcd == nullptr) {
    return;
  }

  if (_screen == SCREEN_EDIT) {
    renderEdit();
    return;
  }

  if (_screen == SCREEN_MAIN) {
    renderMenuPage("Hauptmenue", MAIN_ITEMS, 4, _mainIndex);
    return;
  }

  if (_screen == SCREEN_TEST_MENU) {
    renderMenuPage("Testbetrieb", TEST_ITEMS, 7, _testIndex);
    return;
  }

  if (_screen == SCREEN_SETTINGS) {
    renderMenuPage("Einstellung", SETTINGS_ITEMS, 13, _settingsIndex);
    return;
  }

  if (_screen == SCREEN_SWITCH_TEST) {
    char line1[17];
    char line2[17];
    const bool azMin = (_motor != nullptr) && _motor->isAzimuthMinActive();
    const bool azMax = (_motor != nullptr) && _motor->isAzimuthMaxActive();
    const bool elMin = (_motor != nullptr) && _motor->isElevationMinActive();
    const bool elMax = (_motor != nullptr) && _motor->isElevationMaxActive();

    snprintf(line1, sizeof(line1), "Az: Ost%c West%c", azMin ? '!' : '.', azMax ? '!' : '.');
    snprintf(line2, sizeof(line2), "El: Unt%c Oben%c", elMin ? '!' : '.', elMax ? '!' : '.');
    _lcd->show(line1, line2);
    return;
  }

  if (_screen == SCREEN_START_POSITION_INFO) {
    char line1[17];
    char line2[17];
    snprintf(line1, sizeof(line1), "Start Az%03d", _startAzimuth);
    snprintf(line2, sizeof(line2), "El%02d gespeichert", _startElevation);
    _lcd->show(line1, line2);
    return;
  }

  if (_screen == SCREEN_END_POSITION_INFO) {
    char line1[17];
    char line2[17];
    snprintf(line1, sizeof(line1), "Ende Az%03d", _endAzimuth);
    snprintf(line2, sizeof(line2), "El%02d gespeichert", _endElevation);
    _lcd->show(line1, line2);
    return;
  }

  if (_screen == SCREEN_NORMAL_MENU) {
    renderMenuPage("Normal", NORMAL_ITEMS, 2, _normalIndex);
    return;
  }

  if (_screen == SCREEN_SIMULATION_MENU) {
    renderMenuPage("Simulation", SIMULATION_ITEMS, 2, _simulationIndex);
    return;
  }

  if (_screen == SCREEN_NORMAL) {
    char line2[17];
    if (_normalRunning) {
      snprintf(line2, sizeof(line2), "Az%03d El%02d", _azimuth, _elevation);
    } else {
      snprintf(line2, sizeof(line2), "nicht gestartet");
    }
    _lcd->show("Normal Status", line2);
    return;
  }

  if (_screen == SCREEN_SIMULATION) {
    char line1[17];
    char line2[17];
    if (_simulationRunning) {
      snprintf(line1, sizeof(line1), "Az:%03d Sim%d", _azimuth, _simulationSpeed);
      snprintf(line2, sizeof(line2), "El:%02d aktiv", _elevation);
    } else {
      snprintf(line1, sizeof(line1), "Az:%03d bereit", _azimuth);
      snprintf(line2, sizeof(line2), "El:%02d Speed%d", _elevation, _simulationSpeed);
    }
    _lcd->show(line1, line2);
    return;
  }
}

void MenuSystem::renderMenuPage(const char* title, const char* const* items, uint8_t count, uint8_t index) {
  
  char line1[17];
  char line2[17];

  snprintf(line1, sizeof(line1), "%s %u/%u", title, index + 1, count);
  snprintf(line2, sizeof(line2), ">%s", items[index]);

  _lcd->show(line1, line2);
}

void MenuSystem::enterCurrentItem() {
  
  if (_screen == SCREEN_MAIN) {
    if (_mainIndex == 0) {
      _screen = SCREEN_NORMAL_MENU;
      _normalIndex = 0;
    } else if (_mainIndex == 1) {
      _screen = SCREEN_SIMULATION_MENU;
      _simulationIndex = 0;
    } else if (_mainIndex == 2) {
      _screen = SCREEN_TEST_MENU;
      _testIndex = 0;
    } else {
      _screen = SCREEN_SETTINGS;
      _settingsIndex = 0;
    }
    return;
  }

  if (_screen == SCREEN_NORMAL || _screen == SCREEN_SIMULATION) {
    return;
  }

  if (_screen == SCREEN_NORMAL_MENU) {
    if (_normalIndex == 0) {
      _normalRunning = true;
      _normalLastUpdateMs = 0;
      _screen = SCREEN_NORMAL;
      _lcd->showFlash("Betrieb starten", "OK ENTER", 1000);
    } else {
      _screen = SCREEN_NORMAL;
    }
    return;
  }

  if (_screen == SCREEN_SIMULATION_MENU) {
    if (_simulationIndex == 0) {
      startSimulation();
    } else {
      startEdit(EDIT_SIM_SPEED);
    }
    return;
  }

  if (_screen == SCREEN_SWITCH_TEST) {
    _screen = SCREEN_SETTINGS;
    return;
  }

  if (_screen == SCREEN_TEST_MENU) {
    switch (_testIndex) {
      case 0: runTestEndschalter(); break;
      case 1: runTestRTC(); break;
      case 2: runTestLCD(); break;
      case 3: runTestAzimutMotor(); break;
      case 4: runTestElevationMotor(); break;
      case 5: runTestJoystick(); break;
      case 6:
        runTestEndschalter();
        runTestRTC();
        runTestLCD();
        runTestAzimutMotor();
        runTestElevationMotor();
        runTestJoystick();
        break;
      default: break;
    }
    return;
  }

  if (_screen == SCREEN_SETTINGS) {
    switch (_settingsIndex) {
      case 0:
        startEdit(EDIT_MANUAL_AXES);
        break;
      case 1:
        syncFromClock();
        startEdit(EDIT_DATE_DAY);
        break;
      case 2:
        syncFromClock();
        startEdit(EDIT_TIME_HOUR);
        break;
      case 3:
        startEdit(EDIT_LATITUDE);
        break;
      case 4:
        startEdit(EDIT_LONGITUDE);
        break;
      case 5:
        moveToStartPositionByHomeSwitch();
        saveSettingsToStorage();
        _lcd->showFlash("Startposition", "angefahren", 1000);
        break;
      case 6:
        _startAzimuth = _azimuth;
        _startElevation = _elevation;
        saveSettingsToStorage();
        _lcd->showFlash("Position", "gespeichert", 1000);
        break;
      case 7:
        _screen = SCREEN_START_POSITION_INFO;
        break;
      case 8:
        if (_motor != nullptr) {
          const int azimuthDelta = _endAzimuth - _azimuth;
          const int elevationDelta = _endElevation - _elevation;

          _motor->moveDegrees(MOTOR_AZIMUTH, azimuthDelta);
          _motor->movePanelDegrees(MOTOR_ELEVATION, elevationDelta);
        }

        _azimuth = _endAzimuth;
        _elevation = _endElevation;
        saveSettingsToStorage();
        _lcd->showFlash("Endposition", "angefahren", 1000);
        break;
      case 9:
        _endAzimuth = _azimuth;
        _endElevation = _elevation;
        saveSettingsToStorage();
        _lcd->showFlash("Position", "gespeichert", 1000);
        break;
      case 10:
        _screen = SCREEN_END_POSITION_INFO;
        break;
      case 11:
        _screen = SCREEN_SWITCH_TEST;
        break;
      case 12:
        calibrateAxes();
        break;
      default:
        break;
    }
  }
}

void MenuSystem::goBack() {
  
  if (_screen == SCREEN_SWITCH_TEST) {
    _screen = SCREEN_SETTINGS;
    return;
  }

  if (_screen == SCREEN_TEST_MENU) {
    _screen = SCREEN_MAIN;
    return;
  }

  if (_screen == SCREEN_MAIN) {
    _lcd->showFlash("Hauptmenue", "bereit", 700);
    return;
  }

  if (_screen == SCREEN_SIMULATION) {
    _simulationRunning = false;
  }

  if (_screen == SCREEN_EDIT) {
    _screen = _returnScreen;
    _editField = EDIT_NONE;
    return;
  }

  _screen = SCREEN_MAIN;
}

void MenuSystem::moveUp() {
  
  if (_screen == SCREEN_MAIN) {
    _mainIndex = (_mainIndex == 0) ? 3 : _mainIndex - 1;
    return;
  }

  if (_screen == SCREEN_NORMAL_MENU) {
    _normalIndex = (_normalIndex == 0) ? 1 : _normalIndex - 1;
    return;
  }

  if (_screen == SCREEN_SIMULATION_MENU) {
    _simulationIndex = (_simulationIndex == 0) ? 1 : _simulationIndex - 1;
    return;
  }

if (_screen == SCREEN_SETTINGS) {
    _settingsIndex = (_settingsIndex == 0) ? 12 : _settingsIndex - 1;
  }

  if (_screen == SCREEN_TEST_MENU) {
    _testIndex = (_testIndex == 0) ? 6 : _testIndex - 1;
  }
}

void MenuSystem::moveDown() {
  
  if (_screen == SCREEN_MAIN) {
    _mainIndex = (_mainIndex + 1) % 4;
    return;
  }

  if (_screen == SCREEN_NORMAL_MENU) {
    _normalIndex = (_normalIndex + 1) % 2;
    return;
  }

  if (_screen == SCREEN_SIMULATION_MENU) {
    _simulationIndex = (_simulationIndex + 1) % 2;
    return;
  }

  if (_screen == SCREEN_SETTINGS) {
    _settingsIndex = (_settingsIndex + 1) % 13;
  }

  if (_screen == SCREEN_TEST_MENU) {
    _testIndex = (_testIndex + 1) % 7;
  }
}

void MenuSystem::startEdit(EditField field) {
  
  _returnScreen = _screen;
  _screen = SCREEN_EDIT;
  _editField = field;
}

void MenuSystem::renderEdit() {
  
  char line1[17];
  char line2[17];
  char coordinateText[12];

  switch (_editField) {
    case EDIT_MANUAL_AXES:
      snprintf(line1, sizeof(line1), "UP/DN El L/R Az");
      snprintf(line2, sizeof(line2), "Az%03d El%02d", _azimuth, _elevation);
      break;
    case EDIT_AZIMUTH:
      snprintf(line1, sizeof(line1), "Azimut UP/DOWN");
      snprintf(line2, sizeof(line2), "%03d Grad ENTER", _azimuth);
      break;
    case EDIT_ELEVATION:
      snprintf(line1, sizeof(line1), "Elevat. UP/DOWN");
      snprintf(line2, sizeof(line2), "%02d Grad ENTER", _elevation);
      break;
    case EDIT_DATE_DAY:
      snprintf(line1, sizeof(line1), "Tag UP/DOWN");
      snprintf(line2, sizeof(line2), "%02d.%02d.%04d", _day, _month, _year);
      break;
    case EDIT_DATE_MONTH:
      snprintf(line1, sizeof(line1), "Monat UP/DOWN");
      snprintf(line2, sizeof(line2), "%02d.%02d.%04d", _day, _month, _year);
      break;
    case EDIT_DATE_YEAR:
      snprintf(line1, sizeof(line1), "Jahr UP/DOWN");
      snprintf(line2, sizeof(line2), "%02d.%02d.%04d", _day, _month, _year);
      break;
    case EDIT_TIME_HOUR:
      snprintf(line1, sizeof(line1), "Stunde UP/DOWN");
      snprintf(line2, sizeof(line2), "%02d:%02d ENTER", _hour, _minute);
      break;
    case EDIT_TIME_MINUTE:
      snprintf(line1, sizeof(line1), "Minute UP/DOWN");
      snprintf(line2, sizeof(line2), "%02d:%02d ENTER", _hour, _minute);
      break;
    case EDIT_LATITUDE:
      formatCoordinate(coordinateText, sizeof(coordinateText), _latitudeThousandths);
      snprintf(line1, sizeof(line1), "Breite UP/DOWN");
      snprintf(line2, sizeof(line2), "%s Grad", coordinateText);
      break;
    case EDIT_LONGITUDE:
      formatCoordinate(coordinateText, sizeof(coordinateText), _longitudeThousandths);
      snprintf(line1, sizeof(line1), "Laenge UP/DOWN");
      snprintf(line2, sizeof(line2), "%s Grad", coordinateText);
      break;
    case EDIT_SIM_SPEED:
      snprintf(line1, sizeof(line1), "Sim Speed");
      snprintf(line2, sizeof(line2), "Stufe %d", _simulationSpeed);
      break;
    case EDIT_START_AZIMUTH:
      snprintf(line1, sizeof(line1), "Start Azimut");
      snprintf(line2, sizeof(line2), "%03d Grad", _startAzimuth);
      break;
    case EDIT_START_ELEVATION:
      snprintf(line1, sizeof(line1), "Start Elevat.");
      snprintf(line2, sizeof(line2), "%02d Grad", _startElevation);
      break;
    default:
      snprintf(line1, sizeof(line1), "Eingabe");
      snprintf(line2, sizeof(line2), "Fehler");
      break;
  }

  _lcd->show(line1, line2);
}

void MenuSystem::increaseEditValue() {
  
  switch (_editField) {
    case EDIT_AZIMUTH:
      if (_motor != nullptr) {
        if (_motor->moveDegrees(MOTOR_AZIMUTH, 1)) {
          _azimuth++;
        }
      } else {
        _azimuth++;
      }
      break;
    case EDIT_ELEVATION:
      if (_motor != nullptr) {
        if (_motor->movePanelDegrees(MOTOR_ELEVATION, 1)) {
          _elevation++;
        }
      } else {
        _elevation++;
      }
      break;
    case EDIT_DATE_DAY:
      _day++;
      break;
    case EDIT_DATE_MONTH:
      _month++;
      break;
    case EDIT_DATE_YEAR:
      _year++;
      break;
    case EDIT_TIME_HOUR:
      _hour++;
      break;
    case EDIT_TIME_MINUTE:
      _minute++;
      break;
    case EDIT_LATITUDE:
      _latitudeThousandths++;
      break;
    case EDIT_LONGITUDE:
      _longitudeThousandths++;
      break;
    case EDIT_SIM_SPEED:
      _simulationSpeed++;
      break;
    default:
      break;
  }

  clampValues();
}

void MenuSystem::decreaseEditValue() {
  
  switch (_editField) {
    case EDIT_AZIMUTH:
      if (_motor != nullptr) {
        if (_motor->moveDegrees(MOTOR_AZIMUTH, -1)) {
          _azimuth--;
        }
      } else {
        _azimuth--;
      }
      break;
    case EDIT_ELEVATION:
      if (_motor != nullptr) {
        if (_motor->movePanelDegrees(MOTOR_ELEVATION, -1)) {
          _elevation--;
        }
      } else {
        _elevation--;
      }
      break;
    case EDIT_DATE_DAY:
      _day--;
      break;
    case EDIT_DATE_MONTH:
      _month--;
      break;
    case EDIT_DATE_YEAR:
      _year--;
      break;
    case EDIT_TIME_HOUR:
      _hour--;
      break;
    case EDIT_TIME_MINUTE:
      _minute--;
      break;
    case EDIT_LATITUDE:
      _latitudeThousandths--;
      break;
    case EDIT_LONGITUDE:
      _longitudeThousandths--;
      break;
    case EDIT_SIM_SPEED:
      _simulationSpeed--;
      break;
    default:
      break;
  }

  clampValues();
}

void MenuSystem::nextEditFieldOrSave() {
  
  switch (_editField) {
    case EDIT_AZIMUTH:
      saveEdit("Azimut OK");
      break;
    case EDIT_MANUAL_AXES:
      saveEdit("Manuell OK");
      break;
    case EDIT_ELEVATION:
      saveEdit("Elevation OK");
      break;
    case EDIT_DATE_DAY:
      _editField = EDIT_DATE_MONTH;
      break;
    case EDIT_DATE_MONTH:
      _editField = EDIT_DATE_YEAR;
      break;
    case EDIT_DATE_YEAR:
      saveEdit("Datum OK");
      break;
    case EDIT_TIME_HOUR:
      _editField = EDIT_TIME_MINUTE;
      break;
    case EDIT_TIME_MINUTE:
      saveEdit("Uhrzeit OK");
      break;
    case EDIT_LATITUDE:
      saveEdit("Breite OK");
      break;
    case EDIT_LONGITUDE:
      saveEdit("Laenge OK");
      break;
    case EDIT_SIM_SPEED:
      saveEdit("Speed OK");
      break;
    default:
      saveEdit("Wert OK");
      break;
  }
}

void MenuSystem::saveEdit(const char* message) {
  
  syncClockFromMenu();
  saveSettingsToStorage();
  _screen = _returnScreen;
  _editField = EDIT_NONE;
  _lcd->showFlash("Position", "gespeichert", 900);
}

void MenuSystem::clampValues() {
  
  if (_azimuth < 0) _azimuth = 359;
  if (_azimuth > 359) _azimuth = 0;

  if (_day < 1) _day = 31;
  if (_day > 31) _day = 1;

  if (_month < 1) _month = 12;
  if (_month > 12) _month = 1;

  if (_year < 2024) _year = 2035;
  if (_year > 2035) _year = 2024;

  if (_hour < 0) _hour = 23;
  if (_hour > 23) _hour = 0;

  if (_minute < 0) _minute = 59;
  if (_minute > 59) _minute = 0;

  if (_latitudeThousandths < -90000) _latitudeThousandths = 90000;
  if (_latitudeThousandths > 90000) _latitudeThousandths = -90000;

  if (_longitudeThousandths < -180000) _longitudeThousandths = 180000;
  if (_longitudeThousandths > 180000) _longitudeThousandths = -180000;

  if (_simulationSpeed < 1) _simulationSpeed = 2;
  if (_simulationSpeed > 2) _simulationSpeed = 1;
}

void MenuSystem::formatCoordinate(char* buffer, size_t size, long valueThousandths) const {
  
  const char sign = (valueThousandths < 0) ? '-' : '+';
  const long absoluteValue = labs(valueThousandths);
  const long degrees = absoluteValue / 1000;
  const long decimals = absoluteValue % 1000;

  snprintf(buffer, size, "%c%ld.%03ld", sign, degrees, decimals);
}

void MenuSystem::loadSettingsFromStorage() {
  
  if (_storage == nullptr) {
    return;
  }

  TrackerSettings settings;
  _storage->load(settings);

  _azimuth = settings.azimuth;
  _elevation = settings.elevation;
  _startAzimuth = settings.startAzimuth;
  _startElevation = settings.startElevation;
  _endAzimuth = settings.endAzimuth;
  _endElevation = settings.endElevation;
  _day = settings.day;
  _month = settings.month;
  _year = settings.year;
  _hour = settings.hour;
  _minute = settings.minute;
  _latitudeThousandths = settings.latitudeThousandths;
  _longitudeThousandths = settings.longitudeThousandths;
  _simulationSpeed = settings.simulationSpeed;

  clampValues();

  if (_clock != nullptr) {
    _clock->begin(_day, _month, _year, _hour, _minute);
  }
}

void MenuSystem::saveSettingsToStorage() {
  
  if (_storage == nullptr) {
    return;
  }

  TrackerSettings settings;
  settings.azimuth = _azimuth;
  settings.elevation = _elevation;
  settings.startAzimuth = _startAzimuth;
  settings.startElevation = _startElevation;
  settings.endAzimuth = _endAzimuth;
  settings.endElevation = _endElevation;
  settings.day = _day;
  settings.month = _month;
  settings.year = _year;
  settings.hour = _hour;
  settings.minute = _minute;
  settings.latitudeThousandths = _latitudeThousandths;
  settings.longitudeThousandths = _longitudeThousandths;
  settings.simulationSpeed = _simulationSpeed;

  _storage->save(settings);
}

void MenuSystem::syncStartPositionFromHomeSwitch() {
  
  if (_motor == nullptr) {
    return;
  }

  bool changed = false;

  
  if (_motor->isAzimuthMinActive()) {
    _azimuth = 90;
    _startAzimuth = 90;
    changed = true;
  }

  
  if (_motor->isElevationMinActive()) {
    _elevation = 0;
    _startElevation = 0;
    changed = true;
  }

  if (changed) {
    clampValues();
    saveSettingsToStorage();
  }
}

void MenuSystem::moveToStartPositionByHomeSwitch() {
  
  if (_motor == nullptr) {
    _azimuth = _startAzimuth;
    _elevation = _startElevation;
    return;
  }

  
  const bool azimuthHomeReached = _motor->moveAzimuthUntilHome(-1);
  if (azimuthHomeReached) {
    _azimuth = 90;
    _startAzimuth = 90;
  } else {
    _azimuth = _startAzimuth;
  }

  
  const bool elevationHomeReached = _motor->moveElevationUntilHome(-1);
  if (elevationHomeReached) {
    _elevation = 0;
    _startElevation = 0;
  } else {
    _elevation = _startElevation;
  }

  clampValues();
  saveSettingsToStorage();
}

void MenuSystem::runTestEndschalter() {
  if (_motor == nullptr) {
    _lcd->showFlash("Endschalter", "Motor fehlt", 1200);
    return;
  }
  Serial.println("=== Test Endschalter ===");
  const bool azMin = _motor->isAzimuthMinActive();
  const bool azMax = _motor->isAzimuthMaxActive();
  const bool elMin = _motor->isElevationMinActive();
  const bool elMax = _motor->isElevationMaxActive();
  Serial.print("AZ min:"); Serial.print(azMin);
  Serial.print(" AZ max:"); Serial.print(azMax);
  Serial.print(" EL min:"); Serial.print(elMin);
  Serial.print(" EL max:"); Serial.println(elMax);
  _lcd->showFlash("Endschalter", "siehe Serial", 1200);
}

void MenuSystem::runTestRTC() {
  Serial.println("=== Test RTC (DS3231) ===");
  RTC_DS3231 rtc;
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
  if (!rtc.begin()) {
    Serial.println("FEHLER: DS3231 nicht gefunden!");
    _lcd->showFlash("RTC", "nicht gefunden", 1200);
    return;
  }
  DateTime now = rtc.now();
  Serial.print("Datum/Uhrzeit: ");
  Serial.print(now.day()); Serial.print(".");
  Serial.print(now.month()); Serial.print(".");
  Serial.print(now.year()); Serial.print(" ");
  Serial.print(now.hour()); Serial.print(":");
  Serial.print(now.minute()); Serial.print(":");
  Serial.println(now.second());
  _lcd->showFlash("RTC", "ok, siehe Serial", 1200);
}

void MenuSystem::runTestLCD() {
  Serial.println("=== Test LCD ===");
  _lcd->show("Testbetrieb", "LCD OK");
  delay(1200);
  Serial.println("LCD-Zeilen gesetzt.");
}

void MenuSystem::runTestAzimutMotor() {
  if (_motor == nullptr) {
    _lcd->showFlash("Az-Motor", "Motor fehlt", 1200);
    return;
  }
  Serial.println("=== Test Azimut-Motor ===");
  _lcd->showFlash("Az-Motor", "teste", 600);
  _motor->moveDegrees(MOTOR_AZIMUTH, 5);
  _motor->moveDegrees(MOTOR_AZIMUTH, -5);
  Serial.println("Azimut bewegt (5 Grad hin, 5 zurueck).");
}

void MenuSystem::runTestElevationMotor() {
  if (_motor == nullptr) {
    _lcd->showFlash("El-Motor", "Motor fehlt", 1200);
    return;
  }
  Serial.println("=== Test Elevation-Motor ===");
  _lcd->showFlash("El-Motor", "teste", 600);
  _motor->movePanelDegrees(MOTOR_ELEVATION, 5);
  _motor->movePanelDegrees(MOTOR_ELEVATION, -5);
  Serial.println("Elevation bewegt (5 Grad hin, 5 zurueck).");
}

void MenuSystem::runTestJoystick() {
  Serial.println("=== Test Joystick ===");
  Serial.println("Bewege den Stick. 5s Aufnahme...");
  _lcd->showFlash("Joystick", "bewege", 600);
  unsigned long t = millis();
  int samples = 0;
  while (millis() - t < 5000 && samples < 200) {
    int x = analogRead(PIN_JOYSTICK_X);
    int y = analogRead(PIN_JOYSTICK_Y);
    if (x < JOYSTICK_LOW_THRESHOLD) {
      Serial.println("UP"); samples++;
    } else if (x > JOYSTICK_HIGH_THRESHOLD) {
      Serial.println("DOWN"); samples++;
    } else if (y < JOYSTICK_LOW_THRESHOLD) {
      Serial.println("LEFT"); samples++;
    } else if (y > JOYSTICK_HIGH_THRESHOLD) {
      Serial.println("RIGHT"); samples++;
    } else if (digitalRead(PIN_JOYSTICK_SW) == LOW) {
      Serial.println("ENTER"); samples++;
    }
    delay(40);
  }
  Serial.println("Joystick-Test beendet.");
  _lcd->showFlash("Joystick", "fertig", 800);
}

void MenuSystem::calibrateAxes() {
  
  if (_motor == nullptr || _lcd == nullptr) {
    return;
  }

  _lcd->show("Kalibrierung", "Az MIN fahren");
  if (!_motor->moveAzimuthUntilHome(-1)) {
    _lcd->showFlash("Fehler", "Az MIN fehlt", 1500);
    return;
  }

  _lcd->show("Kalibrierung", "Az MAX fahren");
  if (!_motor->moveAzimuthUntilMax(1)) {
    _lcd->showFlash("Fehler", "Az MAX fehlt", 1500);
    return;
  }

  _lcd->show("Kalibrierung", "El MIN fahren");
  if (!_motor->moveElevationUntilHome(-1)) {
    _lcd->showFlash("Fehler", "El MIN fehlt", 1500);
    return;
  }

  _lcd->show("Kalibrierung", "El MAX fahren");
  if (!_motor->moveElevationUntilMax(1)) {
    _lcd->showFlash("Fehler", "El MAX fehlt", 1500);
    return;
  }

  
  
  
  _azimuth = _endAzimuth;
  _elevation = _endElevation;
  saveSettingsToStorage();
  _lcd->showFlash("Kalibrierung", "fertig, Position sicher", 1800);
}

void MenuSystem::syncFromClock() {
  
  if (_clock == nullptr) {
    return;
  }

  
  
  
  if (_screen == SCREEN_EDIT &&
      (_editField == EDIT_DATE_DAY ||
       _editField == EDIT_DATE_MONTH ||
       _editField == EDIT_DATE_YEAR ||
       _editField == EDIT_TIME_HOUR ||
       _editField == EDIT_TIME_MINUTE)) {
    return;
  }

  const int newDay = _clock->day();
  const int newMonth = _clock->month();
  const int newYear = _clock->year();
  const int newHour = _clock->hour();
  const int newMinute = _clock->minute();

  if (_day != newDay ||
      _month != newMonth ||
      _year != newYear ||
      _hour != newHour ||
      _minute != newMinute) {
    _dirty = true;
  }

  _day = newDay;
  _month = newMonth;
  _year = newYear;
  _hour = newHour;
  _minute = newMinute;
}

void MenuSystem::syncClockFromMenu() {
  
  if (_clock == nullptr) {
    return;
  }

  if (_editField == EDIT_DATE_DAY || _editField == EDIT_DATE_MONTH || _editField == EDIT_DATE_YEAR) {
    _clock->setDate(_day, _month, _year);
  }

  if (_editField == EDIT_TIME_HOUR || _editField == EDIT_TIME_MINUTE) {
    _clock->setTime(_hour, _minute);
  }
}

void MenuSystem::startSimulation() {
  
  
  
  
  
  const int simulationStartAzimuth = _startAzimuth;
  const int simulationStartElevation = _startElevation;

  if (_endAzimuth < _startAzimuth) {
    _endAzimuth = _startAzimuth;
    saveSettingsToStorage();
  }

  moveToStartPositionByHomeSwitch();
  _simulationStartAzimuth = simulationStartAzimuth;
  _simulationStartElevation = simulationStartElevation;
  _simulationDurationMs = (_simulationSpeed == 1) ? 60000UL : 30000UL;
  _simulationStartMs = millis();
  _simulationLastStep = -1;
  _simulationRunning = true;
  _screen = SCREEN_SIMULATION;
  _dirty = true;
}

void MenuSystem::updateSimulation() {
  
  if (!_simulationRunning) {
    return;
  }

  const unsigned long elapsed = millis() - _simulationStartMs;

  if (elapsed >= _simulationDurationMs) {
    finishSimulationAndReturnHome();
    return;
  }

  
  
  
  const int stepCount = (int)(_simulationDurationMs / 1000UL);
  const int currentStep = (int)((elapsed * stepCount) / _simulationDurationMs);

  if (currentStep == _simulationLastStep) {
    return;
  }

  _simulationLastStep = currentStep;

  int daylightStartMinute = 6 * 60;
  int daylightEndMinute = 18 * 60;
  float daylightStartAzimuth = _startAzimuth;
  float daylightEndAzimuth = _endAzimuth;
  bool foundSunrise = false;

  
  
  
  for (int minuteOfDay = 0; minuteOfDay <= 1430; minuteOfDay += 10) {
    SolarPosition scanPosition = _noaa.calculate(
      _day,
      _month,
      _year,
      minuteOfDay / 60,
      minuteOfDay % 60,
      _latitudeThousandths,
      _longitudeThousandths
    );

    if (scanPosition.elevation > 0.0) {
      if (!foundSunrise) {
        daylightStartMinute = minuteOfDay;
        daylightStartAzimuth = scanPosition.azimuth;
        foundSunrise = true;
      }

      daylightEndMinute = minuteOfDay;
      daylightEndAzimuth = scanPosition.azimuth;
    }
  }

  const int daylightDuration = max(1, daylightEndMinute - daylightStartMinute);
  const int simulatedMinutes = daylightStartMinute + ((long)daylightDuration * currentStep) / stepCount;
  const int simulatedHour = simulatedMinutes / 60;
  const int simulatedMinute = simulatedMinutes % 60;

  
  SolarPosition solarPosition = _noaa.calculate(
    _day,
    _month,
    _year,
    simulatedHour,
    simulatedMinute,
    _latitudeThousandths,
    _longitudeThousandths
  );

  float azimuthProgress = 0.0;

  if (abs(daylightEndAzimuth - daylightStartAzimuth) > 1.0) {
    azimuthProgress = (solarPosition.azimuth - daylightStartAzimuth) / (daylightEndAzimuth - daylightStartAzimuth);
  } else {
    azimuthProgress = (float)currentStep / (float)stepCount;
  }

  if (azimuthProgress < 0.0) azimuthProgress = 0.0;
  if (azimuthProgress > 1.0) azimuthProgress = 1.0;

  int targetAzimuth = _startAzimuth + (int)((_endAzimuth - _startAzimuth) * azimuthProgress + 0.5);
  int targetElevation = (int)(solarPosition.elevation + 0.5);

  if (targetElevation < 0) {
    targetElevation = 0;
  }

  if (targetAzimuth < _startAzimuth) targetAzimuth = _startAzimuth;
  if (targetAzimuth > _endAzimuth) targetAzimuth = _endAzimuth;

  
  
  if (targetElevation > 90) targetElevation = 90;

  const int azimuthDelta = targetAzimuth - _azimuth;
  const int elevationDelta = targetElevation - _elevation;

  if (_motor != nullptr) {
    if (azimuthDelta != 0) {
      _motor->moveDegrees(MOTOR_AZIMUTH, azimuthDelta);
    }

    if (elevationDelta != 0) {
      _motor->movePanelDegrees(MOTOR_ELEVATION, elevationDelta);
    }
  }

  _azimuth = targetAzimuth;
  _elevation = targetElevation;
  _dirty = true;
}

void MenuSystem::finishSimulationAndReturnHome() {
  
  moveToStartPositionByHomeSwitch();
  _simulationRunning = false;
  _simulationLastStep = -1;
  saveSettingsToStorage();
  _lcd->showFlash("Simulation Ende", "Startposition", 1200);
  _dirty = true;
}

