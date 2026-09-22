

#ifndef MOTOR_H
#define MOTOR_H


#include <Arduino.h>


enum MotorAxis {
  
  MOTOR_AZIMUTH,
  
  MOTOR_ELEVATION
};


class MotorController {
public:
  
  void begin();
  
  bool moveDegrees(MotorAxis axis, int degrees);
  
  bool movePanelDegrees(MotorAxis axis, int panelDegrees);
  
  bool moveSteps(MotorAxis axis, int steps);
  
  void releaseAll();

  
  
  bool isAzimuthMinActive() const;
  
  bool isAzimuthMaxActive() const;
  
  bool isElevationMinActive() const;
  
  bool isElevationMaxActive() const;

  
  
  bool isAzimuthHomeSwitchActive() const;

  
  
  bool moveAzimuthUntilHome(int stepDirection = -1);
  
  bool moveAzimuthUntilMax(int stepDirection = 1);
  
  bool moveElevationUntilHome(int stepDirection = -1);
  
  bool moveElevationUntilMax(int stepDirection = 1);
  
  bool canMoveAzimuth(int stepsOrDegrees) const;
  
  bool canMoveElevation(int stepsOrDegrees) const;

private:
  
  void setStep(MotorAxis axis, uint8_t stepIndex);
  
  bool moveUntilLimit(MotorAxis axis, int stepDirection, bool moveToMax);
  
  bool moveAwayFromLimit(MotorAxis axis, int stepDirection);
  
  void releaseAxis(MotorAxis axis);
  
  void writeAxisPins(MotorAxis axis, uint8_t a, uint8_t b, uint8_t c, uint8_t d);

  
  int _azimuthStepIndex = 0;
  
  int _elevationStepIndex = 0;
};

#endif

