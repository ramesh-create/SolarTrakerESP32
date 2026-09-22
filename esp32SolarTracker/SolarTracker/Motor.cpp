

#include "Motor.h"
#include "Config.h"


static const uint8_t HALF_STEP_SEQUENCE[8][4] = {
  {1, 0, 0, 0},
  {1, 1, 0, 0},
  {0, 1, 0, 0},
  {0, 1, 1, 0},
  {0, 0, 1, 0},
  {0, 0, 1, 1},
  {0, 0, 0, 1},
  {1, 0, 0, 1}
};

void MotorController::begin() {
  
  pinMode(PIN_AZIMUTH_IN1, OUTPUT);
  pinMode(PIN_AZIMUTH_IN2, OUTPUT);
  pinMode(PIN_AZIMUTH_IN3, OUTPUT);
  pinMode(PIN_AZIMUTH_IN4, OUTPUT);

  
  pinMode(PIN_ELEVATION_IN1, OUTPUT);
  pinMode(PIN_ELEVATION_IN2, OUTPUT);
  pinMode(PIN_ELEVATION_IN3, OUTPUT);
  pinMode(PIN_ELEVATION_IN4, OUTPUT);

  
  pinMode(PIN_AZIMUTH_MIN_SWITCH, INPUT_PULLUP);
  pinMode(PIN_AZIMUTH_MAX_SWITCH, INPUT_PULLUP);
  pinMode(PIN_ELEVATION_MIN_SWITCH, INPUT_PULLUP);
  pinMode(PIN_ELEVATION_MAX_SWITCH, INPUT_PULLUP);

  
  releaseAll();
}

bool MotorController::moveDegrees(MotorAxis axis, int degrees) {
  
  if (axis == MOTOR_AZIMUTH && !canMoveAzimuth(degrees)) {
    releaseAxis(MOTOR_AZIMUTH);
    return false;
  }

  if (axis == MOTOR_ELEVATION && !canMoveElevation(degrees)) {
    releaseAxis(MOTOR_ELEVATION);
    return false;
  }

  int steps = 0;

  if (axis == MOTOR_AZIMUTH) {
    steps = (int)(degrees * STEPS_PER_DEGREE);
  } else {
    steps = degrees * MANUAL_MOVE_STEPS;
  }

  if (degrees > 0 && steps == 0) {
    steps = 1;
  }

  if (degrees < 0 && steps == 0) {
    steps = -1;
  }

  return moveSteps(axis, steps);
}

bool MotorController::movePanelDegrees(MotorAxis axis, int panelDegrees) {
  
  if (axis == MOTOR_ELEVATION) {
    if (!canMoveElevation(panelDegrees)) {
      releaseAxis(MOTOR_ELEVATION);
      return false;
    }

    int steps = (int)(panelDegrees * ELEVATION_STEPS_PER_PANEL_DEGREE);

    if (panelDegrees > 0 && steps == 0) {
      steps = 1;
    }

    if (panelDegrees < 0 && steps == 0) {
      steps = -1;
    }

    return moveSteps(axis, steps);
  }

  return moveDegrees(axis, panelDegrees);
}

bool MotorController::moveSteps(MotorAxis axis, int steps) {
  
  const int direction = (steps >= 0) ? 1 : -1;
  const int totalSteps = abs(steps);

  
  for (int i = 0; i < totalSteps; i++) {
    
    if (axis == MOTOR_AZIMUTH) {
      if (direction < 0 && isAzimuthMinActive()) {
        moveAwayFromLimit(axis, direction);
        return false;
      }
      if (direction > 0 && isAzimuthMaxActive()) {
        moveAwayFromLimit(axis, direction);
        return false;
      }
    } else {
      if (direction < 0 && isElevationMinActive()) {
        moveAwayFromLimit(axis, direction);
        return false;
      }
      if (direction > 0 && isElevationMaxActive()) {
        moveAwayFromLimit(axis, direction);
        return false;
      }
    }

    
    int* currentStepIndex;

    if (axis == MOTOR_AZIMUTH) {
      currentStepIndex = &_azimuthStepIndex;
    } else {
      currentStepIndex = &_elevationStepIndex;
    }

    *currentStepIndex += direction;

    if (*currentStepIndex > 7) {
      *currentStepIndex = 0;
    }

    if (*currentStepIndex < 0) {
      *currentStepIndex = 7;
    }

    
    setStep(axis, *currentStepIndex);
    delay(MOTOR_STEP_DELAY_MS);
  }

  releaseAxis(axis);
  return true;
}

void MotorController::releaseAll() {
  
  releaseAxis(MOTOR_AZIMUTH);
  releaseAxis(MOTOR_ELEVATION);
}




bool MotorController::isAzimuthMinActive() const {
  
  return digitalRead(PIN_AZIMUTH_MIN_SWITCH) == LOW;
}

bool MotorController::isAzimuthMaxActive() const {
  return digitalRead(PIN_AZIMUTH_MAX_SWITCH) == LOW;
}

bool MotorController::isElevationMinActive() const {
  return digitalRead(PIN_ELEVATION_MIN_SWITCH) == LOW;
}

bool MotorController::isElevationMaxActive() const {
  return digitalRead(PIN_ELEVATION_MAX_SWITCH) == LOW;
}

bool MotorController::isAzimuthHomeSwitchActive() const {
  return isAzimuthMinActive();
}

bool MotorController::moveAzimuthUntilHome(int stepDirection) {
  return moveUntilLimit(MOTOR_AZIMUTH, stepDirection, false);
}

bool MotorController::moveAzimuthUntilMax(int stepDirection) {
  return moveUntilLimit(MOTOR_AZIMUTH, stepDirection, true);
}

bool MotorController::moveElevationUntilHome(int stepDirection) {
  return moveUntilLimit(MOTOR_ELEVATION, stepDirection, false);
}

bool MotorController::moveElevationUntilMax(int stepDirection) {
  return moveUntilLimit(MOTOR_ELEVATION, stepDirection, true);
}

bool MotorController::moveUntilLimit(MotorAxis axis, int stepDirection, bool moveToMax) {
  
  if (stepDirection == 0) {
    if (axis == MOTOR_AZIMUTH) {
      return moveToMax ? isAzimuthMaxActive() : isAzimuthMinActive();
    }
    return moveToMax ? isElevationMaxActive() : isElevationMinActive();
  }

  const int direction = (stepDirection > 0) ? 1 : -1;
  
  for (int i = 0; i < AZIMUTH_HOME_SEARCH_STEPS; i++) {
    int* currentStepIndex = (axis == MOTOR_AZIMUTH) ? &_azimuthStepIndex : &_elevationStepIndex;
    *currentStepIndex += direction;

    if (*currentStepIndex > 7) {
      *currentStepIndex = 0;
    }
    if (*currentStepIndex < 0) {
      *currentStepIndex = 7;
    }

    setStep(axis, *currentStepIndex);
    delay(MOTOR_STEP_DELAY_MS);

    const bool limitActive = (axis == MOTOR_AZIMUTH)
      ? (moveToMax ? isAzimuthMaxActive() : isAzimuthMinActive())
      : (moveToMax ? isElevationMaxActive() : isElevationMinActive());

    if (limitActive) {
      delay(LIMIT_SWITCH_DEBOUNCE_MS);
      const bool stillActive = (axis == MOTOR_AZIMUTH)
        ? (moveToMax ? isAzimuthMaxActive() : isAzimuthMinActive())
        : (moveToMax ? isElevationMaxActive() : isElevationMinActive());

      if (!stillActive) {
        continue;
      }

      moveAwayFromLimit(axis, direction);
      return true;
    }
  }

  releaseAxis(axis);
  return false;
}

bool MotorController::moveAwayFromLimit(MotorAxis axis, int stepDirection) {
  
  const int awayDirection = (stepDirection > 0) ? -1 : 1;

  
  for (int i = 0; i < LIMIT_RELEASE_MAX_STEPS; i++) {
    const bool limitActive = (axis == MOTOR_AZIMUTH)
      ? ((stepDirection > 0) ? isAzimuthMaxActive() : isAzimuthMinActive())
      : ((stepDirection > 0) ? isElevationMaxActive() : isElevationMinActive());

    if (!limitActive) {
      delay(LIMIT_SWITCH_DEBOUNCE_MS);
      const bool stillOpen = (axis == MOTOR_AZIMUTH)
        ? ((stepDirection > 0) ? !isAzimuthMaxActive() : !isAzimuthMinActive())
        : ((stepDirection > 0) ? !isElevationMaxActive() : !isElevationMinActive());

      if (stillOpen) {
        releaseAxis(axis);
        return true;
      }
    }

    moveSteps(axis, awayDirection);
  }

  releaseAxis(axis);
  return false;
}

bool MotorController::canMoveAzimuth(int stepsOrDegrees) const {
  
  if (stepsOrDegrees < 0) {
    return !isAzimuthMinActive();
  }
  if (stepsOrDegrees > 0) {
    return !isAzimuthMaxActive();
  }
  return true;
}

bool MotorController::canMoveElevation(int stepsOrDegrees) const {
  
  if (stepsOrDegrees < 0) {
    return !isElevationMinActive();
  }
  if (stepsOrDegrees > 0) {
    return !isElevationMaxActive();
  }
  return true;
}

void MotorController::setStep(MotorAxis axis, uint8_t stepIndex) {
  
  writeAxisPins(
    axis,
    HALF_STEP_SEQUENCE[stepIndex][0],
    HALF_STEP_SEQUENCE[stepIndex][1],
    HALF_STEP_SEQUENCE[stepIndex][2],
    HALF_STEP_SEQUENCE[stepIndex][3]
  );
}

void MotorController::releaseAxis(MotorAxis axis) {
  
  writeAxisPins(axis, LOW, LOW, LOW, LOW);
}

void MotorController::writeAxisPins(MotorAxis axis, uint8_t a, uint8_t b, uint8_t c, uint8_t d) {
  
  if (axis == MOTOR_AZIMUTH) {
    digitalWrite(PIN_AZIMUTH_IN1, a);
    digitalWrite(PIN_AZIMUTH_IN2, b);
    digitalWrite(PIN_AZIMUTH_IN3, c);
    digitalWrite(PIN_AZIMUTH_IN4, d);
  } else {
    digitalWrite(PIN_ELEVATION_IN1, a);
    digitalWrite(PIN_ELEVATION_IN2, b);
    digitalWrite(PIN_ELEVATION_IN3, c);
    digitalWrite(PIN_ELEVATION_IN4, d);
  }
}

