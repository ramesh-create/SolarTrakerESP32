

#ifndef NOAA_H
#define NOAA_H

#include <Arduino.h>

struct SolarPosition {
  float azimuth;
  float elevation;
};

class NOAA {
public:
  SolarPosition calculate(
    int day,
    int month,
    int year,
    int hour,
    int minute,
    long latitudeThousandths,
    long longitudeThousandths
  ) const;

private:
  int dayOfYear(int day, int month, int year) const;
  bool isLeapYear(int year) const;
  float degToRad(float degrees) const;
  float radToDeg(float radians) const;
};

#endif

